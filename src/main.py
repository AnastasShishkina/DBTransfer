from src.logger.logger import setup_logging
setup_logging()
import uvicorn
from src.fastAPI import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)