import cvxpy as cp
import numpy as np
import pandas as pd
from app.core.constants import EPS_ZERO

def compute_optimal_weights(price_history: pd.DataFrame, target_return: float = None, risk_tolerance: float = 0.5) -> dict[str, float]:
    """
    Compute the optimal portfolio weights to minimize risk while considering a target return 
    and risk tolerance using mean-variance optimization.
    Args:
        price_history (pd.DataFrame): A DataFrame containing historical prices of assets. 
            Each column represents an asset, and each row represents a time period.
        target_return (float, optional): The desired minimum portfolio return. If None, 
            the optimization does not enforce a return constraint. Defaults to None.
        risk_tolerance (float, optional): A parameter controlling the trade-off between 
            risk and return. Higher values prioritize return over risk. Defaults to 0.5.
    Returns:
        dict[str, float]: A dictionary mapping asset tickers (columns of `price_history`) 
        to their respective optimal weights in the portfolio.
    Notes:
        - The function uses log-returns for calculations.
        - The optimization minimizes portfolio variance adjusted by a scaled return term.
        - Constraints ensure that weights sum to 1 and are non-negative.
        - If numerical issues arise, weights are normalized to ensure they sum to 1.
    """
    # 1. Рассчитываем логарифмические доходности активов
    returns = np.log(price_history / price_history.shift(1)).dropna()

    # 2. Вычисляем статистики для модели Марковица
    mu = returns.mean().values  # Ожидаемая доходность активов (вектор средних)
    Sigma = returns.cov().values  # Ковариационная матрица доходностей
    n = len(mu)  # Количество активов

    # 3. Определяем переменные оптимизации: веса активов в портфеле
    w = cp.Variable(n)

    # 4. Формируем целевую функцию: минимизация риска с учетом доходности
    portfolio_variance = cp.quad_form(w, Sigma)  # Риск портфеля (дисперсия)
    portfolio_return = mu.T @ w  # Ожидаемая доходность портфеля
    # Параметр trade-off: risk_tolerance определяет баланс между риском и доходностью
    gamma = risk_tolerance * 10  # Масштабируем gamma для управления вкладом доходности
    objective = cp.Minimize(portfolio_variance - gamma * portfolio_return)

    # 5. Накладываем ограничения: сумма весов = 1, веса >= 0
    constraints = [cp.sum(w) == 1, w >= 0]  # Вес каждого актива должен быть неотрицательным
    if target_return is not None:
        constraints.append(portfolio_return >= target_return)  # Ограничение на минимальную доходность

    # 6. Решаем задачу оптимизации
    problem = cp.Problem(objective, constraints)
    problem.solve(solver=cp.SCS)  # Используем SCS как решатель

    # Нормируем веса для устранения численных ошибок
    raw_w = w.value  # Получаем оптимальные веса
    w_clipped = np.where(raw_w < EPS_ZERO, 0.0, raw_w)  # Убираем численные ошибки (очень малые значения)
    if w_clipped.sum() > 0:
        w_norm = w_clipped / w_clipped.sum()  # Нормируем веса, чтобы их сумма была равна 1
    else:
        w_norm = np.ones_like(w_clipped) / n  # Если все веса обнулились, равномерно распределяем

    # Возвращаем результат в виде словаря: тикер -> вес
    tickers = price_history.columns.tolist()
    return {tickers[i]: float(w_norm[i]) for i in range(n)}