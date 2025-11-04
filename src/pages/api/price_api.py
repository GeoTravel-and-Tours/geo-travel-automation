# src/pages/api/price_api.py


from ...core.base_api import BaseAPI

class PriceAPI(BaseAPI):
    def apply_voucher(self, voucher_data):
        """POST /api/price/voucher/apply"""
        return self.post("/api/price/voucher/apply", json=voucher_data)
    
    def get_voucher(self, code):
        """GET /api/price/voucher/{code}"""
        return self.get(f"/api/price/voucher/{code}")