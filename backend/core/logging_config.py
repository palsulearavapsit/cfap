import logging
import json

class StructuredJSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Capture additional properties if available
        if hasattr(record, "extra_context") and isinstance(record.extra_context, dict):
            log_data.update(record.extra_context)
            
        # Scrub sensitive variables to protect PII and credentials
        sensitive_keys = ["password", "password_hash", "access_token", "refresh_token", "secret"]
        for key in sensitive_keys:
            if key in log_data:
                log_data[key] = "[MASKED]"
            if isinstance(log_data["message"], str) and key in log_data["message"].lower():
                log_data["message"] = f"[Scrubbed message containing sensitive {key}]"
                
        return json.dumps(log_data)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = StructuredJSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    logging.info("Structured JSON logging framework initialized.")
