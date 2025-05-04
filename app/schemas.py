from datetime import datetime
from pydantic import BaseModel, EmailStr, constr, Field
from typing import List, Optional

# --- User ---
class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: constr(min_length=6) = Field(..., description="User's password, at least 6 characters long")
    risk_tolerance: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="User's risk tolerance (0 to 1)")

class UserRead(BaseModel):
    id: int = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User's email address")
    risk_tolerance: float = Field(..., ge=0.0, le=1.0, description="User's risk tolerance (0 to 1)")

    class Config:
        from_attributes = True

class TokenRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: constr(min_length=6) = Field(..., description="User's password, at least 6 characters long")

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token string")
    token_type: str = Field("bearer", description="Type of the token, typically 'bearer'")

class TokenData(BaseModel):
    user_id: Optional[int] = None

# --- Asset ---
class AssetBase(BaseModel):
    symbol: str = Field(..., description="Ticker symbol of the asset, e.g., 'AAPL'")
    type: str = Field(..., description="Asset type, e.g., 'stock', 'bond', 'crypto'")
    volatility: float = Field(..., ge=0.0, description="Historical volatility of the asset")
    expected_return: float = Field(..., description="Expected return of the asset")

class AssetCreate(AssetBase):
    pass

class AssetRead(AssetBase):
    id: int = Field(..., description="Unique asset identifier")

    class Config:
        from_attributes = True

# --- PortfolioAsset ---
class PortfolioAssetCreate(BaseModel):
    asset_id: int = Field(..., ge=1, description="ID of the asset from the assets table")
    target_pct: float = Field(..., ge=0.0, le=1.0, description="Target allocation percentage (0 to 1)")
    quantity: float = Field(..., ge=0.0, description="Actual quantity of the asset")

class PortfolioAssetRead(BaseModel):
    asset: AssetRead = Field(..., description="Asset details")
    target_pct: float = Field(..., ge=0.0, le=1.0, description="Target allocation percentage (0 to 1)")
    quantity: float = Field(..., ge=0.0, description="Actual quantity of the asset")

    class Config:
        from_attributes = True

# --- Portfolio ---
class PortfolioCreate(BaseModel):
    name: str = Field(..., description="Portfolio name")
    assets: List[PortfolioAssetCreate] = Field(
        default_factory=list,
        description="List of portfolio asset positions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Portfolio",
                "assets": [
                    {
                        "asset_id": 1,
                        "target_pct": 0.5,
                        "quantity": 10.0
                    }
                ]
            }
        }

class PortfolioRead(BaseModel):
    id: int = Field(..., description="Unique portfolio identifier")
    name: str = Field(..., description="Portfolio name")
    assets: List[PortfolioAssetRead] = Field(default_factory=list, description="List of portfolio assets")

    class Config:
        from_attributes = True

# --- Recommendation ---
class Recommendation(BaseModel):
    symbol: str = Field(..., description="Ticker symbol of the recommended asset")
    current_pct: float = Field(..., ge=0.0, le=1.0, description="Current portfolio percentage of the asset")
    target_pct: float = Field(..., ge=0.0, le=1.0, description="Desired portfolio percentage of the asset")
    action: str = Field(..., description="Action to take: 'buy' or 'sell'")
    amount_units: float = Field(..., ge=0.0, description="Number of units to buy or sell")
    amount_value: float = Field(..., ge=0.0, description="Monetary value of the transaction")

# --- Rebalancing Report ---
class RebalancingReportRead(BaseModel):
    id: int = Field(..., description="Unique report identifier")
    portfolio_id: int = Field(..., ge=1, description="ID of the portfolio this report belongs to")
    generated_at: datetime = Field(..., description="Timestamp when the report was generated")
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="List of buy/sell recommendations for rebalancing"
    )

    class Config:
        from_attributes = True