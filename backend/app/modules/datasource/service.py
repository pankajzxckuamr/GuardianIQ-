from sqlalchemy.orm import Session
from app.modules.datasource.models import DataSource
from app.modules.datasource.schemas import DataSourceCreate


def create_data_source(
    db: Session,
    payload: DataSourceCreate
):
    data_source = DataSource(
        source_name=payload.source_name,
        source_type=payload.source_type.value,
        description=payload.description,
        status=payload.status,
        owner_department_id=payload.owner_department_id
    )

    db.add(data_source)

    db.commit()

    db.refresh(data_source)

    return data_source


def get_data_sources(db: Session):
    return db.query(DataSource).all()
