# src/tests/test_data.py

from datetime import datetime, timedelta
import random

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


ADJECTIVES = ["Grand", "Royal", "Golden", "Silver", "Urban", "Ocean", "Emerald", "Crystal"]
NOUNS = ["Palace", "Suites", "Inn", "Resort", "Lodge", "Heights", "Stay", "Haven"]

def generate_hotel_name():
    return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"

def generate_hotel_test_data():
    """Generate dynamic test data for hotel tests"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    future_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    
    return {
        "hotel_search_payload": {
            "hotelName": "Any",
            "cityCode": "NYC",
            "countryOfResidence": "US",
            "destination": {
                "country": "US",
                "city": "New York"
            },
            "adults": 2,
            "checkInDate": current_date,
            "checkOutDate": future_date,
            "roomQuantity": 1
        },
        "hotel_search_payload_with_price": {
            "hotelName": "Any",
            "cityCode": "NYC",
            "countryOfResidence": "US",
            "destination": {
                "country": "US",
                "city": "New York"
            },
            "adults": 2,
            "checkInDate": current_date,
            "checkOutDate": future_date,
            "roomQuantity": 1,
            "priceRange": "200-300",
            "currency": "USD"
        },
        "hotel_booking_payload": {
            "firstName": "Bot",
            "lastName": "GEO",
            "email": "geo.qa.bot@gmail.com",
            "phone": "7079090909",
            "adults": 2,
            "checkInDate": current_date,
            "checkOutDate": future_date,
            "roomQuantity": 1,
            "hotelName": generate_hotel_name(),
            "destination": {
                "country": "Nigeria",
                "city": "Aba"
            }
        }
    }