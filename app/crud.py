from sqlalchemy.orm import Session
from . import models, schemas
from typing import List

# --- Users ---
def create_user(db: Session, user_in: schemas.UserCreate, hashed_password: str):
    db_user = models.User(
        email=user_in.email,
        password_hash=hashed_password,
        risk_tolerance=user_in.risk_tolerance
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# --- Assets ---
def create_asset(db: Session, asset_in: schemas.AssetCreate):
    db_asset = models.Asset(**asset_in.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def get_asset(db: Session, asset_id: int):
    return db.query(models.Asset).filter(models.Asset.id == asset_id).first()

def get_assets(db: Session, skip: int = 0, limit: int = 100) -> List[models.Asset]:
    return db.query(models.Asset).offset(skip).limit(limit).all()

# --- Portfolios ---
def create_portfolio(db: Session, user_id: int, portfolio_in: schemas.PortfolioCreate):
    db_port = models.Portfolio(user_id=user_id, name=portfolio_in.name)
    db.add(db_port)
    db.commit()
    # привязка активов, если заданы
    for item in portfolio_in.assets:
        db_ass = models.PortfolioAsset(
            portfolio_id=db_port.id,
            asset_id=item["asset_id"],
            target_pct=item["target_pct"]
        )
        db.add(db_ass)
    db.commit()
    db.refresh(db_port)
    return db_port

def get_portfolio(db: Session, portfolio_id: int, user_id: int):
    return (
        db.query(models.Portfolio)
        .filter(models.Portfolio.id == portfolio_id, models.Portfolio.user_id == user_id)
        .first()
    )

def get_portfolios(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Portfolio)
        .filter(models.Portfolio.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def delete_portfolio(db: Session, portfolio_id: int, user_id: int):
    db_port = get_portfolio(db, portfolio_id, user_id)
    if db_port:
        db.delete(db_port)
        db.commit()
    return db_port
