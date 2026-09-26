"""Evaluation and live leaderboard service for Hogwarts Legacy 5.0 (Phase 3)."""
import io
import csv
from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func

from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus
from app.models.domain import Domain, DomainName
from app.models.audit_log import AuditLog
from app.models.review import ReviewRound1, ReviewRound2, ReviewRound3
from app.schemas.review import ReviewRound1Submit, ReviewRound2Submit, ReviewRound3Submit


def get_team_and_project(db: Session, team_id: int) -> tuple[User, Project]:
    """Fetch team user and their project, or raise 404."""
    user = db.query(User).filter(User.id == team_id, User.role == UserRole.USER).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": f"Team #{team_id} not found", "error_code": "TEAM_NOT_FOUND"},
        )
    project = db.query(Project).filter(Project.user_id == user.id).first()
    if not project:
        # Create default draft project container if team has none yet
        from app.services.project_service import _next_project_code
        prefix = "OI" if (user.domain and user.domain.name == "OPEN_INNOVATION") else ("AI" if (user.domain and user.domain.name == "AI") else "CY")
        project = Project(
            project_code=f"PRJ-{prefix}-{user.id:04d}",
            user_id=user.id,
            domain_id=user.domain_id,
            project_title=f"{user.team_name or user.name} Project",
            status=ProjectStatus.SUBMITTED,
            current_round=1,
            is_submitted=True,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
    return user, project


def submit_review_round_1(db: Session, team_id: int, data: ReviewRound1Submit, admin: User) -> ReviewRound1:
    """Save draft or submit final evaluation for Review Round 1 (Max 60)."""
    user, project = get_team_and_project(db, team_id)
    total = data.calculate_total()

    # Check if a review already exists for round 1
    rev = db.query(ReviewRound1).filter(ReviewRound1.team_id == team_id).order_by(ReviewRound1.id.desc()).first()

    now = datetime.now(timezone.utc)
    is_completed = not data.is_draft

    if not rev:
        rev = ReviewRound1(
            team_id=team_id,
            project_id=project.id,
            evaluator_name=data.evaluator_name or admin.name or "Chief Arbiter",
            score_problem_clarity=data.score_problem_clarity,
            score_solution_quality=data.score_solution_quality,
            score_tech_stack=data.score_tech_stack,
            score_idea_presentation=data.score_idea_presentation,
            score_feasibility=data.score_feasibility,
            score_confidence_qa=data.score_confidence_qa,
            total_score=total,
            comments=data.comments,
            suggestions=data.suggestions,
            status="COMPLETED" if is_completed else "DRAFT",
            is_locked=is_completed,
            is_published=True,
            evaluated_at=now,
        )
        db.add(rev)
    else:
        # Update existing record
        rev.evaluator_name = data.evaluator_name or admin.name or rev.evaluator_name
        rev.score_problem_clarity = data.score_problem_clarity
        rev.score_solution_quality = data.score_solution_quality
        rev.score_tech_stack = data.score_tech_stack
        rev.score_idea_presentation = data.score_idea_presentation
        rev.score_feasibility = data.score_feasibility
        rev.score_confidence_qa = data.score_confidence_qa
        rev.total_score = total
        rev.comments = data.comments
        rev.suggestions = data.suggestions
        rev.status = "COMPLETED" if is_completed else "DRAFT"
        rev.is_locked = is_completed
        rev.evaluated_at = now

    if is_completed and project.current_round < 2:
        project.current_round = 2

    # Audit log
    audit = AuditLog(
        admin_id=admin.id,
        action="EVALUATION_ROUND_1",
        target_type="team",
        target_id=team_id,
        description=f"Round 1 Evaluation: score {total}/60 (draft={data.is_draft}) by {rev.evaluator_name}",
    )
    db.add(audit)
    db.commit()
    db.refresh(rev)
    return rev


def submit_review_round_2(db: Session, team_id: int, data: ReviewRound2Submit, admin: User) -> ReviewRound2:
    """Save draft or submit final evaluation for Review Round 2 (Max 70)."""
    user, project = get_team_and_project(db, team_id)
    total = data.calculate_total()

    r1 = db.query(ReviewRound1).filter(ReviewRound1.team_id == team_id).order_by(ReviewRound1.id.desc()).first()
    rev = db.query(ReviewRound2).filter(ReviewRound2.team_id == team_id).order_by(ReviewRound2.id.desc()).first()

    now = datetime.now(timezone.utc)
    is_completed = not data.is_draft

    if not rev:
        rev = ReviewRound2(
            team_id=team_id,
            project_id=project.id,
            review_round_1_id=r1.id if r1 else None,
            evaluator_name=data.evaluator_name or admin.name or "Chief Arbiter",
            score_planning_workflow=data.score_planning_workflow,
            score_frontend_progress=data.score_frontend_progress,
            score_backend_progress=data.score_backend_progress,
            score_prototype_progress=data.score_prototype_progress,
            score_technical_quality=data.score_technical_quality,
            score_team_collaboration=data.score_team_collaboration,
            score_milestone_completion=data.score_milestone_completion,
            total_score=total,
            review_notes=data.review_notes,
            improvement_suggestions=data.improvement_suggestions,
            status="COMPLETED" if is_completed else "DRAFT",
            is_locked=is_completed,
            is_published=True,
            evaluated_at=now,
        )
        db.add(rev)
    else:
        rev.evaluator_name = data.evaluator_name or admin.name or rev.evaluator_name
        rev.score_planning_workflow = data.score_planning_workflow
        rev.score_frontend_progress = data.score_frontend_progress
        rev.score_backend_progress = data.score_backend_progress
        rev.score_prototype_progress = data.score_prototype_progress
        rev.score_technical_quality = data.score_technical_quality
        rev.score_team_collaboration = data.score_team_collaboration
        rev.score_milestone_completion = data.score_milestone_completion
        rev.total_score = total
        rev.review_notes = data.review_notes
        rev.improvement_suggestions = data.improvement_suggestions
        rev.status = "COMPLETED" if is_completed else "DRAFT"
        rev.is_locked = is_completed
        rev.evaluated_at = now

    if is_completed and project.current_round < 3:
        project.current_round = 3

    audit = AuditLog(
        admin_id=admin.id,
        action="EVALUATION_ROUND_2",
        target_type="team",
        target_id=team_id,
        description=f"Round 2 Evaluation: score {total}/70 (draft={data.is_draft}) by {rev.evaluator_name}",
    )
    db.add(audit)
    db.commit()
    db.refresh(rev)
    return rev


def submit_review_round_3(db: Session, team_id: int, data: ReviewRound3Submit, admin: User) -> ReviewRound3:
    """Save draft or submit final evaluation for Review Round 3 (Max 70)."""
    user, project = get_team_and_project(db, team_id)
    total = data.calculate_total()

    r2 = db.query(ReviewRound2).filter(ReviewRound2.team_id == team_id).order_by(ReviewRound2.id.desc()).first()
    rev = db.query(ReviewRound3).filter(ReviewRound3.team_id == team_id).order_by(ReviewRound3.id.desc()).first()

    now = datetime.now(timezone.utc)
    is_completed = not data.is_draft

    if not rev:
        rev = ReviewRound3(
            team_id=team_id,
            project_id=project.id,
            review_round_2_id=r2.id if r2 else None,
            evaluator_name=data.evaluator_name or admin.name or "Chief Arbiter",
            score_tech_understanding=data.score_tech_understanding,
            score_problem_solution_fit=data.score_problem_solution_fit,
            score_innovation_creativity=data.score_innovation_creativity,
            score_prototype_functionality=data.score_prototype_functionality,
            score_solution_completeness=data.score_solution_completeness,
            score_teamwork_execution=data.score_teamwork_execution,
            score_qa_handling=data.score_qa_handling,
            total_score=total,
            final_remarks=data.final_remarks,
            strengths=data.strengths,
            weaknesses=data.weaknesses,
            recommendation=data.recommendation,
            status="COMPLETED" if is_completed else "DRAFT",
            is_locked=is_completed,
            is_published=True,
            evaluated_at=now,
        )
        db.add(rev)
    else:
        rev.evaluator_name = data.evaluator_name or admin.name or rev.evaluator_name
        rev.score_tech_understanding = data.score_tech_understanding
        rev.score_problem_solution_fit = data.score_problem_solution_fit
        rev.score_innovation_creativity = data.score_innovation_creativity
        rev.score_prototype_functionality = data.score_prototype_functionality
        rev.score_solution_completeness = data.score_solution_completeness
        rev.score_teamwork_execution = data.score_teamwork_execution
        rev.score_qa_handling = data.score_qa_handling
        rev.total_score = total
        rev.final_remarks = data.final_remarks
        rev.strengths = data.strengths
        rev.weaknesses = data.weaknesses
        rev.recommendation = data.recommendation
        rev.status = "COMPLETED" if is_completed else "DRAFT"
        rev.is_locked = is_completed
        rev.evaluated_at = now

    if is_completed:
        project.status = ProjectStatus.COMPLETED

    audit = AuditLog(
        admin_id=admin.id,
        action="EVALUATION_ROUND_3",
        target_type="team",
        target_id=team_id,
        description=f"Round 3 Evaluation: score {total}/70 (draft={data.is_draft}) by {rev.evaluator_name}",
    )
    db.add(audit)
    db.commit()
    db.refresh(rev)
    return rev


def get_team_evaluation_details(db: Session, team_id: int) -> Dict[str, Any]:
    """Fetch complete evaluation details across R1, R2, R3 for a team."""
    user, project = get_team_and_project(db, team_id)

    r1 = db.query(ReviewRound1).filter(ReviewRound1.team_id == team_id).order_by(ReviewRound1.id.desc()).first()
    r2 = db.query(ReviewRound2).filter(ReviewRound2.team_id == team_id).order_by(ReviewRound2.id.desc()).first()
    r3 = db.query(ReviewRound3).filter(ReviewRound3.team_id == team_id).order_by(ReviewRound3.id.desc()).first()

    r1_score = r1.total_score if (r1 and r1.status == "COMPLETED") else 0
    r2_score = r2.total_score if (r2 and r2.status == "COMPLETED") else 0
    r3_score = r3.total_score if (r3 and r3.status == "COMPLETED") else 0
    grand_total = r1_score + r2_score + r3_score
    percentage = round((grand_total / 200.0) * 100, 2)

    ps = project.problem_statement_rel
    ps_code = ps.problem_code if ps else (project.problem_code or "—")
    ps_title = ps.title if ps else (project.project_title or "—")
    d_name = project.domain.name if project.domain else (user.domain.name if user.domain else "AI")
    d_display = {"AI": "AI", "CYBERSECURITY": "Cybersecurity", "OPEN_INNOVATION": "Open Innovation"}.get(d_name, d_name)

    return {
        "team": {
            "id": user.id,
            "team_name": user.team_name or user.name,
            "team_leader": user.team_leader or user.name,
            "username": user.username,
            "email": user.email,
            "college": user.college_name or user.organization or "—",
            "domain": d_name,
            "domain_display": d_display,
        },
        "project": {
            "id": project.id,
            "project_code": project.project_code,
            "project_title": project.project_title or ps_title,
            "problem_code": ps_code,
            "problem_title": ps_title,
            "current_round": project.current_round,
            "status": project.status,
        },
        "scores": {
            "r1": r1_score,
            "r2": r2_score,
            "r3": r3_score,
            "grand_total": grand_total,
            "percentage": percentage,
        },
        "round_1": {
            "id": r1.id if r1 else None,
            "evaluator_name": r1.evaluator_name if r1 else "",
            "score_problem_clarity": r1.score_problem_clarity if r1 else 0,
            "score_solution_quality": r1.score_solution_quality if r1 else 0,
            "score_tech_stack": r1.score_tech_stack if r1 else 0,
            "score_idea_presentation": r1.score_idea_presentation if r1 else 0,
            "score_feasibility": r1.score_feasibility if r1 else 0,
            "score_confidence_qa": r1.score_confidence_qa if r1 else 0,
            "total_score": r1.total_score if r1 else 0,
            "comments": r1.comments if r1 else "",
            "suggestions": r1.suggestions if r1 else "",
            "status": r1.status if r1 else "PENDING",
            "is_locked": r1.is_locked if r1 else False,
            "evaluated_at": r1.evaluated_at.isoformat() if r1 and r1.evaluated_at else None,
        } if r1 else None,
        "round_2": {
            "id": r2.id if r2 else None,
            "evaluator_name": r2.evaluator_name if r2 else "",
            "score_planning_workflow": r2.score_planning_workflow if r2 else 0,
            "score_frontend_progress": r2.score_frontend_progress if r2 else 0,
            "score_backend_progress": r2.score_backend_progress if r2 else 0,
            "score_prototype_progress": r2.score_prototype_progress if r2 else 0,
            "score_technical_quality": r2.score_technical_quality if r2 else 0,
            "score_team_collaboration": r2.score_team_collaboration if r2 else 0,
            "score_milestone_completion": r2.score_milestone_completion if r2 else 0,
            "total_score": r2.total_score if r2 else 0,
            "review_notes": r2.review_notes if r2 else "",
            "improvement_suggestions": r2.improvement_suggestions if r2 else "",
            "status": r2.status if r2 else "PENDING",
            "is_locked": r2.is_locked if r2 else False,
            "evaluated_at": r2.evaluated_at.isoformat() if r2 and r2.evaluated_at else None,
        } if r2 else None,
        "round_3": {
            "id": r3.id if r3 else None,
            "evaluator_name": r3.evaluator_name if r3 else "",
            "score_tech_understanding": r3.score_tech_understanding if r3 else 0,
            "score_problem_solution_fit": r3.score_problem_solution_fit if r3 else 0,
            "score_innovation_creativity": r3.score_innovation_creativity if r3 else 0,
            "score_prototype_functionality": r3.score_prototype_functionality if r3 else 0,
            "score_solution_completeness": r3.score_solution_completeness if r3 else 0,
            "score_teamwork_execution": r3.score_teamwork_execution if r3 else 0,
            "score_qa_handling": r3.score_qa_handling if r3 else 0,
            "total_score": r3.total_score if r3 else 0,
            "final_remarks": r3.final_remarks if r3 else "",
            "strengths": r3.strengths if r3 else "",
            "weaknesses": r3.weaknesses if r3 else "",
            "recommendation": r3.recommendation if r3 else "",
            "status": r3.status if r3 else "PENDING",
            "is_locked": r3.is_locked if r3 else False,
            "evaluated_at": r3.evaluated_at.isoformat() if r3 and r3.evaluated_at else None,
        } if r3 else None,
    }


def get_all_evaluations_summary(
    db: Session,
    search: Optional[str] = None,
    domain: Optional[str] = None,
    round_num: Optional[int] = None,
    status_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return evaluation table entries for all teams in the Reviews Dashboard."""
    users = db.query(User).filter(User.role == UserRole.USER).order_by(User.id.asc()).all()

    # Pre-fetch latest reviews for all teams in memory
    r1_map = {r.team_id: r for r in db.query(ReviewRound1).order_by(ReviewRound1.id.asc()).all()}
    r2_map = {r.team_id: r for r in db.query(ReviewRound2).order_by(ReviewRound2.id.asc()).all()}
    r3_map = {r.team_id: r for r in db.query(ReviewRound3).order_by(ReviewRound3.id.asc()).all()}

    results = []
    domain_map = {"AI": "AI", "CYBERSECURITY": "Cybersecurity", "OPEN_INNOVATION": "Open Innovation"}

    for u in users:
        proj = u.projects[0] if u.projects else None
        d_name = u.domain.name if u.domain else (proj.domain.name if (proj and proj.domain) else "AI")

        r1 = r1_map.get(u.id)
        r2 = r2_map.get(u.id)
        r3 = r3_map.get(u.id)

        r1_score = r1.total_score if (r1 and r1.status == "COMPLETED") else 0
        r2_score = r2.total_score if (r2 and r2.status == "COMPLETED") else 0
        r3_score = r3.total_score if (r3 and r3.status == "COMPLETED") else 0
        grand_total = r1_score + r2_score + r3_score
        pct = round((grand_total / 200.0) * 100, 1)

        cur_round = proj.current_round if proj else 1

        # Determine review status
        if r3 and r3.status == "COMPLETED":
            eval_status = "COMPLETED"
        elif r2 and r2.status == "COMPLETED":
            eval_status = "ROUND_2_DONE"
        elif r1 and r1.status == "COMPLETED":
            eval_status = "ROUND_1_DONE"
        elif (r1 and r1.status == "DRAFT") or (r2 and r2.status == "DRAFT") or (r3 and r3.status == "DRAFT"):
            eval_status = "DRAFT"
        else:
            eval_status = "PENDING"

        # Apply filtering in memory
        if domain:
            d_filter = domain.strip().upper()
            if d_name.upper() != d_filter:
                continue

        if round_num is not None:
            if cur_round != round_num:
                continue

        if status_filter:
            sf = status_filter.strip().upper()
            if sf == "COMPLETED" and eval_status != "COMPLETED":
                continue
            if sf == "PENDING" and eval_status == "COMPLETED":
                continue

        if search:
            q = search.strip().lower()
            name_match = (u.team_name or "").lower()
            leader_match = (u.team_leader or "").lower()
            id_match = str(u.id)
            code_match = (proj.project_code if proj else "").lower()
            if q not in name_match and q not in leader_match and q not in id_match and q not in code_match:
                continue

        results.append({
            "team_id": u.id,
            "team_name": u.team_name or u.name,
            "team_leader": u.team_leader or u.name,
            "domain": d_name,
            "domain_display": domain_map.get(d_name, d_name),
            "project_id": proj.id if proj else None,
            "project_code": proj.project_code if proj else "—",
            "project_title": proj.project_title if proj else "—",
            "current_round": cur_round,
            "r1_score": r1_score,
            "r2_score": r2_score,
            "r3_score": r3_score,
            "grand_total": grand_total,
            "percentage": pct,
            "r1_status": r1.status if r1 else "PENDING",
            "r2_status": r2.status if r2 else "PENDING",
            "r3_status": r3.status if r3 else "PENDING",
            "evaluation_status": eval_status,
        })

    return results


def get_live_leaderboard(
    db: Session,
    domain: Optional[str] = None,
    round_num: Optional[int] = None,
    sort_by: Optional[str] = "total",
    limit: Optional[int] = None,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate live leaderboard rankings and return House Cup winners and full table."""
    entries = get_all_evaluations_summary(db=db, search=search, domain=domain, round_num=round_num)

    # Pre-fetch detailed R2 & R3 criteria for specific sorting criteria
    r2_map = {r.team_id: r for r in db.query(ReviewRound2).filter(ReviewRound2.status == "COMPLETED").all()}
    r3_map = {r.team_id: r for r in db.query(ReviewRound3).filter(ReviewRound3.status == "COMPLETED").all()}

    sort_key = (sort_by or "total").lower()

    if sort_key in ("r3", "highest_review_3"):
        entries.sort(key=lambda x: (x["r3_score"], x["grand_total"]), reverse=True)
    elif sort_key in ("innovation", "highest_innovation"):
        entries.sort(
            key=lambda x: (r3_map.get(x["team_id"]).score_innovation_creativity if r3_map.get(x["team_id"]) else 0, x["grand_total"]),
            reverse=True,
        )
    elif sort_key in ("backend", "highest_backend"):
        entries.sort(
            key=lambda x: (r2_map.get(x["team_id"]).score_backend_progress if r2_map.get(x["team_id"]) else 0, x["grand_total"]),
            reverse=True,
        )
    elif sort_key == "ai":
        entries = [e for e in entries if e["domain"] == "AI"]
        entries.sort(key=lambda x: (x["grand_total"], x["r3_score"]), reverse=True)
    elif sort_key in ("cybersecurity", "cyber"):
        entries = [e for e in entries if e["domain"] == "CYBERSECURITY"]
        entries.sort(key=lambda x: (x["grand_total"], x["r3_score"]), reverse=True)
    else:
        # Default: highest grand total
        entries.sort(key=lambda x: (x["grand_total"], x["r3_score"], x["r2_score"]), reverse=True)

    # Assign ranks
    for idx, e in enumerate(entries, start=1):
        e["rank"] = idx

    total_count = len(entries)

    if limit and limit > 0:
        paged_entries = entries[:limit]
    else:
        paged_entries = entries

    # Top 3 House Cup Winners
    podium = {
        "gold": entries[0] if len(entries) > 0 and entries[0]["grand_total"] > 0 else None,
        "silver": entries[1] if len(entries) > 1 and entries[1]["grand_total"] > 0 else None,
        "bronze": entries[2] if len(entries) > 2 and entries[2]["grand_total"] > 0 else None,
    }

    return {
        "success": True,
        "total": total_count,
        "podium": podium,
        "leaderboard": paged_entries,
    }


def export_leaderboard_csv(db: Session) -> str:
    """Generate RFC-compliant CSV of live leaderboard with UTF-8 BOM."""
    res = get_live_leaderboard(db)
    rows = res["leaderboard"]

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Rank",
        "Team ID",
        "Team Name",
        "Domain",
        "Review 1 (Max 60)",
        "Review 2 (Max 70)",
        "Review 3 (Max 70)",
        "Grand Total (Max 200)",
        "Percentage (%)",
        "Status",
    ])

    for r in rows:
        writer.writerow([
            r["rank"],
            r["team_id"],
            r["team_name"],
            r["domain_display"],
            r["r1_score"],
            r["r2_score"],
            r["r3_score"],
            r["grand_total"],
            f"{r['percentage']}%",
            r["evaluation_status"],
        ])

    return "\ufeff" + output.getvalue()


