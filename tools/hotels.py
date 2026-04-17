import requests
import googlemaps
from langchain_core.tools import tool
from config.settings import DUFFEL_API_KEY, GOOGLE_MAPS_API_KEY

BASE_URL = "https://api.duffel.com"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {DUFFEL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Duffel-Version": "v2",
    }


def _geocode(city: str) -> tuple[float, float]:
    """Convert a city name to (latitude, longitude) via Google Maps."""
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    result = gmaps.geocode(city)
    if not result:
        raise ValueError(f"Could not geocode city: {city}")
    loc = result[0]["geometry"]["location"]
    return loc["lat"], loc["lng"]


@tool
def search_hotels(
    city_name: str,
    check_in_date: str,
    check_out_date: str,
    adults: int = 1,
    rooms: int = 1,
    radius_km: int = 5,
    max_results: int = 5,
) -> str:
    """Search for available hotels via Duffel Stays. Uses city name and geocodes it automatically.

    Args:
        city_name: City and country (e.g. "Paris, France", "Tokyo, Japan")
        check_in_date: Check-in date in YYYY-MM-DD format
        check_out_date: Check-out date in YYYY-MM-DD format
        adults: Number of adult guests
        rooms: Number of rooms required
        radius_km: Search radius from city center in kilometres
        max_results: Maximum number of results to return
    """
    try:
        lat, lng = _geocode(city_name)

        resp = requests.post(
            f"{BASE_URL}/stays/search",
            headers=_headers(),
            json={
                "data": {
                    "check_in_date": check_in_date,
                    "check_out_date": check_out_date,
                    "rooms": rooms,
                    "guests": [{"type": "adult"} for _ in range(adults)],
                    "location": {
                        "geographic_coordinates": {
                            "latitude": lat,
                            "longitude": lng,
                            "radius": radius_km,
                        }
                    },
                }
            },
            timeout=30,
        )
        resp.raise_for_status()
        items = resp.json()["data"][:max_results]

        if not items:
            return f"No hotels found in {city_name}."

        results = []
        for i, item in enumerate(items, 1):
            acc = item["accommodation"]
            addr = acc.get("location", {}).get("address", {})
            address_line = addr.get("line1", "") or addr.get("city_name", "N/A")
            stars = acc.get("rating", "N/A")
            cheapest = (
                f"{item['cheapest_rate_currency']} {item['cheapest_rate_public_amount']}"
                if item.get("cheapest_rate_public_amount")
                else "rates on request"
            )
            results.append(
                f"Option {i}: {acc['name']}\n"
                f"  Stars: {stars} | Address: {address_line}\n"
                f"  From: {cheapest} total\n"
                f"  Accommodation ID: {acc['id']}"
            )
        return "\n\n".join(results)

    except requests.HTTPError as e:
        return f"Duffel Stays error: {e.response.text}"
    except Exception as e:
        return f"Hotel search error: {str(e)}"


@tool
def book_hotel(
    accommodation_id: str,
    check_in_date: str,
    check_out_date: str,
    guest_first_name: str,
    guest_last_name: str,
    guest_email: str,
    guest_phone: str,
    adults: int = 1,
    rooms: int = 1,
) -> str:
    """Book a hotel using an accommodation ID from search_hotels.
    Automatically selects the cheapest available rate and creates a booking.

    Args:
        accommodation_id: Accommodation ID from search_hotels results
        check_in_date: Check-in date in YYYY-MM-DD format
        check_out_date: Check-out date in YYYY-MM-DD format
        guest_first_name: First name of primary guest
        guest_last_name: Last name of primary guest
        guest_email: Contact email
        guest_phone: Phone number with country code (e.g. "+12025551234")
        adults: Number of adult guests
        rooms: Number of rooms
    """
    try:
        rates_resp = requests.get(
            f"{BASE_URL}/stays/accommodation/{accommodation_id}/rates",
            headers=_headers(),
            params={
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "rooms": rooms,
                "guests": adults,
            },
            timeout=20,
        )
        rates_resp.raise_for_status()
        rates = rates_resp.json()["data"]

        if not rates:
            return "No rates available for this property on those dates."

        rate = sorted(rates, key=lambda r: float(r.get("public_amount", 9999)))[0]

        quote_resp = requests.post(
            f"{BASE_URL}/stays/quotes",
            headers=_headers(),
            json={"data": {"rate_id": rate["id"]}},
            timeout=20,
        )
        quote_resp.raise_for_status()
        quote = quote_resp.json()["data"]

        booking_resp = requests.post(
            f"{BASE_URL}/stays/bookings",
            headers=_headers(),
            json={
                "data": {
                    "quote_id": quote["id"],
                    "accommodation": {"id": accommodation_id},
                    "guests": [{
                        "given_name": guest_first_name,
                        "family_name": guest_last_name,
                        "email": guest_email,
                        "phone_number": guest_phone,
                    }],
                    "payment": {
                        "type": "balance",
                        "amount": quote.get("total_amount", "0"),
                        "currency": quote.get("currency", "USD"),
                    },
                }
            },
            timeout=30,
        )
        booking_resp.raise_for_status()
        booking = booking_resp.json()["data"]
        acc_name = booking.get("accommodation", {}).get("name", accommodation_id)

        return (
            f"✅ Hotel booked!\n"
            f"Booking ID: {booking['id']}\n"
            f"Confirmation: {booking.get('reference', 'N/A')}\n"
            f"Property: {acc_name}\n"
            f"Check-in: {check_in_date}\n"
            f"Check-out: {check_out_date}\n"
            f"Total: {quote.get('currency', '')} {quote.get('total_amount', '')}\n"
            f"Guest: {guest_first_name} {guest_last_name}"
        )

    except requests.HTTPError as e:
        return f"Duffel hotel booking error: {e.response.text}"
    except Exception as e:
        return f"Hotel booking error: {str(e)}"


@tool
def cancel_hotel(booking_id: str) -> str:
    """Cancel a hotel booking by booking ID.

    Args:
        booking_id: The booking ID returned when the hotel was booked
    """
    try:
        resp = requests.delete(
            f"{BASE_URL}/stays/bookings/{booking_id}",
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return (
            f"✅ Hotel booking {booking_id} cancelled.\n"
            f"Note: Refund terms are subject to the property's cancellation policy."
        )

    except requests.HTTPError as e:
        return f"Cancellation error: {e.response.text}"
    except Exception as e:
        return f"Hotel cancellation error: {str(e)}"
