"""Leaderboard routes for Hogwarts Legacy 5.0."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.evaluation_service import get_live_leaderboard, export_leaderboard_csv

router = APIRouter(prefix="/api/leaderboard", tags=["Leaderboard"])


@router.get("", status_code=200)
def get_leaderboard_endpoint(
    domain: Optional[str] = Query(None),
    current_round: Optional[int] = Query(None, alias="round"),
    sort_by: Optional[str] = Query("total"),
    limit: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Retrieve live leaderboard rankings, House Cup winners, and percentage stats."""
    data = get_live_leaderboard(
        db=db,
        domain=domain,
        round_num=current_round,
        sort_by=sort_by,
        limit=limit,
        search=search,
    )
    return {
        "success": True,
        "message": "Live leaderboard retrieved",
        "data": data,
    }


@router.get("/export-csv")
def export_leaderboard_csv_endpoint(
    db: Session = Depends(get_db),
):
    """Export live leaderboard rankings as an Excel-ready UTF-8 CSV."""
    csv_content = export_leaderboard_csv(db)
    csv_bytes = csv_content.encode("utf-8")
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="hogwarts_legacy_leaderboard.csv"'}
    )
