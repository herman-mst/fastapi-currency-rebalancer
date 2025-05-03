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
    return crud.create_asset(db, asset_in)

@router.get("/", response_model=list[schemas.AssetRead])
def read_assets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return crud.get_assets(db, skip, limit)

@router.get("/{asset_id}", response_model=schemas.AssetRead)
def read_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    asset = crud.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset