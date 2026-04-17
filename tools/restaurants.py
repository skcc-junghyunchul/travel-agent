import requests
import uuid
from langchain_core.tools import tool
from config.settings import YELP_API_KEY

YELP_API_BASE = "https://api.yelp.com/v3"

# In-memory reservation store (in production, persist to a database)
_reservations: dict[str, dict] = {}


def _yelp_headers() -> dict:
    return {"Authorization": f"Bearer {YELP_API_KEY}"}


@tool
def search_restaurants(
    location: str,
    cuisine: str = "",
    price_range: str = "",
    limit: int = 8,
) -> str:
    """Search for restaurants in a location using Yelp.

    Args:
        location: City or address (e.g. "Paris, France", "Shibuya, Tokyo")
        cuisine: Food type (e.g. "french", "sushi", "italian", "local")
        price_range: Price level "1" (cheap) to "4" (expensive), comma-separated for multiple
        limit: Max number of results
    """
    try:
        params: dict = {
            "location": location,
            "categories": cuisine if cuisine else "restaurants",
            "sort_by": "rating",
            "limit": limit,
        }
        if price_range:
            params["price"] = price_range

        resp = requests.get(
            f"{YELP_API_BASE}/businesses/search",
            headers=_yelp_headers(),
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        businesses = resp.json().get("businesses", [])

        results = []
        for b in businesses:
            price = b.get("price", "N/A")
            rating = b.get("rating", "N/A")
            cats = ", ".join(c["title"] for c in b.get("categories", []))
            address = ", ".join(b.get("location", {}).get("display_address", []))
            results.append(
                f"**{b['name']}** | {cats} | Rating: {rating}/5 | Price: {price}\n"
                f"  Address: {address} | ID: {b['id']}"
            )

        return "\n".join(results) if results else "No restaurants found."
    except Exception as e:
        return f"Restaurant search error: {str(e)}"


@tool
def search_workout_areas(
    location: str,
    workout_type: str = "running,gyms,hiking",
    limit: int = 6,
) -> str:
    """Search for workout areas including running paths, trails, and gyms.

    Args:
        location: City or neighborhood (e.g. "Paris, France")
        workout_type: Comma-separated Yelp categories such as "running,gyms,hiking,yoga,parks"
        limit: Max number of results
    """
    try:
        params = {
            "location": location,
            "categories": workout_type,
            "sort_by": "rating",
            "limit": limit,
        }
        resp = requests.get(
            f"{YELP_API_BASE}/businesses/search",
            headers=_yelp_headers(),
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        businesses = resp.json().get("businesses", [])

        results = []
        for b in businesses:
            rating = b.get("rating", "N/A")
            cats = ", ".join(c["title"] for c in b.get("categories", []))
            address = ", ".join(b.get("location", {}).get("display_address", []))
            results.append(
                f"**{b['name']}** | {cats} | Rating: {rating}/5\n"
                f"  Address: {address}"
            )

        return "\n".join(results) if results else "No workout areas found."
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
