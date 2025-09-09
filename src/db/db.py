from sqlmodel import create_engine, Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
from src.config import settings
from itertools import islice

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=True) # echo=True
EXCLUDE_UPDATE  = {"created_at", "updated_at"}
BATCH_SIZE = 1000

def get_session():
    return Session(engine)


def _chunked(iterable, size):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk


def upsert_data(configMetaData, data):
    dataModel = configMetaData['model']
    updatedColumns = list(column.name for column in dataModel.__table__.columns if not column.primary_key and column.name not in EXCLUDE_UPDATE )
    pkColums = list(column.name for column in dataModel.__table__.columns if  column.primary_key)
    with Session(engine) as session:
        for batch in _chunked(data, BATCH_SIZE):
            rows = []
            for raw in batch:
                dto = dataModel.model_validate(raw)
                record = dto.dict( by_alias=False, exclude_unset=True,  exclude=EXCLUDE_UPDATE )
                rows.append(record)

            if not rows:
                continue

            sqlRequest = insert(dataModel.__table__).values(rows)
            set_map = {column: getattr(sqlRequest.excluded, column) for column in updatedColumns}
            set_map["updated_at"] = func.now()
            sqlRequest = sqlRequest.on_conflict_do_update( index_elements=pkColums,set_=set_map, )
            session.exec(sqlRequest)
            session.commit()
