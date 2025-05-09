"""
Module containing SQLAlchemy models for the FastAPI currency rebalancer project.
All models represent database tables and include basic documentation.
"""
import datetime
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, JSON
)
from sqlalchemy.orm import relationship
from .db import Base

# pylint: disable=too-few-public-methods
class User(Base):
    """
    User model representing an application user.

    Attributes:
        id (int): Primary key.
        email (str): User's email address.
        password_hash (str): Hashed password.
        risk_tolerance (float): User's risk tolerance.
        portfolios (list): Related portfolios.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    risk_tolerance = Column(Float, default=0.5)

    portfolios = relationship("Portfolio", back_populates="owner")

# pylint: disable=too-few-public-methods
class Asset(Base):
    """
    Asset model representing a financial asset.

    Attributes:
        id (int): Primary key.
        symbol (str): Asset symbol.
        type (str): Asset type.
        volatility (float): Asset volatility.
        expected_return (float): Expected return of the asset.
    """
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, nullable=False)
    volatility = Column(Float, nullable=False)
    expected_return = Column(Float, nullable=False)

    portfolio_assets = relationship("PortfolioAsset", back_populates="asset")

# pylint: disable=too-few-public-methods
class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)

    owner = relationship("User", back_populates="portfolios")
    assets = relationship("PortfolioAsset", back_populates="portfolio", cascade="all, delete-orphan")
    rebalancing_reports = relationship("RebalancingReport", back_populates="portfolio")

# pylint: disable=too-few-public-methods
class PortfolioAsset(Base):
    __tablename__ = "portfolio_assets"

    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    target_pct = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)

    portfolio = relationship("Portfolio", back_populates="assets")
    asset = relationship("Asset", back_populates="portfolio_assets")

# pylint: disable=too-few-public-methods
class RebalancingReport(Base):
    __tablename__ = "rebalancing_reports"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
    recommendations = Column(JSON, nullable=False)

    portfolio = relationship("Portfolio", back_populates="rebalancing_reports")
