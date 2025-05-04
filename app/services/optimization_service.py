import cvxpy as cp
import numpy as np
import pandas as pd
from typing import List, Dict

EPS_ZERO = 1e-6  # для обработки нулей в ценах

def compute_optimal_weights(
    price_history: pd.DataFrame,
    target_return: float = None,
    risk_tolerance: float = 0.5
) -> Dict[str, float]:
    """
    Рассчитать оптимальные доли активов по модели Марковица.

    price_history: DataFrame, где столбцы -- тикеры, индекс -- даты, значения -- цены.
    target_return: желаемая средняя доходность (ежедневная), если None, оптимизируется по риску
    risk_tolerance: параметр (0 консервативно, 1 агрессивно) для trade-off

    Возвращает dict: {ticker: weight}
    """
    # 1. Рассчитать лог-доходности
    returns = np.log(price_history / price_history.shift(1)).dropna()

    # 2. Статистики
    mu = returns.mean().values  # ожидания доходности
    Sigma = returns.cov().values  # ковариационная матрица
    n = len(mu)

    # 3. Переменные оптимизации: веса
    w = cp.Variable(n)

    # 4. Целевая функция: минимизировать риск - lambda * доходность
    portfolio_variance = cp.quad_form(w, Sigma)
    portfolio_return = mu.T @ w
    # trade-off параметр: risk_tolerance
    # хотим минимизировать variance - gamma * return
    gamma = risk_tolerance * 10  # шкалируем gamma
    objective = cp.Minimize(portfolio_variance - gamma * portfolio_return)

    # 5. Ограничения: сумма весов = 1, веса >= 0
    constraints = [cp.sum(w) == 1, w >= 0]
    if target_return is not None:
        constraints.append(portfolio_return >= target_return)

    # 6. Решаем задачу
    problem = cp.Problem(objective, constraints)
    problem.solve(solver=cp.SCS)

    # Нормировка для устранения численных ошибок
    raw_w = w.value
    w_clipped = np.where(raw_w < EPS_ZERO, 0.0, raw_w)
    if w_clipped.sum() > 0:
        w_norm = w_clipped / w_clipped.sum()
    else:
        w_norm = np.ones_like(w_clipped) / n

    tickers = price_history.columns.tolist()
    return {tickers[i]: float(w_norm[i]) for i in range(n)}