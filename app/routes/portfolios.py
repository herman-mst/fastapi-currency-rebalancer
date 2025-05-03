from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas, models
from app.db import get_db
from app.core.security import get_current_user
from app.services.price_service import fetch_current_prices

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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Загрузить портфель
    port = crud.get_portfolio(db, portfolio_id, current_user.id)
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # 2. Сформировать список тикеров (id CoinGecko)
    symbols = [pa.asset.symbol.lower() for pa in port.assets]
    if not symbols:
        raise HTTPException(status_code=400, detail="Portfolio has no assets")

    # 3. Получить текущие цены
    prices = await fetch_current_prices(symbols)

    # 4. Вычислить текущую стоимость и доли
    total_value = 0.0
    current_values = {}
    for pa in port.assets:
        sym = pa.asset.symbol.lower()
        qty = pa.quantity
        val = qty * prices.get(sym, 0.0)
        current_values[sym] = val
        total_value += val

    # Обработка ошибки деления на ноль
    if total_value == 0.0:
        return schemas.RebalancingReportRead(
            id=0,
            portfolio_id=portfolio_id,
            generated_at=None,
            recommendations=[],
            message="Total portfolio value is zero — проверьте quantity активов"
        )

    current_pcts = {sym: val / total_value for sym, val in current_values.items()}

    # 5. Простейшие рекомендации
    recommendations = []
    for pa in port.assets:
        sym = pa.asset.symbol.lower()
        target = pa.target_pct
        current = current_pcts.get(sym, 0.0)
        diff = target - current
        action = "buy" if diff > 0 else "sell"
        units = abs(diff) * total_value / (prices.get(sym, 1.0) or 1.0)
        recommendations.append({
            "symbol": sym,
            "current_pct": current,
            "target_pct": target,
            "action": action,
            "amount_units": units,
            "amount_value": units * prices.get(sym, 0.0)
        })

    # 6. Сохранить и вернуть отчёт
    report = crud.create_rebalancing_report(
        db, portfolio_id=port.id, recommendations=recommendations
    )

    return report