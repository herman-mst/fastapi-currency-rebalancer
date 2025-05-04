"""
Module containing Pydantic schemas for the FastAPI currency rebalancer project.
All schemas are used for data validation and serialization/deserialization.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, constr, Field

# --- User ---

# pylint: disable=too-few-public-methods
class UserCreate(BaseModel):
    """Schema for creating a user."""
    email: EmailStr = Field(
        ..., description="User's email address"
    )
    password: constr(min_length=6) = Field(
        ..., description="User's password, at least 6 characters long"
    )
    risk_tolerance: Optional[float] = Field(
        0.5, ge=0.0, le=1.0,
        description="User's risk tolerance (0 to 1)"
    )

# pylint: disable=too-few-public-methods
class UserRead(BaseModel):
    """Schema for reading a user."""
    id: int = Field(
        ..., description="Unique user identifier"
    )
    email: EmailStr = Field(
        ..., description="User's email address"
    )
    risk_tolerance: float = Field(
        ..., ge=0.0, le=1.0,
        description="User's risk tolerance (0 to 1)"
    )

    # pylint: disable=missing-class-docstring
    class Config:
        from_attributes = True

# pylint: disable=too-few-public-methods
class TokenRequest(BaseModel):
    """Schema for token generation request."""
    email: EmailStr = Field(
        ..., description="User's email address"
    )
    password: constr(min_length=6) = Field(
        ..., description="User's password, at least 6 characters long"
    )

# pylint: disable=too-few-public-methods
class Token(BaseModel):
    """Schema for JWT token."""
    access_token: str = Field(
        ..., description="JWT access token string"
    )
    token_type: str = Field(
        "bearer", description="Type of the token, typically 'bearer'"
    )

# pylint: disable=too-few-public-methods
class TokenData(BaseModel):
    """Schema for token data."""
    user_id: Optional[int] = None

# --- Asset ---

# pylint: disable=too-few-public-methods
class AssetBase(BaseModel):
    """Base schema for asset information."""
    symbol: str = Field(
        ..., description="Ticker symbol of the asset, e.g., 'AAPL'"
    )
    type: str = Field(
        ..., description="Asset type, e.g., 'stock', 'bond', 'crypto'"
    )
    volatility: float = Field(
        ..., ge=0.0,
        description="Historical volatility of the asset"
    )
    expected_return: float = Field(
        ..., description="Expected return of the asset"
    )

# pylint: disable=too-few-public-methods
class AssetCreate(AssetBase):
    """Schema for creating an asset."""
    ...

# pylint: disable=too-few-public-methods
class AssetRead(AssetBase):
    """Schema for reading an asset."""
    id: int = Field(
        ..., description="Unique asset identifier"
    )

    # pylint: disable=missing-class-docstring
    class Config:
        from_attributes = True

# --- PortfolioAsset ---

# pylint: disable=too-few-public-methods
class PortfolioAssetCreate(BaseModel):
    """Schema for creating a portfolio asset entry."""
    asset_id: int = Field(
        ..., ge=1, description="ID of the asset from the assets table"
    )
    target_pct: float = Field(
        ..., ge=0.0, le=1.0,
        description="Target allocation percentage (0 to 1)"
    )
    quantity: float = Field(
        ..., ge=0.0,
        description="Actual quantity of the asset"
    )

# pylint: disable=too-few-public-methods
class PortfolioAssetRead(BaseModel):
    """Schema for reading a portfolio asset entry."""
    asset: AssetRead = Field(
        ..., description="Asset details"
    )
    target_pct: float = Field(
        ..., ge=0.0, le=1.0,
        description="Target allocation percentage (0 to 1)"
    )
    quantity: float = Field(
        ..., ge=0.0,
        description="Actual quantity of the asset"
    )

    # pylint: disable=missing-class-docstring
    class Config:
        from_attributes = True

# --- Portfolio ---

# pylint: disable=too-few-public-methods
class PortfolioCreate(BaseModel):
    """Schema for creating a portfolio."""
    name: str = Field(
        ..., description="Portfolio name"
    )
    assets: List[PortfolioAssetCreate] = Field(
        default_factory=list,
        description="List of portfolio asset positions"
    )

    # pylint: disable=missing-class-docstring
    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Portfolio",
                "assets": [{
                    "asset_id": 1,
                    "target_pct": 0.5,
                    "quantity": 10.0
                }]
            }
        }

# pylint: disable=too-few-public-methods
class PortfolioRead(BaseModel):
    """Schema for reading a portfolio."""
    id: int = Field(
        ..., description="Unique portfolio identifier"
    )
    name: str = Field(
        ..., description="Portfolio name"
    )
    assets: List[PortfolioAssetRead] = Field(
        default_factory=list,
        description="List of portfolio assets"
    )

    # pylint: disable=missing-class-docstring
    class Config:
        from_attributes = True

# --- Recommendation ---

# pylint: disable=too-few-public-methods
class Recommendation(BaseModel):
    """Schema for rebalancing recommendation."""
    symbol: str = Field(
        ..., description="Ticker symbol of the recommended asset"
    )
    current_pct: float = Field(
        ..., ge=0.0, le=1.0,
        description="Current portfolio percentage of the asset"
    )
    target_pct: float = Field(
        ..., ge=0.0, le=1.0,
        description="Desired portfolio percentage of the asset"
    )
    action: str = Field(
        ..., description="Action to take: 'buy' or 'sell'"
    )
    amount_units: float = Field(
        ..., ge=0.0,
        description="Number of units to buy or sell"
    )
    amount_value: float = Field(
        ..., ge=0.0,
        description="Monetary value of the transaction"
    )

# --- Rebalancing Report ---

# pylint: disable=too-few-public-methods
class RebalancingReportRead(BaseModel):
    """Schema for reading a rebalancing report."""
    id: int = Field(
        ..., description="Unique report identifier"
    )
    portfolio_id: int = Field(
        ..., ge=1,
        description="ID of the portfolio this report belongs to"
    )
    generated_at: datetime = Field(
        ..., description="Timestamp when the report was generated"
    )
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="List of buy/sell recommendations for rebalancing"
    )

    # pylint: disable=missing-class-docstring
    class Config:
        from_attributes = True
