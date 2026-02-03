import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv

load_dotenv()

AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")

def get_amadeus_client():
    if not AMADEUS_API_KEY or not AMADEUS_API_SECRET:
        return None
    return Client(client_id=AMADEUS_API_KEY, client_secret=AMADEUS_API_SECRET)

def search_flights(origin: str, destination: str, departure_date: str) -> str:
    """
    Search for flights between two cities on a specific date.
    
    Args:
        origin: IATA code of the origin city (e.g., NYC).
        destination: IATA code of the destination city (e.g., LON).
        departure_date: Date of departure in YYYY-MM-DD format.
    """
    amadeus = get_amadeus_client()
    if not amadeus:
        return "Error: Amadeus API credentials not found."

    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=1,
            max=3
        )
        
        offers = response.data
        if not offers:
            return "No flights found."
            
        results = []
        for offer in offers:
            price = offer['price']['total']
            currency = offer['price']['currency']
            itineraries = offer['itineraries'][0]['segments']
            flight_info = " -> ".join([f"{s['carrierCode']}{s['number']}" for s in itineraries])
            results.append(f"Flight: {flight_info}, Price: {price} {currency}")
            
        return "\n".join(results)
        
    except ResponseError as error:
        return f"Error searching flights: {error}"

def search_hotels(city_code: str) -> str:
    """
    Search for hotels in a specific city.
    
    Args:
        city_code: IATA code of the city (e.g., LON).
    """
    amadeus = get_amadeus_client()
    if not amadeus:
        return "Error: Amadeus API credentials not found."

    try:
        # First get hotel ids for the city
        response = amadeus.reference_data.locations.hotels.by_city.get(cityCode=city_code)
        hotels = response.data[:5] # Limit to 5
        
        if not hotels:
            return f"No hotels found in {city_code}."
            
        results = []
        for hotel in hotels:
            name = hotel.get('name', 'Unknown')
            hotel_id = hotel.get('hotelId', 'Unknown')
            results.append(f"Hotel: {name} (ID: {hotel_id})")
            
        return "\n".join(results)
        
    except ResponseError as error:
        return f"Error searching hotels: {error}"
