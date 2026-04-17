import googlemaps
from langchain_core.tools import tool
from config.settings import GOOGLE_MAPS_API_KEY


def _get_gmaps() -> googlemaps.Client:
    return googlemaps.Client(key=GOOGLE_MAPS_API_KEY)


@tool
def get_directions(
    origin: str,
    destination: str,
    mode: str = "transit",
    departure_time: str = "now",
) -> str:
    """Get directions and transportation options between two locations.
    Use for airport transfers, inter-city transport, and local navigation.

    Args:
        origin: Starting point (e.g. "Charles de Gaulle Airport, Paris")
        destination: Ending point (e.g. "Eiffel Tower, Paris")
        mode: "transit", "driving", "walking", or "bicycling"
        departure_time: "now" or ISO datetime string
    """
    try:
        gmaps = _get_gmaps()
        dt = "now" if departure_time == "now" else departure_time
        result = gmaps.directions(origin, destination, mode=mode, departure_time=dt)

        if not result:
            return f"No {mode} route found from {origin} to {destination}."

        leg = result[0]["legs"][0]
        distance = leg["distance"]["text"]
        duration = leg["duration"]["text"]
        steps = leg["steps"]

        summary = (
            f"Route: {origin} → {destination}\n"
            f"Mode: {mode} | Distance: {distance} | Duration: {duration}\n\nSteps:\n"
        )
        for i, step in enumerate(steps[:8], 1):
            instruction = step["html_instructions"].replace("<b>", "").replace("</b>", "").replace("<div>", " ").replace("</div>", "")
            summary += f"{i}. {instruction} ({step['distance']['text']})\n"

        if len(steps) > 8:
            summary += f"... and {len(steps) - 8} more steps"

        return summary
    except Exception as e:
        return f"Directions error: {str(e)}"


@tool
def search_local_transport(
    location: str,
    transport_type: str = "all",
) -> str:
    """Search for local transportation options at a destination.
    Includes metro, bus, taxis, ride-share, bike rental, etc.

    Args:
        location: City or specific area (e.g. "Paris city center")
        transport_type: "metro", "bus", "taxi", "bike", "all"
    """
    try:
        gmaps = _get_gmaps()
        query = f"{transport_type} transportation {location}" if transport_type != "all" else f"public transportation stations {location}"
        places = gmaps.places(query=query)

        results = []
        for p in places.get("results", [])[:6]:
            name = p["name"]
            address = p.get("formatted_address", p.get("vicinity", "N/A"))
            rating = p.get("rating", "N/A")
            results.append(f"**{name}**\n  Address: {address} | Rating: {rating}")

        return "\n\n".join(results) if results else "No transport options found."
    except Exception as e:
        return f"Transport search error: {str(e)}"


@tool
def estimate_transport_cost(
    origin: str,
    destination: str,
    mode: str = "transit",
) -> str:
    """Estimate transportation cost between two points.

    Args:
        origin: Starting location
        destination: Destination
        mode: "transit", "taxi", "driving"
    """
    try:
        gmaps = _get_gmaps()
        result = gmaps.distance_matrix(origin, destination, mode=mode)
        element = result["rows"][0]["elements"][0]

        if element["status"] != "OK":
            return f"Could not calculate distance from {origin} to {destination}."

        distance_m = element["distance"]["value"]
        distance_text = element["distance"]["text"]
        duration_text = element["duration"]["text"]

        cost_estimate = ""
        if mode == "taxi":
            base_fare = 3.0
            per_km = 2.0
            km = distance_m / 1000
            estimated = base_fare + (km * per_km)
            cost_estimate = f"Estimated taxi cost: ~${estimated:.2f} USD"
        elif mode == "transit":
            cost_estimate = "Typical transit cost: $2-5 USD per trip (varies by city)"
        else:
            cost_estimate = "Fuel cost depends on your vehicle"

        return (
            f"From: {origin}\nTo: {destination}\n"
            f"Distance: {distance_text} | Duration: {duration_text}\n{cost_estimate}"
        )
    except Exception as e:
        return f"Cost estimation error: {str(e)}"
