import uuid
import googlemaps
from langchain_core.tools import tool
from config.settings import GOOGLE_MAPS_API_KEY

# In-memory reservation store (in production, persist to a database)
_reservations: dict[str, dict] = {}

PRICE_LEVEL = {0: "Free", 1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}


def _gmaps() -> googlemaps.Client:
    return googlemaps.Client(key=GOOGLE_MAPS_API_KEY)


def _geocode(location: str) -> tuple[float, float]:
    result = _gmaps().geocode(location)
    if not result:
        raise ValueError(f"Could not geocode: {location}")
    loc = result[0]["geometry"]["location"]
    return loc["lat"], loc["lng"]


@tool
def search_restaurants(
    location: str,
    cuisine: str = "",
    price_range: str = "",
    limit: int = 8,
) -> str:
    """Search for restaurants using Google Maps Places API.

    Args:
        location: City or address (e.g. "Paris, France", "Shibuya, Tokyo")
        cuisine: Food type keyword (e.g. "french", "sushi", "italian", "local")
        price_range: Price level "1" (cheap) to "4" (expensive)
        limit: Max number of results (max 20)
    """
    try:
        gmaps = _gmaps()
        lat, lng = _geocode(location)

        keyword = cuisine if cuisine else "restaurant"
        resp = gmaps.places_nearby(
            location=(lat, lng),
            radius=3000,
            type="restaurant",
            keyword=keyword,
            rank_by="prominence",
        )

        places = resp.get("results", [])[:limit]
        if not places:
            return "No restaurants found."

        # Filter by price level if specified
        if price_range:
            target_price = int(price_range)
            places = [p for p in places if p.get("price_level", -1) <= target_price] or places

        results = []
        for p in places:
            price = PRICE_LEVEL.get(p.get("price_level", -1), "N/A")
            rating = p.get("rating", "N/A")
            address = p.get("vicinity", "N/A")
            open_now = p.get("opening_hours", {}).get("open_now")
            status = "Open now" if open_now else ("Closed" if open_now is False else "Hours N/A")
            results.append(
                f"**{p['name']}** | Rating: {rating}/5 | Price: {price} | {status}\n"
                f"  Address: {address} | Place ID: {p['place_id']}"
            )

        return "\n".join(results)
    except Exception as e:
        return f"Restaurant search error: {str(e)}"


@tool
def search_workout_areas(
    location: str,
    workout_type: str = "gym",
    limit: int = 6,
) -> str:
    """Search for workout areas including gyms, running parks, and hiking trails
    using Google Maps Places API.

    Args:
        location: City or neighborhood (e.g. "Paris, France")
        workout_type: One of "gym", "park", "hiking", "yoga", "running" or any keyword
        limit: Max number of results
    """
    try:
        gmaps = _gmaps()
        lat, lng = _geocode(location)

        # Map workout type to Google Maps place type
        place_type_map = {
            "gym": "gym",
            "yoga": "gym",
            "park": "park",
            "hiking": "park",
            "running": "park",
        }
        place_type = place_type_map.get(workout_type.lower(), "gym")
        keyword = workout_type if workout_type not in place_type_map else None

        resp = gmaps.places_nearby(
            location=(lat, lng),
            radius=5000,
            type=place_type,
            keyword=keyword,
            rank_by="prominence",
        )

        places = resp.get("results", [])[:limit]
        if not places:
            return f"No {workout_type} areas found near {location}."

        results = []
        for p in places:
            rating = p.get("rating", "N/A")
            address = p.get("vicinity", "N/A")
            open_now = p.get("opening_hours", {}).get("open_now")
            status = "Open now" if open_now else ("Closed" if open_now is False else "")
            results.append(
                f"**{p['name']}** | Rating: {rating}/5 | {status}\n"
                f"  Address: {address}"
            )

        return "\n".join(results)
    except Exception as e:
        return f"Workout area search error: {str(e)}"


@tool
def book_restaurant(
    restaurant_name: str,
    restaurant_address: str,
    date: str,
    time: str,
    party_size: int,
    guest_name: str,
    guest_email: str,
) -> str:
    """Make a restaurant reservation (simulated — in production integrates with OpenTable/Resy).
    Returns a confirmation reference number.

    Args:
        restaurant_name: Name of the restaurant
        restaurant_address: Address of the restaurant
        date: Reservation date in YYYY-MM-DD format
        time: Reservation time in HH:MM format (e.g. "19:30")
        party_size: Number of guests
        guest_name: Name for the reservation
        guest_email: Contact email
    """
    ref = f"RST-{uuid.uuid4().hex[:8].upper()}"
    _reservations[ref] = {
        "type": "restaurant",
        "restaurant_name": restaurant_name,
        "restaurant_address": restaurant_address,
        "date": date,
        "time": time,
        "party_size": party_size,
        "guest_name": guest_name,
        "guest_email": guest_email,
        "status": "confirmed",
    }
    return (
        f"✅ Restaurant reservation confirmed!\n"
        f"Reference: {ref}\n"
        f"Restaurant: {restaurant_name}\n"
        f"Address: {restaurant_address}\n"
        f"Date & Time: {date} at {time}\n"
        f"Party size: {party_size}\n"
        f"Name: {guest_name}\n"
        f"Note: Please arrive 10 minutes early. Cancellation policies vary by restaurant."
    )


@tool
def cancel_restaurant_reservation(booking_reference: str) -> str:
    """Cancel a restaurant reservation.

    Args:
        booking_reference: The reservation reference starting with RST-
    """
    if booking_reference not in _reservations:
        return f"Reservation {booking_reference} not found."
    res = _reservations[booking_reference]
    if res["type"] != "restaurant":
        return f"{booking_reference} is not a restaurant reservation."
    _reservations[booking_reference]["status"] = "cancelled"
    return (
        f"✅ Restaurant reservation {booking_reference} at {res['restaurant_name']} "
        f"on {res['date']} has been cancelled."
    )
