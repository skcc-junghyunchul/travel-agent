import requests
from langchain_core.tools import tool
from config.settings import DUFFEL_API_KEY

BASE_URL = "https://api.duffel.com"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {DUFFEL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Duffel-Version": "v1",
    }


@tool
def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 1,
    cabin_class: str = "economy",
    return_date: str = "",
    max_results: int = 5,
) -> str:
    """Search for available flights using IATA airport codes via Duffel.

    Args:
        origin: IATA departure airport code (e.g. "JFK", "ICN", "LHR")
        destination: IATA destination airport code (e.g. "CDG", "NRT", "DXB")
        departure_date: Departure date in YYYY-MM-DD format
        adults: Number of adult passengers
        cabin_class: "economy", "premium_economy", "business", or "first"
        return_date: Return date in YYYY-MM-DD format (leave empty for one-way)
        max_results: Maximum number of results to return
    """
    try:
        slices = [{"origin": origin, "destination": destination, "departure_date": departure_date}]
        if return_date:
            slices.append({"origin": destination, "destination": origin, "departure_date": return_date})

        resp = requests.post(
            f"{BASE_URL}/air/offer_requests",
            headers=_headers(),
            json={
                "data": {
                    "slices": slices,
                    "passengers": [{"type": "adult"} for _ in range(adults)],
                    "cabin_class": cabin_class,
                    "return_offers": True,
                }
            },
            timeout=30,
        )
        resp.raise_for_status()
        offers = resp.json()["data"].get("offers", [])[:max_results]

        if not offers:
            return "No flights found for this route and date."

        results = []
        for i, offer in enumerate(offers, 1):
            seg = offer["slices"][0]["segments"][0]
            last_seg = offer["slices"][0]["segments"][-1]
            stops = len(offer["slices"][0]["segments"]) - 1
            airline = seg["operating_carrier"]["name"]
            flight_no = f"{seg['operating_carrier']['iata_code']}{seg['operating_carrier_flight_number']}"
            results.append(
                f"Option {i}: {airline} {flight_no} | "
                f"{seg['origin']['iata_code']} {seg['departing_at']} → "
                f"{last_seg['destination']['iata_code']} {last_seg['arriving_at']} | "
                f"Stops: {stops} | "
                f"Price: {offer['total_currency']} {offer['total_amount']}/person | "
                f"OfferID: {offer['id']}"
            )
        return "\n".join(results)

    except requests.HTTPError as e:
        return f"Duffel API error: {e.response.text}"
    except Exception as e:
        return f"Flight search error: {str(e)}"


@tool
def book_flight(
    offer_id: str,
    passenger_first_name: str,
    passenger_last_name: str,
    passenger_date_of_birth: str,
    passenger_email: str,
    passenger_phone: str,
    passenger_gender: str = "m",
) -> str:
    """Book a flight using an offer ID returned by search_flights.
    Returns an order ID and booking reference on success.

    Args:
        offer_id: Offer ID from search_flights (starts with off_)
        passenger_first_name: First name
        passenger_last_name: Last name
        passenger_date_of_birth: Date of birth in YYYY-MM-DD format
        passenger_email: Contact email
        passenger_phone: Phone with country code (e.g. "+12025551234")
        passenger_gender: "m" or "f"
    """
    try:
        offer_resp = requests.get(
            f"{BASE_URL}/air/offers/{offer_id}",
            headers=_headers(),
            timeout=15,
        )
        offer_resp.raise_for_status()
        offer = offer_resp.json()["data"]
        passenger_id = offer["passengers"][0]["id"]

        resp = requests.post(
            f"{BASE_URL}/air/orders",
            headers=_headers(),
            json={
                "data": {
                    "type": "instant",
                    "selected_offers": [offer_id],
                    "passengers": [{
                        "id": passenger_id,
                        "title": "mr" if passenger_gender == "m" else "ms",
                        "given_name": passenger_first_name,
                        "family_name": passenger_last_name,
                        "born_on": passenger_date_of_birth,
                        "email": passenger_email,
                        "phone_number": passenger_phone,
                        "gender": passenger_gender,
                    }],
                    "payments": [{
                        "type": "balance",
                        "amount": offer["total_amount"],
                        "currency": offer["total_currency"],
                    }],
                }
            },
            timeout=30,
        )
        resp.raise_for_status()
        order = resp.json()["data"]
        seg = order["slices"][0]["segments"][0]

        return (
            f"✅ Flight booked!\n"
            f"Order ID: {order['id']}\n"
            f"Booking Reference: {order['booking_reference']}\n"
            f"Flight: {seg['operating_carrier']['iata_code']}{seg['operating_carrier_flight_number']}\n"
            f"Route: {seg['origin']['iata_code']} → {seg['destination']['iata_code']}\n"
            f"Departure: {seg['departing_at']}\n"
            f"Total: {order['total_currency']} {order['total_amount']}\n"
            f"Passenger: {passenger_first_name} {passenger_last_name}"
        )

    except requests.HTTPError as e:
        return f"Duffel booking error: {e.response.text}"
    except Exception as e:
        return f"Flight booking error: {str(e)}"


@tool
def cancel_flight(order_id: str) -> str:
    """Cancel a booked flight. Initiates and confirms the cancellation in one step.

    Args:
        order_id: The order ID returned when the flight was booked (starts with ord_)
    """
    try:
        cancel_resp = requests.post(
            f"{BASE_URL}/air/order_cancellations",
            headers=_headers(),
            json={"data": {"order_id": order_id}},
            timeout=15,
        )
        cancel_resp.raise_for_status()
        cancellation = cancel_resp.json()["data"]
        cancellation_id = cancellation["id"]
        refund_amount = cancellation.get("refund_amount", "0")
        refund_currency = cancellation.get("refund_currency", "")

        confirm_resp = requests.post(
            f"{BASE_URL}/air/order_cancellations/{cancellation_id}/actions/confirm",
            headers=_headers(),
            timeout=15,
        )
        confirm_resp.raise_for_status()

        return (
            f"✅ Flight order {order_id} cancelled.\n"
            f"Refund: {refund_currency} {refund_amount}\n"
            f"Note: Refund timeline depends on the airline's policy."
        )

    except requests.HTTPError as e:
        return f"Cancellation error: {e.response.text}"
    except Exception as e:
        return f"Flight cancellation error: {str(e)}"
