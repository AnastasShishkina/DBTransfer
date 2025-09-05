from sqlmodel import SQLModel
from src.db.db import engine
#from src.logging import setup_logging
from src.consumers.consumers import start_consumer

if __name__ == "__main__":
    SQLModel.metadata.create_all(engine)
    #setup_logging()
    start_consumer()