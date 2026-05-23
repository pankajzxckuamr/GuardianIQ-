from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.datasource.schemas import DataSourceCreate, DataSourceResponse
from app.modules.datasource.service import create_data_source, get_data_sources
from app.shared.response_utils import ResponseHelper
from app.shared.responses import StandardResponse

router = APIRouter(
    prefix="/api/data-sources",
    tags=["Data Sources"]
)


@router.post(
    "",
    response_model=StandardResponse[DataSourceResponse]
)
def create_data_source_api(
    payload: DataSourceCreate,
    db: Session = Depends(get_db)
):
    result = create_data_source(db, payload)
    return ResponseHelper.created(
        data=result,
        message="Data source created successfully"
    )


@router.get(
    "",
    response_model=StandardResponse[list[DataSourceResponse]]
)
def get_data_sources_api(
    db: Session = Depends(get_db)
):
    result = get_data_sources(db)
    return ResponseHelper.list_response(
        items=result,
        message="Data sources retrieved successfully"
    )
