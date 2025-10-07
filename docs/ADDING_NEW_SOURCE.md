# Добавление нового источника данных (модели)

Этот документ описывает шаги, необходимые для добавления нового справочника или регистра в проект DBTransferSoftTeam.

---
## Пример получаемых данных из 1С в формате json
``` json
[
{
	"НаименованиеМетаданных": "ОбщиеЗатраты",
	"Данные": [
			{
				"Период": "2025-09-10T00:00:00",
				"Регистратор": "9827e81a-8e0b-11f0-880d-60a5e22431c7",
				"СтатьяЗатрат": "300d9817-0ad6-11f0-87f5-60a5e22431c7",
				"ЭтоРасходПрошлогоПериода": true,
				"СуммаUSD": 123
			}
		]
	}
]
```
## 1. Создать модель
Модели описаны `src/db/models.py`. 

Модели описываются с использованием `SQLModel`.  
Каждая модель отражает таблицу в PostgreSQL (**заранее создавать не надо**).

Пример:
```python

class GeneralExpenses(TimestampMixin, BaseModelConfig, table=True):
    """
    ОбщиеЗатраты
    """
    __tablename__ = "general_expenses"
    __scope_delete_cols__ = ["registrar_id"]

    registrar_id: uuid.UUID = Field(primary_key=True, alias="Регистратор")
    date: datetime = Field(primary_key=True, alias="Период")
    cost_category_id: uuid.UUID = Field(primary_key=True, alias="СтатьяЗатрат")
    is_previous_period: bool | None = Field(alias="ЭтоРасходПрошлогоПериода")
    amount: Decimal | None = Field(alias="СуммаUSD")

    __table_args__ = (
        {Index("ix_ge_cost_category_id", "cost_category_id"),
            "postgresql_partition_by": "RANGE (date)"},)
```   
| Элемент                                                 | Назначение                                                                                                                   |                             Обязательно                              |
|---------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------:|
| `__tablename__ = "general_expenses"`                    | Имя таблицы в PostgreSQL (в `snake_case`)                                                                                    |                                  ✅                                   |
| `ОбщиеЗатраты`                                          | Наименование метаданных для удобного поиска в проекте                                                                        |                                  ✅                                   |
| `__scope_delete_cols__`                                 | Поля, по которым выполняется «удаление» при перезаливке данных. <br/>Если не указано, то будет использованы поля primary_key |                       ⛔️/✅ (по необходимости)                        |
| `registrar_id`                                          | Поле в таблице  PostgreSQL. Для полей не primary_key указывать дефолтное значение None                                       |                                  ✅                                   |
| `: bool \| None `                                       | Тип поля. Для полей не primary_key указывать дефолтное значение None                                                         |                    ✅                    |
| `alias="Регистратор"`                                   | Ключ из JSON, приходящего из 1С                                                                                              |                                  ✅                                   |
| `Field(primary_key=True)`                               | Указывает поля, формирующие первичный ключ                                                                                   |                                  ✅                                   |
| `{Index("ix_ge_cost_category_id", "cost_category_id")}` | Указывает на создание индекса по этому полю.                                                                                 |                       ⛔️/✅ (по необходимости)                        |
| `{"postgresql_partition_by": "RANGE (date)"}`           | Настраивает партиционирование таблицы по дате. Эти поля должны быть в primary_key                                            |                       ⛔️/✅ (по необходимости)                        |
| `TimestampMixin`, `BaseModelConfig`                     | Добавляют поля и общие настройки модели                                                                                      |                                  ✅                                   |

## 2. Добавить связь метаданных и SQL модели
`src/handlers/registry.py` 

Обновить `REGISTRY`

```python
REGISTRY = {
    # ...
    #"МестонахождениеТовара": models.GoodsLocation,
    "ОбщиеЗатраты": models.GeneralExpenses, # ОбщиеЗатраты - НаименованиеМетаданных models.GeneralExpenses - класс модели
}
```
## 3. (Опционально) Добавить в каскадное удаление
`src/handlers/registry.py`

1. Если из 1С приходят записи с пометкой на удаление в Метаданных `ТП_ДанныеНаУдаление`

Ничего дополнительно делать не нужно — система сама обработает такие записи и удалит их из базы данных при загрузке.

2. Если нужно удалять записи при удалении связанных данных

Если требуется, чтобы записи удалялись автоматически, когда удаляются связанные данные в другой таблице (например, удалили документ-регистратор или справочник, и связанные строки должны исчезнуть),
— необходимо добавить соответствие в словарь CASCADE_DELETED_MAP.
Обновить `CASCADE_DELETED_MAP`
```python
CASCADE_DELETED_MAP: dict[str, list[CascadeRule]] = {
    "Документ.тп_ПеремещениеТовара": [
        CascadeRule(model=models.GoodsTransfers, column_name="transfer_id"),
        CascadeRule(model=models.GoodsLocation, column_name="registrar_id"),
        CascadeRule(model=models.DirectExpenses, column_name="goods_doc_id"),
    ],
```
Пояснение: Если удаляется записть из `Документ.тп_ПеремещениеТовара`, 
то также буду удалены записи из таблицы модели `GoodsTransfers` по ключу `transfer_id`, `GoodsLocation` по ключу `registrar_id` 
и `DirectExpenses` по ключу `goods_doc_id`

## 4. Создание миграции БД
В терминале в корне проекта вызов автогенерации миграции
```bash
alembic revision --autogenerate -m "create_GeneralExpenses"  
```
`-m "create_GeneralExpenses"`  - связное краткое описание

Создается файл в `src/db/migrations/versions` c названием create_GeneralExpenses

Просматриваем его, проверяя на корректность. (если изменяеется столбец, то они может изменять через удаление, что нам скорее всего не требуется)
Пример создания таблицы.
```python
 op.create_table('general_expenses',
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('UTC', now())"), nullable=False),
    sa.Column('registrar_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('cost_category_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('is_previous_period', sa.Boolean(), nullable=True),
    sa.Column('amount', sa.Numeric(), nullable=True),
    sa.PrimaryKeyConstraint('registrar_id', 'date', 'cost_category_id'),
    postgresql_partition_by='RANGE (date)'
    )
```
Миграцию можно поправить вручную. Но это редкий случай. 

## 5. Исполнение миграции БД
> ⚠️ **На прод-среде выполняется автоматически при деплое.**

```bash
alembic upgrade head
```
Если у таблицы есть партиции, то требуется запустить скрипт создания партиций 
src/db/utils/partition_manager.py