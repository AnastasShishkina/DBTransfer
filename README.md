# DBTransferSoftTeam

Сервис для загрузки данных из 1С и расчёта агрегатов в PostgreSQL.
Проект написан на Python 3, использует SQLAlchemy/SQLModel и PostgreSQL как хранилище данных.
Для обмена сообщениями планируется или POST запрос или RabbitMQ.

## Структура проекта

```bash
src/
 ├── config.py           # Настройки проекта (DATABASE_URL, RabbitMQ и т.п.) переменные берем из .env
 ├── consumers 			 # Заготовка под RabbitMQ (не используется)
 ├── data 				 # Файлы .json для загрузки
 ├── db/
 │    ├── db.py          # engine, подключение к БД, сохранение данных в таблицы
 │    ├── models.py      # SQLModel-модели
 │    └── dags.py      	 # SQL для расчетов
 ├── handlers/
 │    ├── first_load_data.py  # Скрипт первой загрузки JSON в БД
 │    ├── handle_message.py   # Обработка JSON
 │    └── registry.py  # Связь SQLModel-модели и формата данных из 1С
 ├── migrations/ 	# Инструмент для создания БД (создание/изменение таблиц)
 │    └── versions  # версии изменений в структуре БД
 ├── utils/
 │   
 ├── migrations/ 	# Инструмент для создания БД (создание/изменение таблиц)
 └── tests	  # тeстовые скрипты (запуск тестого продьюсера, загрузка 1 файла)

```
## Установка


```bash
git clone https://github.com/<your-org>/DBTransferSoftTeam.git
cd DBTransferSoftTeam

python -m venv .venv
source .venv/bin/activate   # (Windows: .venv\Scripts\activate)

pip install -r requirements.txt
```



## Переменные окружения
Премененные для подключения БД 

Создай файл .env в корне проекта: и заполни по примеру файла .env_example

## Добавление новой таблицы для источника

1) В модуле *src/db/models.py* Добавь класс для новой таблицы.


```python
class GoodsReceipts(TimestampMixin, BaseModelConfig, table=True):
    """
    Наименование метаданных
    """
    __tablename__ = "table" # table Название таблицы

 #  receipt_id: uuid.UUID = Field(primary_key=True, alias="СсылкаДокумента")
 #  receipt_id - наименование поля в таблице 
 #  uuid.UUID - тип поля
 #  primary_key=True - поле входит в уникальный ключ
 #  alias="СсылкаДокумента" - это ключ в JSON. по этому ключу будет записываться информация в поле таблицы
    receipt_id: uuid.UUID = Field(primary_key=True, alias="СсылкаДокумента")
    date: datetime = Field(primary_key=True, alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    __table_args__ = (
        Index("ix_we_number", "number"),
    )
```

2) В модуле *src/handlers/registry.py* укажите связь Названия из JSON и SQL-модели
3) Создайте новую версию миграции
```bash
alembic revision --autogenerate -m "message"
```
В *src/migrations/versions* будет создана мграция на изменение структуры таблиц
4) Примените изменения структуры таблиц
```bash
alembic upgrade head   
```
5) Можно производить загрузку в новую таблицу
  