def export_evaluations_csv(db: Session) -> str:
    """Generate comprehensive evaluation sheets CSV including criterion scores, comments, suggestions."""
    users = db.query(User).filter(User.role == UserRole.USER).order_by(User.id.asc()).all()

    r1_map = {r.team_id: r for r in db.query(ReviewRound1).all()}
    r2_map = {r.team_id: r for r in db.query(ReviewRound2).all()}
    r3_map = {r.team_id: r for r in db.query(ReviewRound3).all()}

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Team ID",
        "Team Name",
        "Team Leader",
        "Domain",
        "Project Code",
        # Round 1
        "R1 Problem Clarity (1-10)",
        "R1 Proposed Solution (1-10)",
        "R1 Tech Stack (1-10)",
        "R1 Idea Presentation (1-10)",
        "R1 Feasibility (1-10)",
        "R1 Team Confidence & QA (1-10)",
        "R1 Total (60)",
        "R1 Evaluator",
        "R1 Comments",
        "R1 Suggestions",
        # Round 2
        "R2 Planning & Workflow (1-10)",
        "R2 Frontend Progress (1-10)",
        "R2 Backend Progress (1-10)",
        "R2 Prototype Progress (1-10)",
        "R2 Technical Quality (1-10)",
        "R2 Collaboration (1-10)",
        "R2 Milestone Completion (1-10)",
        "R2 Total (70)",
        "R2 Evaluator",
        "R2 Notes",
        "R2 Suggestions",
        # Round 3
        "R3 Tech Understanding (1-10)",
        "R3 Problem Solution Fit (1-10)",
        "R3 Innovation & Creativity (1-10)",
        "R3 Prototype Functionality (1-10)",
        "R3 Solution Completeness (1-10)",
        "R3 Teamwork & Execution (1-10)",
        "R3 QA Handling (1-10)",
        "R3 Total (70)",
        "R3 Evaluator",
        "R3 Remarks",
        "R3 Strengths",
        "R3 Weaknesses",
        "R3 Recommendation",
        # Grand Total
        "Grand Total (200)",
        "Percentage (%)",
    ])

    for u in users:
        proj = u.projects[0] if u.projects else None
        d_name = u.domain.name if u.domain else "AI"
        r1 = r1_map.get(u.id)
        r2 = r2_map.get(u.id)
        r3 = r3_map.get(u.id)

        r1_tot = r1.total_score if (r1 and r1.status == "COMPLETED") else 0
        r2_tot = r2.total_score if (r2 and r2.status == "COMPLETED") else 0
        r3_tot = r3.total_score if (r3 and r3.status == "COMPLETED") else 0
        grand = r1_tot + r2_tot + r3_tot
        pct = round((grand / 200.0) * 100, 1)

        writer.writerow([
            u.id,
            u.team_name or u.name,
            u.team_leader or u.name,
            d_name,
            proj.project_code if proj else "—",
            # R1
            r1.score_problem_clarity if r1 else 0,
            r1.score_solution_quality if r1 else 0,
            r1.score_tech_stack if r1 else 0,
            r1.score_idea_presentation if r1 else 0,
            r1.score_feasibility if r1 else 0,
            r1.score_confidence_qa if r1 else 0,
            r1_tot,
            r1.evaluator_name if r1 else "—",
            r1.comments if r1 else "",
            r1.suggestions if r1 else "",
            # R2
            r2.score_planning_workflow if r2 else 0,
            r2.score_frontend_progress if r2 else 0,
            r2.score_backend_progress if r2 else 0,
            r2.score_prototype_progress if r2 else 0,
            r2.score_technical_quality if r2 else 0,
            r2.score_team_collaboration if r2 else 0,
            r2.score_milestone_completion if r2 else 0,
            r2_tot,
            r2.evaluator_name if r2 else "—",
            r2.review_notes if r2 else "",
            r2.improvement_suggestions if r2 else "",
            # R3
            r3.score_tech_understanding if r3 else 0,
            r3.score_problem_solution_fit if r3 else 0,
            r3.score_innovation_creativity if r3 else 0,
            r3.score_prototype_functionality if r3 else 0,
            r3.score_solution_completeness if r3 else 0,
            r3.score_teamwork_execution if r3 else 0,
            r3.score_qa_handling if r3 else 0,
            r3_tot,
            r3.evaluator_name if r3 else "—",
            r3.final_remarks if r3 else "",
            r3.strengths if r3 else "",
            r3.weaknesses if r3 else "",
            r3.recommendation if r3 else "",
            # Grand
            grand,
            f"{pct}%",
        ])

    return "\ufeff" + output.getvalue()
