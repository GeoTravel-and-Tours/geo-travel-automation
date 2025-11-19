# src/utils/__init__.py

"""
Utils package for Geo Travel automation
"""
# ✅ Safe imports (no Selenium dependencies)
from .cleanup import CleanupManager
from .logger import GeoLogger, log_info, log_error, log_step
from .reporting import ReportUtils
from .notifications import slack_notifier, email_notifier
from .reporting import smoke_reporting

# ✅ Lazy imports for Selenium-dependent modules
def __getattr__(name):
    if name == "ElementActions":
        from .element_actions import ElementActions
        return ElementActions
    elif name == "ScreenshotUtils":
        from .screenshot import ScreenshotUtils
        return ScreenshotUtils
    elif name == "WaitStrategy":
        from .wait_strategy import WaitStrategy
        return WaitStrategy
    elif name == "NavigationUtils":
        from .navigation import NavigationUtils
        return NavigationUtils
    elif name == "JavaScriptUtils":
        from .javascript import JavaScriptUtils
        return JavaScriptUtils
    elif name == "ValidationUtils":
        from .validation import ValidationUtils
        return ValidationUtils
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ElementActions",
    "WaitStrategy",
    "NavigationUtils",
    "JavaScriptUtils",
    "ValidationUtils",
    "CleanupManager",
    "GeoLogger",
    "log_info",
    "log_error",
    "log_step",
    "ScreenshotUtils",
    "ReportUtils",
    "slack_notifier",
    "email_notifier",
    "smoke_reporting",
]