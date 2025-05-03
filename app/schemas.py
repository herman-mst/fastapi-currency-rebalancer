from datetime import datetime
from pydantic import BaseModel, EmailStr, constr, condecimal
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

# --- PortfolioAsset (для вложенных портфелей) ---
class PortfolioAssetRead(BaseModel):
    asset: AssetRead
    target_pct: float

    class Config:
        orm_mode = True

# --- Portfolio ---
class PortfolioCreate(BaseModel):
    name: str
    assets: Optional[List[Dict[str, float]]] = []

class PortfolioRead(BaseModel):
    id: int
    name: str
    assets: List[PortfolioAssetRead] = []

    class Config:
        orm_mode = True
