from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from .database import Base

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

class BugReport(Base):
    __tablename__ = "bug_reports"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    status = Column(String, default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
