# src/pages/api/commercial_api.py

from ...core.base_api import BaseAPI

class CommercialAPI(BaseAPI):
    def get_all_deals(self, **params):
        """GET /api/commercial/all"""
        return self.get("/api/commercial/all", params=params)
    
    def get_single_deal(self, deal_id):
        """GET /api/commercial/{id}"""
        return self.get(f"/api/commercial/{deal_id}")
    
    def book_commercial(self, booking_data):
        """POST /api/commercial/book"""
        return self.post("/api/commercial/book", json=booking_data)
    
    def verify_payment(self, invoice_id, transaction_id):
        """GET /api/commercial/book/verify/{invoiceId}/{transaction_id}"""
        return self.get(f"/api/commercial/book/verify/{invoice_id}/{transaction_id}")
    
    def get_all_bookings(self, **params):
        """GET /api/commercial/book/all"""
        return self.get("/api/commercial/book/all", params=params)