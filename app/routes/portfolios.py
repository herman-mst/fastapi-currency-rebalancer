"""
Module for portfolio routes.
Handles creation, retrieval, update, deletion and rebalancing of portfolios.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.security import get_current_user
from app.db import get_db
from app.services.optimization_service import compute_optimal_weights
from app.services.price_service import (
    fetch_current_prices,
    fetch_historical_prices
)

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

@router.post("/", response_model=schemas.PortfolioRead, 
             status_code=status.HTTP_201_CREATED)
def create_portfolio(
    portfolio_in: schemas.PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new portfolio for the current user.

    Args:
        portfolio_in (schemas.PortfolioCreate): The data required to create a new portfolio.
        db (Session): The database session dependency.
        current_user (models.User): The currently authenticated user.

    Returns:
        schemas.PortfolioRead: The newly created portfolio.

    Raises:
        HTTPException: If the user is not authenticated or if there is an issue with the portfolio creation.
    """
    return crud.create_portfolio(db, current_user.id, portfolio_in)

@router.get("/", response_model=List[schemas.PortfolioRead])
def read_portfolios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve a list of portfolios for the current user.

    Args:
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.
        db (Session): The database session dependency.
        current_user (models.User): The currently authenticated user dependency.

    Returns:
        List[models.Portfolio]: A list of portfolio objects belonging to the current user.
    """
    return crud.get_portfolios(db, current_user.id, skip, limit)

@router.get("/{portfolio_id}", response_model=schemas.PortfolioRead)
def read_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve a portfolio by its ID.

    Args:
        portfolio_id (int): The ID of the portfolio to retrieve.
        db (Session): The database session dependency.
        current_user (models.User): The currently authenticated user.

    Returns:
        schemas.PortfolioRead: The portfolio data if found.

    Raises:
        HTTPException: If the portfolio is not found, raises a 404 error.
    """
    port = crud.get_portfolio(db, portfolio_id, current_user.id)
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return port

@router.put("/{portfolio_id}", response_model=schemas.PortfolioRead)
def update_portfolio(
    portfolio_id: int,
    portfolio_in: schemas.PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Updates an existing portfolio with new data.
    Args:
        portfolio_id (int): The ID of the portfolio to update.
        portfolio_in (schemas.PortfolioCreate): The new data for the portfolio, including its name and assets.
        db (Session): The database session dependency.
        current_user (models.User): The currently authenticated user.
    Raises:
        HTTPException: If the portfolio with the given ID does not exist or does not belong to the current user.
    Returns:
        schemas.PortfolioRead: The updated portfolio data.
    """
    # Загрузить портфель из базы данных и проверить его существование
    port = crud.get_portfolio(db, portfolio_id, current_user.id)
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Обновить имя портфеля
    port.name = portfolio_in.name
    
    # Удалить все старые позиции (активы) из портфеля
    db.query(models.PortfolioAsset).filter(
        models.PortfolioAsset.portfolio_id == portfolio_id
    ).delete()
    db.commit()
    
    # Добавить новые позиции (активы) в портфель
    for item in portfolio_in.assets:
        pa = models.PortfolioAsset(
            portfolio_id=portfolio_id,
            asset_id=item.asset_id,
            target_pct=item.target_pct,
            quantity=item.quantity
        )
        db.add(pa)
    db.commit()
    
    # Обновить объект портфеля в сессии и вернуть его
    db.refresh(port)
    return port

@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Deletes a portfolio by its ID for the currently authenticated user.

    Args:
        portfolio_id (int): The ID of the portfolio to delete.
        db (Session): The database session dependency.
        current_user (models.User): The currently authenticated user.

    Raises:
        HTTPException: If the portfolio is not found (404 status code).

    Returns:
        None: Indicates successful deletion of the portfolio.
    """
    port = crud.delete_portfolio(db, portfolio_id, current_user.id)
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")

@router.post(
    "/{portfolio_id}/rebalance",
    response_model=schemas.RebalancingReportRead
)
async def rebalance_portfolio(
    portfolio_id: int,
    days: int = Query(
        30,
        ge=5,
        le=365,
        description="Number of days of historical data to use"
    ),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Rebalance a portfolio based on historical data and user risk tolerance.
    This endpoint calculates the optimal asset allocation for a given portfolio
    and provides recommendations to rebalance the portfolio to achieve the target allocation.
    Args:
        portfolio_id (int): The ID of the portfolio to rebalance.
        days (int, optional): Number of days of historical data to use for calculations.
            Must be between 5 and 365. Defaults to 30.
        db (Session): Database session dependency.
        current_user (models.User): The currently authenticated user.
    Raises:
        HTTPException: If the portfolio is not found (404).
        HTTPException: If the portfolio has no assets (400).
    Returns:
        schemas.RebalancingReportRead: A report containing rebalancing recommendations,
        including the current and target percentages, actions to take (buy/sell),
        and the amounts in units and value for each asset.
    """
    # pylint: disable=too-many-locals
    # Получаем портфель пользователя
    port = crud.get_portfolio(db, portfolio_id, current_user.id)
    if not port:
        raise HTTPException(404, "Portfolio not found")

    # Извлекаем символы активов и их количество
    symbols = [pa.asset.symbol.lower() for pa in port.assets]
    quantities = {pa.asset.symbol.lower(): pa.quantity for pa in port.assets}
    if not symbols:
        raise HTTPException(400, "Portfolio has no assets")

    # Получаем текущие цены и общую стоимость портфеля
    prices = await fetch_current_prices(symbols)
    total_value = sum(
        quantities[sym] * prices.get(sym, 0.0)
        for sym in symbols
    )

    if total_value == 0:
        return schemas.RebalancingReportRead(
            id=0,
            portfolio_id=portfolio_id,
            recommendations=[],
            message="Total portfolio value is zero — check asset quantities"
        )

    # Получаем историю цен за указанный период (N дней)
    hist = await fetch_historical_prices(symbols, days=days)

    # Рассчитываем оптимальные веса активов
    weights = compute_optimal_weights(
        price_history=hist,
        risk_tolerance=current_user.risk_tolerance
    )

    # Формируем рекомендации по ребалансировке
    recommendations = []
    for sym in symbols:
        current_pct = (quantities[sym] * prices[sym]) / total_value
        target_pct = weights.get(sym, 0.0)
        diff = target_pct - current_pct
        action = "buy" if diff > 0 else "sell"
        units = abs(diff) * total_value / (prices[sym] or 1.0)
        value = units * prices[sym]
        recommendations.append({
            "symbol": sym,
            "current_pct": current_pct,
            "target_pct": target_pct,
            "action": action,
            "amount_units": units,
            "amount_value": value
        })

    # Сохраняем отчет о ребалансировке в базе данных
    report = crud.create_rebalancing_report(db, portfolio_id, recommendations)
    return report