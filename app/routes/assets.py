from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.db import get_db

router = APIRouter(prefix="/assets", tags=["assets"])

@router.post("/", response_model=schemas.AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(
    asset_in: schemas.AssetCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new asset.

    This endpoint allows the creation of a new asset in the database. 
    It accepts asset details as input and returns the created asset.

    Args:
        asset_in (schemas.AssetCreate): The data required to create a new asset.
        db (Session): The database session dependency.

    Returns:
        schemas.AssetRead: The newly created asset.

    Raises:
        HTTPException: If there is an error during asset creation.
    """
    return crud.create_asset(db, asset_in)

@router.get("/", response_model=list[schemas.AssetRead])
def read_assets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of assets from the database.

    Args:
        skip (int): The number of records to skip for pagination. Defaults to 0.
        limit (int): The maximum number of records to return. Defaults to 100.
        db (Session): The database session dependency.

    Returns:
        list[schemas.AssetRead]: A list of assets represented as `AssetRead` schema objects.
    """
    return crud.get_assets(db, skip, limit)

@router.get("/{asset_id}", response_model=schemas.AssetRead)
def read_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve an asset by its ID.

    Args:
        asset_id (int): The ID of the asset to retrieve.
        db (Session): Database session dependency.

    Returns:
        schemas.AssetRead: The asset data if found.

    Raises:
        HTTPException: If the asset with the given ID is not found, raises a 404 error.
    """
    asset = crud.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset