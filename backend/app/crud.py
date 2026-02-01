from sqlalchemy.orm import Session
from typing import Optional, List
from . import models

def get_bug_report(db: Session, bug_report_id: int) -> Optional[models.BugReport]:
    return db.query(models.BugReport).filter(models.BugReport.id == bug_report_id).first()

def get_bug_reports(db: Session, skip: int = 0, limit: int = 100) -> List[models.BugReport]:
    return db.query(models.BugReport).offset(skip).limit(limit).all()

def create_bug_report(db: Session, description: str) -> models.BugReport:
    db_bug_report = models.BugReport(description=description)
    db.add(db_bug_report)
    db.commit()
    db.refresh(db_bug_report)
    return db_bug_report

def update_bug_report_status(db: Session, bug_report_id: int, status: str) -> Optional[models.BugReport]:
    db_bug_report = db.query(models.BugReport).filter(models.BugReport.id == bug_report_id).first()
    if db_bug_report:
        db_bug_report.status = status
        db.commit()
        db.refresh(db_bug_report)
    return db_bug_report
