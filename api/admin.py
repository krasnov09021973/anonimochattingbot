from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import sys
import os
import aiofiles

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from config import ADMIN_IDS
# from database import db
from utils.admin_auth import verify_pin
from repositories.user_repo import UserRepo
from repositories.chat_repo import ChatRepo
from repositories.report_repo import ReportRepo
from repositories.ai_repo import AIRepo

app = FastAPI(title="AnonimoChattingBot Admin Panel")

# После создания app
app.mount("/static", StaticFiles(directory="api/templates/static"), name="static")

admin_sessions = {}

async def read_template(template_name: str) -> str:
    """Читает HTML-файл шаблона"""
    template_path = os.path.join("api/templates", template_name)
    async with aiofiles.open(template_path, "r", encoding="utf-8") as f:
        return await f.read()

@app.get("/", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(content=await read_template("login.html"))

# @app.get("/site.webmanifest", response_class=HTMLResponse)
# async def site_webmanifest():
#     return HTMLResponse(content=await read_template("site.webmanifest"))

@app.post("/login", response_class=HTMLResponse)
async def login_page(pin: str = Form(...)):
    user_id = verify_pin(pin)

    if not user_id:
        login_html = await read_template("login.html")
        login_html = login_html.replace('<body>', '<body><div style="color:red;text-align:center">❌ Неверный PIN</div>')
        return HTMLResponse(content=login_html)

    import uuid
    token = str(uuid.uuid4())
    admin_sessions[token] = user_id

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="admin_token", value=token)
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    token = request.cookies.get("admin_token")
    if not token or token not in admin_sessions:
        return RedirectResponse(url="/", status_code=303)
    return HTMLResponse(content=await read_template("base.html"))

@app.get("/api/stats")
async def get_stats():
    stats = {
        'total_users': len(user_repo.get_all_users()),
        'active_24h': user_repo.get_active_users_count(days=1),
        'pending_reports': len(report_repo.get_pending_reports())
    }
    return stats

@app.get("/api/tab/{tab_name}", response_class=HTMLResponse)
async def get_tab(tab_name: str, request: Request):
    token = request.cookies.get("admin_token")
    if not token or token not in admin_sessions:
        raise HTTPException(status_code=401)

    if tab_name not in ["dashboard", "reports", "users", "premium"]:
        return HTMLResponse("Not found", status_code=404)

    return HTMLResponse(content=await read_template(f"{tab_name}.html"))

@app.get("/api/users")
async def get_users(page: int = 1, limit: int = 20, search: str = ""):
    """Список пользователей с пагинацией и поиском"""
    users_data = user_repo.get_users_paginated(page, limit, search)
    return users_data

@app.get("/api/user/{user_id}")
async def get_user(user_id: int):
    """Полная информация о пользователе (с фото)"""
    # user = db.get_user_profile_data(user_id)
    user = user_repo.get_user_profile_data(user_id)
    if not user:
        return {"error": "User not found"}

    return user

@app.post("/api/user/premium/give")
async def give_premium(request: Request):
    token = request.cookies.get("admin_token")
    if not token or token not in admin_sessions:
        raise HTTPException(status_code=401)
    data = await request.json()
    user_id = data.get('user_id')
    duration = data.get('duration', 'month')

    # Рассчитываем дату окончания
    from datetime import datetime, timedelta
    now = datetime.now()
    if duration == 'day':
        until = now + timedelta(days=1)
    elif duration == 'week':
        until = now + timedelta(weeks=1)
    elif duration == 'month':
        until = now + timedelta(days=30)
    elif duration == '3months':
        until = now + timedelta(days=90)
    elif duration == 'year':
        until = now + timedelta(days=365)
    else:  # forever
        until = None

    # success = db.set_premium_with_expiry(user_id, until)
    success = user_repo.set_premium(user_id, duration_days=until)  # где duration_days = 7, 30, 180, 365
    return {"success": success}

@app.post("/api/user/premium/revoke")
async def revoke_premium(request: Request):
    token = request.cookies.get("admin_token")
    if not token or token not in admin_sessions:
        raise HTTPException(status_code=401)
    data = await request.json()
    user_id = data.get('user_id')
    # success = db.revoke_premium(user_id)
    success = user_repo.revoke_premium(user_id)
    return {"success": success}

@app.post("/api/user/delete")
async def delete_user(request: Request):
    token = request.cookies.get("admin_token")
    if not token or token not in admin_sessions:
        raise HTTPException(status_code=401)
    data = await request.json()
    user_id = data.get('user_id')
    # success = db.delete_user(user_id)
    success = user_repo.delete_user(user_id)
    return {"success": success}

@app.get("/api/reports")
async def get_reports():
    reports = report_repo.get_pending_reports()
    return reports

@app.post("/api/reports/{report_id}/resolve")
async def resolve_report_api(report_id: int, request: Request):
    token = request.cookies.get("admin_token")
    if not token or token not in admin_sessions:
        raise HTTPException(status_code=401)

    admin_id = admin_sessions[token]
    data = await request.json()
    action = data.get('action')
    notes = data.get('notes', '')

    if action not in ['confirm', 'warn', 'reject']:
        return {"error": "Invalid action"}

    # success = db.resolve_report(report_id, admin_id, action, notes)
    success, msg = report_service.resolve_report(report_id, admin_id, action, notes)
    return {"success": success}

@app.get("/api/report/{report_id}")
async def get_report(report_id: int):
    return report_repo.get_report(report_id)

@app.get("/api/reports/{status}")
async def get_reports(status: str, page: int = 1, limit: int = 20, search: str = ""):
    reports_data = report_repo.get_reports_by_status_paginated(status, page, limit, search)
    return reports_data
