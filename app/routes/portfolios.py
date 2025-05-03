from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.db import get_db
from app.core.security import get_current_user
from typing import List

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