from pydantic import BaseModel
from typing import Optional


class FlightInfo(BaseModel):
    airline: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_time: str
    arrival_time: str
    price_per_person: float
    booking_reference: Optional[str] = None


class Accommodation(BaseModel):
    name: str
    address: str
    check_in: str
    check_out: str
    price_per_night: float
    booking_reference: Optional[str] = None


class Activity(BaseModel):
    time: str
    name: str
    description: str
    location: str
    duration: str
    cost: float
    booking_required: bool = False
    booking_reference: Optional[str] = None


class Meal(BaseModel):
    meal_type: str  # breakfast, lunch, dinner
    restaurant: str
    cuisine: str
    address: str
    price_range: str
    reservation_required: bool = False
    booking_reference: Optional[str] = None


class TransportLeg(BaseModel):
    from_location: str
    to_location: str
    mode: str
    duration: str
    cost: float


class WorkoutArea(BaseModel):
    name: str
    workout_type: str  # running, trail, gym, yoga, etc.
    description: str
    location: str
    distance_or_details: str


class DayPlan(BaseModel):
    day: int
    date: str
    title: str
    accommodation: Optional[Accommodation] = None
    activities: list[Activity] = []
    meals: list[Meal] = []
    transportation: list[TransportLeg] = []
    workout: Optional[WorkoutArea] = None


class CostSummary(BaseModel):
    flights: float
    accommodation: float
    activities: float
    meals: float
    transportation: float
    total: float


class Itinerary(BaseModel):
    destination: str
    departure_city: str
    start_date: str
    end_date: str
    duration_days: int
    travelers: int
    age_groups: list[str]
    preferences: list[str]
    outbound_flight: Optional[FlightInfo] = None
    return_flight: Optional[FlightInfo] = None
    days: list[DayPlan] = []
    cost_summary: Optional[CostSummary] = None
