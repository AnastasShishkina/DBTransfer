from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, create_engine

from src.config import settings
from src.utils import _chunked, timeit

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False)  # echo=True
EXCLUDE_UPDATE = {"created_at", "updated_at"}
BATCH_SIZE = 1000


@timeit
def upsert_data(dataModel, data):
    print("Обработка таблицы",dataModel.__tablename__, len(data))
    updatedColumns = list(
        column.name
        for column in dataModel.__table__.columns
        if not column.primary_key and column.name not in EXCLUDE_UPDATE
    )
    pkColums = list(column.name for column in dataModel.__table__.primary_key.columns)
    with Session(engine) as session:
        for batch in _chunked(data, BATCH_SIZE):
            rows = []
            for raw in batch:
                dto = dataModel.model_validate(raw)

                record = dto.dict(by_alias=False, exclude_unset=True, exclude=EXCLUDE_UPDATE)
                rows.append(record)

            if not rows:
                continue

            sqlRequest = insert(dataModel.__table__).values(rows)
            set_map = {column: getattr(sqlRequest.excluded, column) for column in updatedColumns}
            if set_map:
                set_map["updated_at"] = func.now()
                sqlRequest = sqlRequest.on_conflict_do_update(index_elements=pkColums, set_=set_map)
            else:
                sqlRequest = sqlRequest.on_conflict_do_nothing(index_elements=pkColums)
            session.exec(sqlRequest)
            session.commit()

def delinsert_data(dataModel, data):
    """
       Полная замена строк по переданным PK:
       1) CREATE TEMP TABLE AS SELECT * FROM (VALUES ... ) v(cols...)
       2) DELETE target USING temp по PK
       3) INSERT target(cols) SELECT cols FROM temp
    """
    table = dataModel.__table__

    pkColums = [col.name for col in table.primary_key.columns]
    #IN PROGRESS