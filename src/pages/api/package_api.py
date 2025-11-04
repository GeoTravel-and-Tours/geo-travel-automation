# src/pages/api/package_api.py

from ...core.base_api import BaseAPI

class PackageAPI(BaseAPI):
    
    # Package Management
    def get_all_packages(self, **params):
        """GET /api/package/all"""
        return self.get("/api/package/all", params=params)
    
    def get_package_countries(self):
        """GET /api/package/countries"""
        return self.get("/api/package/countries")
    
    def get_single_package(self, package_id):
        """GET /api/package/{id}"""
        return self.get(f"/api/package/{package_id}")
    
    # Package Booking
    def book_package(self, booking_data):
        """POST /api/package/book"""
        return self.post("/api/package/book", json=booking_data)
    
    def verify_payment(self, invoice_id, transaction_id):
        """GET /api/package/book/verify/{invoiceId}/{transaction_id}"""
        return self.get(f"/api/package/book/verify/{invoice_id}/{transaction_id}")
    
    # Package Deals
    def get_all_deals(self, **params):
        """GET /api/package/deal/all"""
        return self.get("/api/package/deal/all", params=params)
    
    def get_single_deal(self, deal_id):
        """GET /api/package/deal/{id}"""
        return self.get(f"/api/package/deal/{deal_id}")