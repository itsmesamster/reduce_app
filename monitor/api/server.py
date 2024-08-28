# standard
import os
from pathlib import Path

# 3rd party
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# project
from app.core.utils import REPORTS_DIR


api = FastAPI()

Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
api.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")

templates = Jinja2Templates(directory="monitor/api")


@api.get("/reports", response_class=HTMLResponse)
def list_files(request: Request):
    files = sorted(os.listdir(REPORTS_DIR))
    files.reverse()
    last = files[0].split("_finished_at_") if files else ""
    last_on = (
        f'on {last[0]} at {last[1].split("_in_")[0].split(".")[0]}' if last else ""
    )
    files_with_paths: dict = {
        file_name: f"{request.url._url}/{file_name}" for file_name in files
    }
    return templates.TemplateResponse(
        "list_reports.html",
        {"request": request, "files": files_with_paths, "last_on": last_on},
    )
