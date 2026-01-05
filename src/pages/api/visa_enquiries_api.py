# src/pages/api/visa_enquiries_api.py

from ...core.base_api import BaseAPI
from configs.environment import EnvironmentConfig

class VisaEnquiryAPI(BaseAPI):
    """Visa Enquiry API client"""
    
    def create_visa_enquiry(self, visa_data):
        """POST /api/visa/create - Create a new visa enquiry"""
        return self.post("/api/visa/create", json=visa_data)
    
    def make_payment(self, payment_data):
        """POST /api/visa/payment - Make payment for visa enquiry"""
        return self.post("/api/visa/payment", json=payment_data)
    
    def verify_payment(self, invoice_id, transaction_id):
        """GET /api/visa/verify/{invoiceId}/{transaction_id} - Verify payment"""
        return self.get(f"/api/visa/verify/{invoice_id}/{transaction_id}")
    
    def get_user_visa_applications(self, **params):
        """GET /api/visa/all/user - Get user's own visa applications"""
        return self.get("/api/visa/all/user", params=params)
    
    def get_visa_application_by_id(self, visa_application_id):
        """GET /api/visa - Get specific visa application by ID"""
        params = {"visa_application_id": visa_application_id}
        return self.get("/api/visa", params=params)
    
    def verify_payment_link(self, payment_link):
        """Verify payment link is accessible and returns valid response"""
        import requests
        try:
            response = requests.get(payment_link, timeout=EnvironmentConfig.API_TIMEOUT, allow_redirects=True)

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