# src/core/__init__.py

"""
Core package for Geo Travel automation framework
"""
from .base_page import BasePage
from .driver_factory import DriverFactory, driver_factory

__all__ = ["BasePage", "DriverFactory", "driver_factory"]
