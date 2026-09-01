"""
src/pages/ui/__init__.py

Package marker for the UI page objects of the Geo-Automation Framework.

Every module in this package is a Selenium Page Object Model class for one
user-facing flow of the Geo Travel web app (gowithgeo.com) - e.g. auth,
home, dashboard, packages, flights, payments, contact, blogs, travel
gallery, visa enquiries. Each page object subclasses ``BasePage``
(src/core/base_page.py). This ``__init__.py`` intentionally contains no
code; it only makes ``src/pages/ui`` importable as a package.
"""
