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

# Common currency test cases
CURRENCIES = ["USD", "NGN", "EUR", "GBP", "JPY", "CAD", "AUD"]

# Test cities with their codes
TEST_CITIES = [
    {"name": "Abuja", "code": "ABV", "country": "NG"},
    {"name": "New York", "code": "NYC", "country": "US"},
    {"name": "London", "code": "LON", "country": "GB"},
    {"name": "Dubai", "code": "DXB", "country": "AE"},
]

def generate_hotel_name():
    return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"

def generate_hotel_test_data(hotel_id=None):
    """Generate dynamic test data for hotel tests"""
    # Always use future dates
    check_in = datetime.now() + timedelta(days=10)  # 10 days from now
    check_out = check_in + timedelta(days=3)        # 3 days later
    
    current_date = check_in.strftime("%Y-%m-%d")
    future_date = check_out.strftime("%Y-%m-%d")
    
    # For invalid date tests
    past_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    next_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    next_month_plus_10 = (datetime.now() + timedelta(days=40)).strftime("%Y-%m-%d")
    
    # Pick a random test city
    test_city = random.choice(TEST_CITIES)
    
    return {
        # Basic search payload
        "hotel_search_payload": {
            "hotelName": "Any",
            "cityCode": test_city["code"],
            "countryOfResidence": "NG",
            "destination": {
                "country": test_city["country"],
                "city": test_city["name"]
            },
            "adults": random.randint(1, 4),
            "checkInDate": current_date,
            "checkOutDate": future_date,
            "roomQuantity": 1
        },
        
        # Search with price range
        "hotel_search_payload_with_price": {
            "hotelName": "Any",
            "cityCode": test_city["code"],
            "countryOfResidence": "US",
            "destination": {
                "country": test_city["country"],
                "city": test_city["name"]
            },
            "adults": random.randint(1, 4),
            "checkInDate": current_date,
            "checkOutDate": future_date,
            "roomQuantity": 1,
            "priceRange": "200-300",
            "currency": "USD"
        },
        
        # Hotel offers payload (for details endpoint)
        "hotel_offers_payload": {
            "hotelId": "SINYC713",  # Will be replaced with actual hotelId
            "adults": 2,
            "checkInDate": next_month,
            "checkOutDate": next_month_plus_10,
            "countryOfResidence": "US",
            "roomQuantity": 1,
            "childAges": [5, 10],
            "currency": "NGN"  # Different from response currency to trigger conversion
        },
        
        # Hotel offers with same currency (should NOT show conversion fields)
        "hotel_offers_same_currency_payload": {
            "hotelId": "SINYC713",  # Will be replaced
            "adults": 2,
            "checkInDate": next_month,
            "checkOutDate": next_month_plus_10,
            "countryOfResidence": "US",
            "roomQuantity": 1,
            "childAges": [5, 10],
            "currency": "USD"  # Same as response currency
        },
        
        # Booking payload
        "hotel_booking_payload": {
            "firstName": "Bot",
            "lastName": "GEO",
            "email": "geo.qa.bot@gmail.com",
            "phone": "07080702920",
            "adults": random.randint(1, 4),
            "checkInDate": current_date,
            "checkOutDate": future_date,
            "roomQuantity": 1,
            "hotelName": generate_hotel_name(),
            "hotelId": hotel_id,  # Will be populated from search results
            "destination": {
                "country": "Nigeria",
                "city": "Aba"
            },
            "dob": "1990-01-01",
            "gender": "Male",
            "alternativePhone": "07080702921",
            "nationality": "Nigerian",
            "otherGuests": []
        },
        
        # Invalid test cases
        "invalid_date_cases": [
            {"name": "Check-out before check-in", 
             "checkInDate": "2026-01-19", "checkOutDate": "2026-01-10"},
            {"name": "Same day check-in/out", 
             "checkInDate": "2026-01-10", "checkOutDate": "2026-01-10"},
            {"name": "Past check-in date", 
             "checkInDate": "2020-01-01", "checkOutDate": "2026-01-10"},
            {"name": "Invalid date format", 
             "checkInDate": "01-01-2026", "checkOutDate": "10-01-2026"},
            {"name": "Too far in future", 
             "checkInDate": "2030-01-01", "checkOutDate": "2030-01-10"},
        ],
        
        "invalid_currencies": ["INVALID", "123", "US", ""],
        "test_cities": TEST_CITIES,
        "test_currencies": CURRENCIES
    }

def generate_blog_comment_data():
    """Generate dynamic test data for blog comments"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return {
        "name": f"QA Bot {timestamp}",
        "email": f"geo.qa.bot.{timestamp}@geotravel.com",
        "message": f"Test comment from automation - {timestamp}"
    }

def get_blog_test_data():
    """Centralized blog test data"""
    return {
        "comment": generate_blog_comment_data(),
        "success_message": "Your comment were successfully added",
        "max_comment_length": 500,
        "invalid_email": "invalid-email",
        "empty_name_message": "Name is required",
        "empty_email_message": "Email is required",
        "empty_comment_message": "Message is required"
    }