import uuid
from langchain_core.tools import tool
from tavily import TavilyClient
from config.settings import TAVILY_API_KEY

_bookings: dict[str, dict] = {}


def _get_tavily() -> TavilyClient:
    return TavilyClient(api_key=TAVILY_API_KEY)


@tool
def search_activities(
    destination: str,
    activity_type: str = "",
    age_group: str = "adults",
) -> str:
    """Search for activities, attractions, and experiences at a destination.
    Returns up-to-date recommendations from travel sites and blogs.

    Args:
        destination: City and country (e.g. "Kyoto, Japan")
        activity_type: Type of activity e.g. "museums", "outdoor", "food tours", "nightlife", "family"
        age_group: "family", "adults", "seniors", "young adults"
    """
    try:
        client = _get_tavily()
        query = f"best {activity_type or 'things to do'} in {destination} for {age_group} 2024 2025"
        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=7,
            include_domains=[
                "tripadvisor.com", "viator.com", "getyourguide.com",
                "timeout.com", "lonelyplanet.com", "cntraveler.com"
            ]
        )
        output = []
        for r in results.get("results", []):
            output.append(f"**{r['title']}**\n{r['content'][:350]}\nSource: {r['url']}")
        return "\n---\n".join(output) if output else "No activities found."
    except Exception as e:
        return f"Activity search error: {str(e)}"


@tool
def book_activity(
    activity_name: str,
    activity_location: str,
    date: str,
    time: str,
    participants: int,
    guest_name: str,
    guest_email: str,
    estimated_cost_per_person: float = 0.0,
) -> str:
    """Book an activity or attraction entry. Returns a booking reference.
    Note: For venues like the Louvre, Colosseum, etc., this simulates a direct booking.
    In production, integrate with GetYourGuide or Viator APIs for real bookings.

    Args:
        activity_name: Name of the activity or attraction
        activity_location: Address or location
        date: Date in YYYY-MM-DD format
        time: Start time in HH:MM format
        participants: Number of participants
        guest_name: Name for the booking
        guest_email: Contact email
        estimated_cost_per_person: Cost per person in USD
    """
    ref = f"ACT-{uuid.uuid4().hex[:8].upper()}"
    total_cost = estimated_cost_per_person * participants
    _bookings[ref] = {
        "type": "activity",
        "activity_name": activity_name,
        "activity_location": activity_location,
        "date": date,
        "time": time,
        "participants": participants,
        "guest_name": guest_name,
        "guest_email": guest_email,
        "cost_per_person": estimated_cost_per_person,
        "total_cost": total_cost,
        "status": "confirmed",
    }
    return (
        f"✅ Activity booked!\n"
        f"Reference: {ref}\n"
        f"Activity: {activity_name}\n"
        f"Location: {activity_location}\n"
        f"Date & Time: {date} at {time}\n"
        f"Participants: {participants}\n"
        f"Total Cost: ${total_cost:.2f} USD\n"
        f"Name: {guest_name}"
    )


@tool
def cancel_activity(booking_reference: str) -> str:
    """Cancel an activity booking.

    Args:
        booking_reference: Reference starting with ACT-
    """
    if booking_reference not in _bookings:
        return f"Booking {booking_reference} not found."
    b = _bookings[booking_reference]
    if b["type"] != "activity":
        return f"{booking_reference} is not an activity booking."
    _bookings[booking_reference]["status"] = "cancelled"
    return (
        f"✅ Activity booking {booking_reference} ({b['activity_name']}) "
        f"on {b['date']} has been cancelled. "
        f"Cancellation policies vary by provider — check your confirmation email for refund terms."
    )
