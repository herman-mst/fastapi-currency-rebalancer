from sqlalchemy.orm import Session
from . import models, schemas
from .models import RebalancingReport

# --- Users ---
def create_user(db: Session, user_in: schemas.UserCreate, hashed_password: str):
    """
    Create a new user in the database.

    Args:
        db (Session): The database session used to interact with the database.
        user_in (schemas.UserCreate): The user input data containing email and risk tolerance.
        hashed_password (str): The hashed password for the user.

    Returns:
        models.User: The newly created user object.
    """
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
    """
    Retrieve a user from the database by their ID.

    Args:
        db (Session): The database session to use for the query.
        user_id (int): The ID of the user to retrieve.

    Returns:
        models.User: The user object if found, otherwise None.
    """
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    """
    Retrieve a user from the database by their email address.

    Args:
        db (Session): The database session to use for the query.
        email (str): The email address of the user to retrieve.

    Returns:
        User: The user object if found, otherwise None.
    """
    return db.query(models.User).filter(models.User.email == email).first()

# --- Assets ---
def create_asset(db: Session, asset_in: schemas.AssetCreate):
    """
    Creates a new asset in the database.

    Args:
        db (Session): The database session used to interact with the database.
        asset_in (schemas.AssetCreate): The data required to create a new asset, 
            provided as an instance of the AssetCreate schema.

    Returns:
        models.Asset: The newly created asset instance after being added to the database.
    """
    db_asset = models.Asset(**asset_in.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def get_asset(db: Session, asset_id: int):
    """
    Retrieve an asset from the database by its ID.

    Args:
        db (Session): The database session to use for the query.
        asset_id (int): The ID of the asset to retrieve.

    Returns:
        models.Asset: The asset object if found, otherwise None.
    """
    return db.query(models.Asset).filter(models.Asset.id == asset_id).first()

def get_assets(db: Session, skip: int = 0, limit: int = 100) -> list[models.Asset]:
    """
    Retrieve a list of assets from the database with optional pagination.

    Args:
        db (Session): The database session to use for the query.
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.

    Returns:
        list[models.Asset]: A list of Asset objects retrieved from the database.
    """
    return db.query(models.Asset).offset(skip).limit(limit).all()

# --- Portfolios ---
def create_portfolio(db: Session, user_id: int, portfolio_in: schemas.PortfolioCreate):
    """
    Creates a new portfolio for a user and adds associated assets to the database.

    Args:
        db (Session): The database session used to interact with the database.
        user_id (int): The ID of the user who owns the portfolio.
        portfolio_in (schemas.PortfolioCreate): The input data for creating the portfolio, 
            including the portfolio name and a list of assets with their target percentages.

    Returns:
        models.Portfolio: The newly created portfolio object, including its associated assets.

    Raises:
        SQLAlchemyError: If there is an issue with the database operation.
    """
    db_port = models.Portfolio(user_id=user_id, name=portfolio_in.name)
    db.add(db_port)
    db.commit()
    for item in portfolio_in.assets:
        db_ass = models.PortfolioAsset(
            portfolio_id=db_port.id,
            asset_id=item.asset_id,
            target_pct=item.target_pct
        )
        db.add(db_ass)
    db.commit()
    db.refresh(db_port)
    return db_port

def get_portfolio(db: Session, portfolio_id: int, user_id: int):
    """
    Retrieve a portfolio from the database based on the portfolio ID and user ID.

    Args:
        db (Session): The database session to use for the query.
        portfolio_id (int): The ID of the portfolio to retrieve.
        user_id (int): The ID of the user who owns the portfolio.

    Returns:
        models.Portfolio: The portfolio object if found, otherwise None.
    """
    return (
        db.query(models.Portfolio)
        .filter(models.Portfolio.id == portfolio_id, models.Portfolio.user_id == user_id)
        .first()
    )

def get_portfolios(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """
    Retrieve a list of portfolios for a specific user from the database.

    Args:
        db (Session): The database session to use for the query.
        user_id (int): The ID of the user whose portfolios are to be retrieved.
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.

    Returns:
        list[Portfolio]: A list of Portfolio objects belonging to the specified user.
    """
    return (
        db.query(models.Portfolio)
        .filter(models.Portfolio.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def delete_portfolio(db: Session, portfolio_id: int, user_id: int):
    """
    Deletes a portfolio from the database if it exists and belongs to the specified user.

    Args:
        db (Session): The database session to use for the operation.
        portfolio_id (int): The ID of the portfolio to delete.
        user_id (int): The ID of the user who owns the portfolio.

    Returns:
        The deleted portfolio object if it was found and deleted, otherwise None.
    """
    db_port = get_portfolio(db, portfolio_id, user_id)
    if db_port:
        db.delete(db_port)
        db.commit()
    return db_port

def create_rebalancing_report(
    db: Session,
    portfolio_id: int,
    recommendations: list[dict]
) -> RebalancingReport:
    """
    Creates a rebalancing report for a given portfolio and saves it to the database.

    Args:
        db (Session): The database session used to interact with the database.
        portfolio_id (int): The ID of the portfolio for which the rebalancing report is created.
        recommendations (list[dict]): A list of recommendation dictionaries containing rebalancing details.

    Returns:
        RebalancingReport: The newly created rebalancing report instance.
    """
    report = RebalancingReport(
        portfolio_id=portfolio_id,
        recommendations=recommendations
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report