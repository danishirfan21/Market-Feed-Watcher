from sqlalchemy.orm import Session

from app.models import CrawlRun

def get_source_health(db: Session, source: str):
    runs = (
        db.query(CrawlRun)
        .filter(CrawlRun.source == source)
        .order_by(CrawlRun.started_at.desc())
        .limit(20)
        .all()
    )

    if not runs:
        return {
            "source": source,
            "status": "unknown",
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "success_rate": 0,
            "last_run_status": None,
            "last_error": None,
            "total_changes_detected": 0,
            "average_listings_found": 0,
        }

    total_runs = len(runs)
    successful_runs = len([run for run in runs if run.status == "success"])
    failed_runs = len([run for run in runs if run.status == "failed"])

    total_changes_detected = sum(run.changes_detected for run in runs)
    average_listings_found = round(
        sum(run.listings_found for run in runs) / total_runs,
        2,
    )

    last_run = runs[0]

    return {
        "source": source,
        "status": "healthy" if failed_runs == 0 else "degraded",
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "success_rate": round((successful_runs / total_runs) * 100, 2),
        "last_run_status": last_run.status,
        "last_error": last_run.error_message,
        "total_changes_detected": total_changes_detected,
        "average_listings_found": average_listings_found,
    }