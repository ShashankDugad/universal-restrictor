"""
Dashboard routes for serving the frontend.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import os

router = APIRouter(tags=["dashboard"])

DASHBOARD_PATH = os.path.join(os.path.dirname(__file__), '../../dashboard')


@router.get("/dashboard", response_class=HTMLResponse)
@router.get("/dashboard/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard."""
    index_path = os.path.join(DASHBOARD_PATH, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)
