# app.py
from datetime import date
from typing import Any, Dict, List
import json

from fastapi import FastAPI, HTTPException, Query

from src.db.dags import recalc_period_by_months
from src.db.db import engine
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


@app.post("/costs/recalculate")
def costs_recalculate(
        start_date: date = Query(..., description="Дата начала, формат YYYY-MM-DD"),
        end_date: date = Query(..., description="Дата конца, формат YYYY-MM-DD"),):

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Стартовый месяц позже конечного.")
    try:
        result = recalc_period_by_months(engine, start_date, end_date)
        return {"status": "ok", "months": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка расчёта: {e}")