# app.py
from typing import Any, Dict, List
import json

from fastapi import FastAPI, HTTPException

from src.handlers.handel_message import handle_json
app = FastAPI()


@app.post("/load_data", summary="Принять JSON-список и передать в handle_json")
async def load_data(json_data: List[Dict[str, Any]],):
    """
    Принять JSON-список и передать в handle_json.
    """
    try:
        handle_json(json.dumps(json_data, ensure_ascii=False).encode("utf-8"))
        return {"status": "ok", "detail": "Данные успешно обработаны", "items": len(json_data), }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обработки: {e}")