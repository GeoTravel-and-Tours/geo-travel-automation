# src/utils/logger.py

import logging
import os
import glob
from datetime import datetime
from pathlib import Path
import threading
from logging.handlers import RotatingFileHandler
from src.utils.cleanup import CleanupManager


class GeoLogger:
    """
    Enhanced logging utility for Geo Travel automation with automated file management
    """

    # Class-level configuration
    LOG_RETENTION_DAYS = 30
    MAX_LOG_SIZE_MB = 10
    MAX_BACKUP_COUNT = 10
    LOGS_DIR = Path("logs")

    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        name=None,
        log_level=logging.INFO,
        log_to_file=True,
        enable_cleanup=True,
        unique_file_per_run=True,
        auto_cleanup_frequency_days=7,
    ):  # ← New parameter
        with self._lock:
            if not GeoLogger._initialized:
                self.name = name or "GeoTravelAutomation"
                self.log_level = log_level
                self.log_to_file = log_to_file
                self.enable_cleanup = enable_cleanup
                self.unique_file_per_run = unique_file_per_run
                self.auto_cleanup_frequency_days = auto_cleanup_frequency_days
                self.current_log_file = None

                # One-time setup
                self._ensure_logs_directory()
                self._setup_logger()

                # Automatic cleanup on startup
                if enable_cleanup:
                    self._cleanup_old_logs()
                    # Optional: Start background cleaner
                    # self._start_background_cleaner()

                GeoLogger._initialized = True

    def _cleanup_old_logs(self):
        """Use centralized cleanup for logs"""
        if not self._should_run_cleanup():
            return

        try:
            manager = CleanupManager(retention_days=self.LOG_RETENTION_DAYS)
            deleted_count = manager._cleanup_directory(
                self.LOGS_DIR,
                ["*.log", "*.html", "*.txt"],
                dry_run=False
            )
            
            if deleted_count > 0:
                self.info(f"Log cleanup completed: {deleted_count} files removed")
            
            self._update_last_cleanup_time()

        except Exception as e:
            self.error(f"Log cleanup error: {e}")

    def _should_run_cleanup(self):
        """Check if cleanup should run based on frequency"""
        last_cleanup_file = self.LOGS_DIR / ".last_cleanup"

        if not last_cleanup_file.exists():
            return True

        last_cleanup_time = datetime.fromtimestamp(last_cleanup_file.stat().st_mtime)
        days_since_last_cleanup = (datetime.now() - last_cleanup_time).days

        return days_since_last_cleanup >= self.auto_cleanup_frequency_days

    def _is_file_old(self, file_path):
        """Check if file is older than retention period"""
        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        file_age = datetime.now() - file_time
        return file_age.days > self.LOG_RETENTION_DAYS

    def _update_last_cleanup_time(self):
        """Update the last cleanup timestamp"""
        last_cleanup_file = self.LOGS_DIR / ".last_cleanup"
        last_cleanup_file.touch()

    # Manual cleanup method for explicit control
    def force_cleanup(self):
        """Force immediate cleanup regardless of frequency settings"""
        self.info("🔧 Forcing immediate log cleanup...")
        self._cleanup_old_logs()

    def _ensure_logs_directory(self):
        """Ensure logs directory exists"""
        self.LOGS_DIR.mkdir(exist_ok=True)

    def _generate_log_filename(self):
        """Generate unique timestamped log filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.unique_file_per_run:
            return f"geo_travel_{timestamp}.log"
        else:
            return f"geo_travel_{datetime.now().strftime('%Y%m%d')}.log"

    def _get_current_log_files(self):
        """Get all current log files in logs directory"""
        log_pattern = str(self.LOGS_DIR / "geo_travel_*.log")
        return glob.glob(log_pattern)

    def _log_to_console(self, message):
        """Utility method to log to console before logger is fully setup"""
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - LoggerSetup - INFO - {message}"
        )

    def _setup_file_handler(self, formatter):
        """Setup file handler with enhanced rotation and compression support"""
        try:
            log_filename = self._generate_log_filename()
            log_file_path = self.LOGS_DIR / log_filename
            self.current_log_file = log_file_path

            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=self.MAX_LOG_SIZE_MB * 1024 * 1024,
                backupCount=self.MAX_BACKUP_COUNT,
                encoding="utf-8",
                delay=True,
            )

            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)

            # Check compression support
            try:
                import gzip

                self._log_to_console("Compression support available for log files")
            except ImportError:
                pass

            return file_handler

        except Exception as e:
            self._log_to_console(f"File handler setup error: {e}")
            return None

    def _setup_logger(self):
        """Configure logger with enhanced handlers and formatters - RUNS ONLY ONCE"""
        # Get or create logger (don't overwrite if exists)
        if not hasattr(self, "logger") or self.logger is None:
            self.logger = logging.getLogger(self.name)

        # Check if already configured by our system
        if (
            hasattr(self.logger, "_GeoLogger_configured")
            and self.logger._GeoLogger_configured
        ):
            return self.logger

        # Set level and clear existing handlers
        self.logger.setLevel(self.log_level)
        self.logger.handlers = []

        # Create enhanced formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler (always active)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler (optional)
        if self.log_to_file:
            file_handler = self._setup_file_handler(formatter)
            if file_handler:
                self.logger.addHandler(file_handler)
                self._log_to_console(f"Log file created: {self.current_log_file}")

        # Prevent propagation to root logger
        self.logger.propagate = False

        # Mark this logger as configured by our class
        self.logger._GeoLogger_configured = True

        return self.logger

    def get_log_statistics(self):
        """Get statistics about log files"""
        try:
            log_files = self._get_current_log_files()
            total_size = sum(Path(f).stat().st_size for f in log_files)

            stats = {
                "total_files": len(log_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "current_log_file": (
                    str(self.current_log_file) if self.current_log_file else None
                ),
                "retention_days": self.LOG_RETENTION_DAYS,
                "logs_directory": str(self.LOGS_DIR),
            }

            return stats

        except Exception as e:
            return {"error": str(e)}

    def archive_current_log(self, archive_name=None):
        """Archive the current log file"""
        try:
            if not self.current_log_file or not self.current_log_file.exists():
                return False

            if not archive_name:
                archive_name = f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            archive_path = self.LOGS_DIR / "archives" / archive_name
            archive_path.parent.mkdir(parents=True, exist_ok=True)

            import shutil

            shutil.copy2(self.current_log_file, archive_path)

            self.info(f"Log archived to: {archive_path}")
            return True

        except Exception as e:
            self.error(f"Log archiving failed: {e}")
            return False

    def start_periodic_cleanup(self, interval_hours=24):
        """Start background thread for periodic log cleanup"""

        def cleanup_worker():
            while True:
                try:
                    self._cleanup_old_logs()
                    threading.Event().wait(interval_hours * 3600)
                except Exception as e:
                    self.error(f"Periodic cleanup error: {e}")

        if self.enable_cleanup:
            cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
            cleanup_thread.start()
            self.info(f"Periodic log cleanup started (interval: {interval_hours}h)")

    # Enhanced logging methods
    def info(self, message, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)

    def debug_handlers(self):
        """Debug method to see all attached handlers"""
        if self.logger:
            print(f"Logger '{self.name}' has {len(self.logger.handlers)} handlers:")
            for i, handler in enumerate(self.logger.handlers):
                print(
                    f"  {i+1}. {type(handler).__name__}: {getattr(handler, 'baseFilename', 'No filename')}"
                )

    def warning(self, message, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self.logger.critical(message, *args, **kwargs)

    def success(self, message):
        self.info(f"SUCCESS: {message}")

    def failure(self, message):
        self.error(f"FAILURE: {message}")

    # Test-specific logging methods
    def step(self, step_number, step_description):
        self.info(f"🔄 STEP {step_number}: {step_description}")

    def test_start(self, test_name):
        self.info("🚀" + "=" * 58 + "🚀")
        self.info(f"🧪 STARTING TEST: {test_name}")
        self.info("🚀" + "=" * 58 + "🚀")

    def test_end(self, test_name, status="COMPLETED", duration=None):
        status_icon = (
            "✅"
            if status.upper() == "PASSED"
            else "❌" if status.upper() == "FAILED" else "🔚"
        )
        duration_text = f" - Duration: {duration:.2f}s" if duration else ""

        self.info(status_icon + "=" * 58 + status_icon)
        self.info(f"{status_icon} TEST {status}: {test_name}{duration_text}")
        self.info(status_icon + "=" * 58 + status_icon)

    def element_action(self, action, locator, additional_info=""):
        action_icons = {
            "click": "🖱️",
            "type": "⌨️",
            "find": "🔍",
            "wait": "⏳",
            "verify": "✅",
        }

        icon = action_icons.get(action.lower(), "📝")
        locator_str = f"{locator[0]}: {locator[1]}"
        message = f"{icon} {action.upper()} - Element: {locator_str}"

        if additional_info:
            message += f" - {additional_info}"

        self.info(message)

    def screenshot_captured(self, screenshot_path):
        self.info(f"📸 Screenshot captured: {screenshot_path}")

    def performance_metric(self, metric_name, value, unit="ms"):
        self.info(f"📊 PERFORMANCE - {metric_name}: {value} {unit}")

    def get_log_file_path(self):
        return str(self.current_log_file) if self.current_log_file else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.error(f"Context error: {exc_val}")
        return False


# Global singleton instance
logger = GeoLogger(
    name="GeoTravelGlobalLogger",
    log_level=logging.INFO,
    log_to_file=True,
    enable_cleanup=True,
    unique_file_per_run=True,
)


# Convenience functions
def log_info(message):
    logger.info(message)


def log_error(message):
    logger.error(message)


def log_success(message):
    logger.success(message)


def log_step(step_number, description):
    logger.step(step_number, description)


def log_performance(metric_name, value, unit="ms"):
    logger.performance_metric(metric_name, value, unit)


def check_log_system_health():
    """Check the health and status of the logging system"""
    stats = logger.get_log_statistics()

    print("\n" + "=" * 60)
    print("📋 LOG SYSTEM HEALTH CHECK")
    print("=" * 60)

    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")

    print("=" * 60)

    return stats


# Example usage and self-test
if __name__ == "__main__":
    print("Testing Enhanced Logger...")

    # Display system health
    check_log_system_health()

    # Test various log levels
    logger.test_start("LoggerSelfTest")
    logger.step(1, "Testing basic logging")
    logger.info("This is an info message")
    logger.debug("This is a debug message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.success("This is a success message")

    logger.step(2, "Testing element actions")
    logger.element_action("click", ("id", "search-button"), "Search initiated")
    logger.element_action("type", ("name", "username"), "Entered: testuser")

    logger.step(3, "Testing performance metrics")
    logger.performance_metric("PageLoad", 2450, "ms")
    logger.performance_metric("SearchQuery", 120, "ms")

    logger.screenshot_captured("/reports/screenshots/test_evidence.png")

    logger.test_end("LoggerSelfTest", "PASSED", duration=2.5)

    print(f"\nCurrent log file: {logger.get_log_file_path()}")
    print("Logger test completed successfully!")
