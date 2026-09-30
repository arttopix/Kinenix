import uuid
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text
from .database import Base
from .timeutils import isoformat_utc, utc_now


class Worker(Base):
    __tablename__ = "workers"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    ip_address = Column(String(64), default="127.0.0.1")
    os_info = Column(String(128), default="Linux")
    status = Column(String(32), default="online")  # online, offline, busy
    current_task = Column(String(128), nullable=True)
    cpu_percent = Column(Float, default=0.0)
    ram_usage = Column(String(32), default="0.0 GB")
    last_heartbeat = Column(DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "ip_address": self.ip_address,
            "os_info": self.os_info,
            "status": self.status,
            "current_task": self.current_task,
            "cpu_percent": self.cpu_percent,
            "ram_usage": self.ram_usage,
            "last_heartbeat": isoformat_utc(self.last_heartbeat),
        }


class Execution(Base):
    __tablename__ = "executions"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    worker_id = Column(String(64), default="local-worker", index=True)
    flow_name = Column(String(128), nullable=False, index=True)
    status = Column(String(32), default="success", index=True)  # success, failed, running
    start_time = Column(DateTime, default=utc_now)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    has_error = Column(Boolean, default=False)
    
    # Error details
    failed_step_id = Column(String(64), nullable=True)
    failed_step_name = Column(String(128), nullable=True)
    error_type = Column(String(64), nullable=True)
    exception_class = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)
    screenshot_path = Column(String(256), nullable=True)
    raw_log = Column(Text, nullable=True)

    # Central AI Triage & Summary
    ai_category = Column(String(128), nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_root_cause = Column(Text, nullable=True)
    ai_suggestion = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "worker_id": self.worker_id,
            "flow_name": self.flow_name,
            "status": self.status,
            "start_time": isoformat_utc(self.start_time),
            "end_time": isoformat_utc(self.end_time),
            "duration_seconds": self.duration_seconds,
            "has_error": self.has_error,
            "failed_step_id": self.failed_step_id,
            "failed_step_name": self.failed_step_name,
            "error_type": self.error_type,
            "exception_class": self.exception_class,
            "error_message": self.error_message,
            "screenshot_path": self.screenshot_path,
            "ai_category": self.ai_category,
            "ai_confidence": self.ai_confidence,
            "ai_summary": self.ai_summary,
            "ai_root_cause": self.ai_root_cause,
            "ai_suggestion": self.ai_suggestion,
            "created_at": isoformat_utc(self.created_at),
        }

