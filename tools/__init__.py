from tools.search import search_popular_destinations, search_travel_info
from tools.flights import search_flights, book_flight, cancel_flight
from tools.hotels import search_hotels, book_hotel, cancel_hotel
from tools.restaurants import search_restaurants, search_workout_areas, book_restaurant, cancel_restaurant_reservation
from tools.transportation import get_directions, search_local_transport, estimate_transport_cost
from tools.activities import search_activities, book_activity, cancel_activity
from tools.payment import process_payment, get_payment_status, refund_payment
from tools.export import export_itinerary_to_excel


def get_all_tools() -> list:
    return [
        # Research & search
        search_popular_destinations,
        search_travel_info,
        search_activities,
        search_restaurants,
        search_workout_areas,
        search_local_transport,
        # Flights
        search_flights,
        book_flight,
        cancel_flight,
        # Hotels
        search_hotels,
        book_hotel,
        cancel_hotel,
        # Restaurants & activities
        book_restaurant,
        cancel_restaurant_reservation,
        book_activity,
        cancel_activity,
        # Transportation
        get_directions,
        estimate_transport_cost,
        # Payment
        process_payment,
        get_payment_status,
        refund_payment,
        # Export
        export_itinerary_to_excel,
    ]
