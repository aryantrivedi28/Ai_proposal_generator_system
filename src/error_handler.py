"""Centralized error handling and logging"""

import traceback
from datetime import datetime
from pathlib import Path

class ErrorHandler:
    """Handle and log errors"""
    
    def __init__(self):
        self.error_log = Path("logs/errors.log")
        self.error_log.parent.mkdir(parents=True, exist_ok=True)
    
    def log_error(self, error: Exception, context: dict = None):
        """Log error with context"""
        
        timestamp = datetime.now().isoformat()
        error_type = type(error).__name__
        error_msg = str(error)
        trace = traceback.format_exc()
        
        log_entry = f"""
{'='*60}
Time: {timestamp}
Type: {error_type}
Message: {error_msg}
Context: {context}
Traceback:
{trace}
{'='*60}
"""
        
        with open(self.error_log, 'a') as f:
            f.write(log_entry)
        
        print(f"❌ Error logged: {error_type}")
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent errors"""
        
        if not self.error_log.exists():
            return []
        
        with open(self.error_log, 'r') as f:
            content = f.read()
        
        errors = content.split('='*60)
        return errors[-limit:]

# Global instance
error_handler = ErrorHandler()