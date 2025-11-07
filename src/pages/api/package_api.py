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
    
    def verify_payment_link(self, payment_link):
        """Verify payment link is accessible and returns valid response"""
        import requests
        try:
            response = requests.get(payment_link, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                # Check if it's a Flutterwave page
                if 'flutterwave' in response.url or 'checkout' in response.text.lower():
                    return True, "Payment link is valid and points to Flutterwave"
                else:
                    return False, f"Payment link redirected to unexpected URL: {response.url}"
            else:
                return False, f"Payment link returned status code: {response.status_code}"
                
        except Exception as e:
            return False, f"Error accessing payment link: {str(e)}"
    
    # Package Deals
    def get_all_deals(self, **params):
        """GET /api/package/deal/all"""
        return self.get("/api/package/deal/all", params=params)
    
    def get_single_deal(self, deal_id):
        """GET /api/package/deal/{id}"""
        return self.get(f"/api/package/deal/{deal_id}")
    
    def book_package(self, booking_data):
        """POST /api/package/book"""
        return self.post("/api/package/book", json=booking_data)