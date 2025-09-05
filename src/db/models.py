import uuid
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, func

ZERO = uuid.UUID("00000000-0000-0000-0000-000000000000")


class StagingBase(SQLModel):
    created_at: datetime = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    model_config = {"populate_by_name": True}


class StgExpenseItem(StagingBase, table=True):
    __tablename__ = "stg_expense_items"
    external_id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    version: Optional[str] = Field(default=None, alias="ВерсияДанных")
    is_deleted: bool = Field(alias="ПометкаУдаления")
    parent_extid: Optional[uuid.UUID] = Field(default=None, alias="Родитель")
    is_group: bool = Field(alias="ЭтоГруппа")
    code: str = Field(alias="Код", max_length=64)
    name: str = Field(alias="Наименование", max_length=255)


class StgCitiesV1(StagingBase, table=True):
    __tablename__ = "stg_cities_v1"
    external_id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    version: Optional[str] = Field(default=None, alias="ВерсияДанных")
    is_deleted: bool = Field(alias="ПометкаУдаления")
    parent_extid: Optional[uuid.UUID] = Field(default=None, alias="Родитель")
    is_group: bool = Field(alias="ЭтоГруппа")
    code: str = Field(alias="Код")
    name: str = Field(alias="Наименование")


class StgCitiesV2(StagingBase, table=True):
    __tablename__ = "stg_cities_v2"
    external_id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    version: Optional[str] = Field(default=None, alias="ВерсияДанных")
    is_deleted: bool = Field(alias="ПометкаУдаления")
    code: str = Field(alias="Код")
    name: str = Field(alias="Наименование")
    country_extid: Optional[uuid.UUID] = Field(default=None, alias="Страна")