"""Core package for the Geo-Automation Framework.

Re-exports the framework's foundational UI building blocks so callers
can do e.g. ``from src.core import BasePage`` instead of reaching into
individual submodules:

- ``BasePage``: superclass for all Selenium UI page objects, see
  ``src/core/base_page.py``.
- ``DriverFactory`` / ``driver_factory``: creates and tracks Selenium
  WebDriver instances for the configured browser, see
  ``src/core/driver_factory.py``.

Note: this package intentionally does not re-export ``BaseAPI``,
``PartnersBaseAPI``, or ``TestBase`` - callers that need those import
them directly from ``src.core.base_api``, ``src.core.partners_base_api``,
and ``src.core.test_base`` respectively.
"""
from .base_page import BasePage
from .driver_factory import DriverFactory, driver_factory

__all__ = ["BasePage", "DriverFactory", "driver_factory"]
