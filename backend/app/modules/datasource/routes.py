from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.datasource.schemas import DataSourceCreate, DataSourceResponse
from app.modules.datasource.service import create_data_source, get_data_sources

router = APIRouter(
    prefix="/api/data-sources",
    tags=["Data Sources"]
)


@router.post(
    "",
    response_model=DataSourceResponse
)
def create_data_source_api(
    payload: DataSourceCreate,
    db: Session = Depends(get_db)
):
    return create_data_source(db, payload)


@router.get(
    "",
    response_model=list[DataSourceResponse]
)
def get_data_sources_api(
    db: Session = Depends(get_db)
):
    return get_data_sources(db)
