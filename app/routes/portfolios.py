from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas, models
from app.db import get_db
from app.core.security import get_current_user
from app.services.price_service import fetch_current_prices, fetch_historical_prices
from app.services.optimization_service import compute_optimal_weights

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

@router.post("/", response_model=schemas.PortfolioRead, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    portfolio_in: schemas.PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_portfolio(db, current_user.id, portfolio_in)

@router.get("/", response_model=List[schemas.PortfolioRead])
def read_portfolios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_portfolios(db, current_user.id, skip, limit)

@router.get("/{portfolio_id}", response_model=schemas.PortfolioRead)
def read_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
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
    # Загрузить и проверить наличие портфеля
    port = crud.get_portfolio(db, portfolio_id, current_user.id)
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    # Обновить имя
    port.name = portfolio_in.name
    # Удалить старые позиции
    db.query(models.PortfolioAsset).filter(
        models.PortfolioAsset.portfolio_id == portfolio_id
    ).delete()
    db.commit()
    # Добавить новые позиции
    for item in portfolio_in.assets:
        pa = models.PortfolioAsset(
            portfolio_id=portfolio_id,
            asset_id=item.asset_id,
            target_pct=item.target_pct,
            quantity=item.quantity
        )
        db.add(pa)
    db.commit()
    db.refresh(port)
    return port

@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    port = crud.delete_portfolio(db, portfolio_id, current_user.id)
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return None

@router.post("/{portfolio_id}/rebalance", response_model=schemas.RebalancingReportRead)
async def rebalance_portfolio(
    portfolio_id: int,
    days: int = Query(30, ge=5, le=365, description="Number of days of historical data to use"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    port = crud.get_portfolio(db, portfolio_id, current_user.id)
    if not port:
        raise HTTPException(404, "Portfolio not found")

    symbols = [pa.asset.symbol.lower() for pa in port.assets]
    quantities = {pa.asset.symbol.lower(): pa.quantity for pa in port.assets}
    if not symbols:
        raise HTTPException(400, "Portfolio has no assets")

    # 1) Получаем текущие цены и total_value
    prices = await fetch_current_prices(symbols)
    total_value = sum(quantities[sym] * prices.get(sym, 0.0) for sym in symbols)
    if total_value == 0:
        return schemas.RebalancingReportRead(
            id=0,
            portfolio_id=portfolio_id,
            generated_at=None,
            recommendations=[],
            message="Total portfolio value is zero — проверьте quantity активов"
        )

    # 2) Получаем историю цен за N дней
    hist = await fetch_historical_prices(symbols, days=days)

    # 3) Считаем оптимальные веса
    weights = compute_optimal_weights(
        price_history=hist,
        risk_tolerance=current_user.risk_tolerance
    )

    # 4) Формируем рекомендации
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

    report = crud.create_rebalancing_report(db, portfolio_id, recommendations)
    return report