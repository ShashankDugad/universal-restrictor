"""
Structured logging for audit trails and compliance.
Logs in JSON format for easy parsing by log aggregators.
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps

# Configure JSON formatter
class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class AuditLogger:
    """
    Audit logger for compliance tracking.
    
    Logs:
    - All API requests (sanitized - no raw PII)
    - Detection results
    - Authentication events
    - Rate limit events
    """
    
    def __init__(self, log_file: str = None):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Console handler (JSON in production)
            console_handler = logging.StreamHandler()
            
            if os.getenv("LOG_FORMAT", "text") == "json":
                console_handler.setFormatter(JSONFormatter())
            else:
                console_handler.setFormatter(
                    logging.Formatter("%(asctime)s - AUDIT - %(message)s")
                )
            self.logger.addHandler(console_handler)
            
            # File handler (always JSON)
            if log_file or os.getenv("AUDIT_LOG_FILE"):
                file_path = log_file or os.getenv("AUDIT_LOG_FILE", "data/audit.log")
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file_handler = logging.FileHandler(file_path)
                file_handler.setFormatter(JSONFormatter())
                self.logger.addHandler(file_handler)
    
    def _log(self, event_type: str, data: Dict[str, Any]):
        """Internal log method."""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            "", 0, 
            f"{event_type}: {data.get('summary', '')}",
            None, None
        )
        record.extra_data = {
            "event_type": event_type,
            **data
        }
        self.logger.handle(record)
    
    def log_request(
        self,
        request_id: str,
        tenant_id: str,
        input_hash: str,
        input_length: int,
        action: str,
        categories: list,
        confidence: float,
        processing_time_ms: float,
        client_ip: str = None,
        detectors_used: list = None
    ):
        """Log an API request (sanitized - no raw input)."""
        self._log("api_request", {
            "request_id": request_id,
            "tenant_id": tenant_id,
            "input_hash": input_hash,
            "input_length": input_length,
            "action": action,
            "categories": categories,
            "confidence": confidence,
            "processing_time_ms": round(processing_time_ms, 2),
            "client_ip": self._mask_ip(client_ip) if client_ip else None,
            "detectors_used": detectors_used or [],
            "summary": f"action={action} categories={len(categories)} time={processing_time_ms:.0f}ms"
        })
    
    def log_auth_success(self, tenant_id: str, client_ip: str = None):
        """Log successful authentication."""
        self._log("auth_success", {
            "tenant_id": tenant_id,
            "client_ip": self._mask_ip(client_ip) if client_ip else None,
            "summary": f"tenant={tenant_id}"
        })
    
    def log_auth_failure(self, reason: str, client_ip: str = None):
        """Log failed authentication attempt."""
        self._log("auth_failure", {
            "reason": reason,
            "client_ip": self._mask_ip(client_ip) if client_ip else None,
            "summary": f"reason={reason}"
        })
    
    def log_rate_limit(self, client_id: str, limit: int):
        """Log rate limit event."""
        self._log("rate_limit", {
            "client_id_hash": client_id[:20] + "...",
            "limit": limit,
            "summary": f"limit={limit}/min exceeded"
        })
    
    def log_escalation(
        self,
        request_id: str,
        triggered_patterns: list,
        claude_result: str,
        cost_usd: float
    ):
        """Log Claude API escalation."""
        self._log("escalation", {
            "request_id": request_id,
            "triggered_patterns": triggered_patterns,
            "claude_result": claude_result,
            "cost_usd": round(cost_usd, 6),
            "summary": f"patterns={triggered_patterns} result={claude_result}"
        })
    
    def log_feedback(
        self,
        feedback_id: str,
        request_id: str,
        feedback_type: str,
        tenant_id: str = None
    ):
        """Log feedback submission."""
        self._log("feedback", {
            "feedback_id": feedback_id,
            "request_id": request_id,
            "feedback_type": feedback_type,
            "tenant_id": tenant_id,
            "summary": f"type={feedback_type}"
        })
    
    def log_error(self, error_type: str, message: str, request_id: str = None):
        """Log error event."""
        self._log("error", {
            "error_type": error_type,
            "message": message,
            "request_id": request_id,
            "summary": f"{error_type}: {message[:50]}"
        })
    
    def _mask_ip(self, ip: str) -> str:
        """Mask IP address for privacy (keep first two octets)."""
        if not ip:
            return None
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.*.*"
        return ip[:10] + "..."


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
