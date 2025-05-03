from datetime import datetime
from pydantic import BaseModel, EmailStr, constr, Field
from typing import List, Optional, Dict

# --- User ---
class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=6)
    risk_tolerance: Optional[float] = 0.5

class UserRead(BaseModel):
    id: int
    email: EmailStr
    risk_tolerance: float

    class Config:
        orm_mode = True

class TokenRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Asset ---
class AssetBase(BaseModel):
    symbol: str
    type: str
    volatility: float
    expected_return: float

class AssetCreate(AssetBase):
    pass

class AssetRead(AssetBase):
    id: int

    class Config:
        orm_mode = True

# --- PortfolioAsset ---
class PortfolioAssetRead(BaseModel):
    asset: AssetRead
    target_pct: float
    quantity: float

    class Config:
        orm_mode = True

class PortfolioAssetCreate(BaseModel):
    asset_id: int = Field(..., description="ID актива из таблицы assets")
    target_pct: float = Field(..., ge=0, le=1, description="Целевая доля от 0 до 1")
    quantity: float = Field(..., ge=0, description="Фактическое количество единиц актива")

# --- Portfolio ---
class PortfolioCreate(BaseModel):
    name: str = Field(..., description="Название портфеля")
    assets: List[PortfolioAssetCreate] = Field(
        default_factory=list,
        description="Список позиций портфеля"
    )

    class Config:
        schema_extra = {
            "example": {
                "name": "name",
                "assets": [
                    {
                        "asset_id": None,
                        "target_pct": None,
                        "quantity": None
                    }
                ]
            }
        }

class PortfolioRead(BaseModel):
    id: int
    name: str
    assets: List[PortfolioAssetRead] = []

    class Config:
        orm_mode = True

# --- Rebalancing Report ---
class Recommendation(BaseModel):
    symbol: str
    current_pct: float
    target_pct: float
    action: str  # "buy" или "sell"
    amount_units: float
    amount_value: float

class RebalancingReportRead(BaseModel):
    id: int
    portfolio_id: int
    generated_at: datetime
    recommendations: List[Recommendation]

    class Config:
        orm_mode = True