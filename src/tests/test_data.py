# src/tests/test_data.py

from datetime import datetime, timedelta

def generate_visa_test_data():
    """Generate dynamic test data for visa tests"""
    future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    return {
        "visa_enquiry_payload": {
            "visaCountry": "Kenya",
            "first_name": "QA Bot",
            "last_name": "GEO",
            "travel_date": future_date,
            "email": "geo.qa.bot@gmail.com",
            "agree": True,
            "phoneNumber": "7080702920",
            "nationality": "Nigeria",
            "passportAvailable": "Yes",
            "message": "I would like to travel for business purposes",
            "type": "Business"
        },
        "payment_payload_flutterwave": {
            "visaId": None,  # Will be populated dynamically
            "paymentMethod": "Flutterwave"
        },
        "payment_payload_bank_transfer": {
            "visaId": None,  # Will be populated dynamically
            "paymentMethod": "Bank Transfer"
        }
    }
    
def get_flight_test_data():
    """Centralized flight test data"""
    return {
        "origin": "LOS",
        "destination": "LHR",
        "cabin": "ECONOMY",
        "flight_type": "one-way",
        "departure_date_offset": 30,  # Days from today
        "adults": 1,
        "children": 0,
        "infants": 0
    }