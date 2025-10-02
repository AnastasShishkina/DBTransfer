import secrets
from typing import Annotated
from datetime import date
from typing import Any, Dict, List
import json

from fastapi import FastAPI, HTTPException, Query,  Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.db.dags import recalc_period_by_months
from src.db.db import engine, delete_with_cascade
from src.handlers.handel_message import handle_json
from src.config import basic_auth

from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import logging
log = logging.getLogger("app")

app = FastAPI()
security = HTTPBasic()


def get_current_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    if not (secrets.compare_digest(credentials.username, basic_auth.USER) and
            secrets.compare_digest(credentials.password, basic_auth.PASS)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.post("/load_data", summary="Принять JSON-список и передать в handle_json")
async def load_data(
        json_data: List[Dict[str, Any]],
        _user: str = Depends(get_current_user),
):
    """
    Принять JSON-список и передать в handle_json.
    """
    try:
        handle_json(json.dumps(json_data, ensure_ascii=False).encode("utf-8"))
        delete_with_cascade()
        return {"status": "ok", "detail": "Данные успешно обработаны", "items": len(json_data), }
    except Exception as e:
        error_message = f"Ошибка обработки: {e}"
        log.error(error_message)
        raise HTTPException(status_code=400, detail=error_message)


@app.post("/costs/recalculate")
def costs_recalculate(
        start_date: date = Query(..., description="Дата начала, формат YYYY-MM-DD"),
        end_date: date = Query(..., description="Дата конца, формат YYYY-MM-DD"),
        _user: str = Depends(get_current_user),
):

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Стартовый месяц позже конечного.")
    try:
        result = recalc_period_by_months(engine, start_date, end_date)
        return {"status": "ok", "months": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка расчёта: {e}")


STATIC_DIR = Path(__file__).resolve().parents[1] / "html"  # -> src/html
app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")

# удобный редирект с корня
@app.get("/")
def root():
    return RedirectResponse(url="/ui/")