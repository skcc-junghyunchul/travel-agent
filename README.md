# ✈️ Travel Itinerary Agent

A chat-based AI travel agent built with Python and LangGraph that creates detailed itineraries, makes real reservations, and processes payments — all through conversation.

## Features

- **AI-powered planning** — Creates day-by-day itineraries based on your preferences
- **Trending destinations** — Searches TripAdvisor, travel blogs, social media, and booking sites for up-to-date recommendations
- **Full booking suite** — Flights (Duffel), hotels (Duffel Stays), restaurants (Yelp), activities, transport
- **Workout finder** — Running routes, trails, and gyms at your destination
- **Excel export** — Exports the full itinerary to a formatted `.xlsx` file
- **Payment processing** — Secure payments via Stripe (test mode by default)
- **Modify & cancel** — Change or cancel any reservation with cancellation policy info

## Prerequisites

- Python 3.11+
- API keys for all services (see below)

## Setup

### 1. Clone and install dependencies

```bash
cd 17_travel_agent_claude
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` and fill in each key:

| Variable | Where to get it |
|---|---|
| `AZURE_OPENAI_API_KEY` | Azure Portal → your OpenAI resource → Keys and Endpoint |
| `AZURE_OPENAI_ENDPOINT` | Azure Portal → your OpenAI resource → Keys and Endpoint |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Azure AI Studio → Deployments (e.g. `gpt-4o`) |
| `AZURE_OPENAI_API_VERSION` | Use `2024-02-01` (or latest stable) |
| `TAVILY_API_KEY` | https://app.tavily.com |
| `DUFFEL_API_KEY` | https://app.duffel.com → Settings → Access tokens (use `duffel_test_...`) |
| `GOOGLE_MAPS_API_KEY` | https://console.cloud.google.com — enable Directions, Places, Distance Matrix APIs |
| `YELP_API_KEY` | https://www.yelp.com/developers |
| `STRIPE_API_KEY` | https://dashboard.stripe.com/test/apikeys (use `sk_test_...`) |

> **Duffel sandbox**: Use a `duffel_test_...` token for test mode. Flight and hotel bookings are simulated and return real-format references. Switch to `duffel_live_...` for production.

> **Stripe test mode**: Use card number `4242 4242 4242 4242` with any future expiry and any CVC for test payments.

### 3. Run the agent

```bash
python main.py
```

## Usage Examples

**Plan a trip:**
> "I want to go to Japan for 10 days in October. There are 2 of us, both adults in our 30s. We love food, temples, and outdoor hiking. Flying from Seoul."

**Get destination suggestions:**
> "What are the most trending travel destinations for 2025 that are good for solo travel?"

**Export to Excel after planning:**
> "Export my itinerary to Excel"

**Book everything at once:**
> "Book all the flights, hotels, and restaurants we discussed"

**Modify or cancel:**
> "Cancel my hotel reservation" or "Change the restaurant booking for Day 3 to 8pm"

## Architecture

### System Overview

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │                        User (CLI Chat)                              │
  └───────────────────────────┬─────────────────────────────────────────┘
                    chat message │ ▲ response
                               ▼ │
  ┌─────────────────────────────────────────────────────────────────────┐
  │               LangGraph ReAct Agent  (agent/)                       │
  │                                                                     │
  │   ┌─────────────────────┐      ┌──────────────────────────────┐    │
  │   │  System Prompt      │─────>│  Azure OpenAI GPT-4o         │    │
  │   │  (prompts.py)       │      │  (AzureChatOpenAI)           │    │
  │   └─────────────────────┘      └──────────┬───────────────────┘    │
  │                                            │ ▲                      │
  │                                 tool calls │ │ tool results         │
  │   ┌─────────────────────┐                  │ │                      │
  │   │  Conversation State │                  │ │                      │
  │   │  (MemorySaver)      │                  │ │                      │
  │   └─────────────────────┘                  │ │                      │
  └────────────────────────────────────────────┼─┼──────────────────────┘
                                               ▼ │
  ┌─────────────────────────────────────────────────────────────────────┐
  │                        Tools Layer  (tools/)                        │
  │                                                                     │
  │  search.py          flights.py        hotels.py     restaurants.py  │
  │  Destination   ──>  Search/Book/ ──>  Search/Book/  Search/Book/    │
  │  research           Cancel            Cancel        Cancel          │
  │                                                                     │
  │  transportation.py  activities.py     payment.py    export.py       │
  │  Directions    ──>  Search/Book/ ──>  Charge/  ──>  Excel           │
  │  & cost             Cancel            Refund        generation      │
  └──────┬─────────────────┬──────────────┬─────────────┬──────────────┘
         │                 │              │             │
         ▼                 ▼              ▼             ▼
  ┌────────────┐  ┌──────────────┐  ┌─────────┐  ┌───────────────────┐
  │   Tavily   │  │    Duffel    │  │  Yelp   │  │   Google Maps     │
  │ Web Search │  │Flights/Hotels│  │ Fusion  │  │   Directions      │
  └────────────┘  └──────────────┘  └─────────┘  └───────────────────┘
                                                  ┌────────┐  ┌───────┐
                                                  │ Stripe │  │openpyxl
                                                  │Payment │  │ Excel │
                                                  └────────┘  └───────┘
```

### ReAct Agent Flow

```
  User              main.py            LangGraph            Azure OpenAI       External API
   │                   │                 Agent                  │                   │
   │  "Plan 7-day      │                   │                    │                   │
   │   trip to Tokyo"  │                   │                    │                   │
   │──────────────────>│                   │                    │                   │
   │                   │  invoke(messages) │                    │                   │
   │                   │──────────────────>│                    │                   │
   │                   │                   │  messages +        │                   │
   │                   │                   │  system prompt     │                   │
   │                   │                   │───────────────────>│                   │
   │                   │                   │                    │  tool_call:       │
   │                   │                   │                    │  search_popular_  │
   │                   │                   │<───────────────────│  destinations     │
   │                   │                   │  execute tool      │                   │
   │                   │                   │──────────────────────────────────────>│
   │                   │                   │                    │   Tavily search   │
   │                   │                   │<──────────────────────────────────────│
   │                   │                   │  tool result       │                   │
   │                   │                   │───────────────────>│                   │
   │                   │                   │                    │  tool_call:       │
   │                   │                   │                    │  search_flights   │
   │                   │                   │<───────────────────│  (ICN --> NRT)    │
   │                   │                   │  execute tool      │                   │
   │                   │                   │──────────────────────────────────────>│
   │                   │                   │                    │  Duffel API       │
   │                   │                   │<──────────────────────────────────────│
   │                   │                   │  tool result       │                   │
   │                   │                   │───────────────────>│                   │
   │                   │                   │                    │  final response   │
   │                   │                   │<───────────────────│  (itinerary)      │
   │                   │  response         │                    │                   │
   │                   │<──────────────────│                    │                   │
   │  itinerary        │                   │                    │                   │
   │<──────────────────│                   │                    │                   │
   │                   │                   │                    │                   │
   │  "Book everything"│                   │                    │                   │
   │──────────────────>│                   │                    │                   │
   │                   │                   │  book_flight ──> book_hotel            │
   │                   │                   │  ──> book_restaurant ──> book_activity │
   │                   │                   │  ──> process_payment                  │
   │  all confirmed    │                   │                    │                   │
   │<──────────────────│                   │                    │                   │
```

### LangGraph Agent Graph

```
                        ┌─────────┐
                        │  START  │
                        └────┬────┘
                             │  HumanMessage
                             ▼
                   ┌─────────────────────┐
              ┌───>│    agent  node      │
              │    │  (Azure OpenAI LLM) │
              │    │  + system prompt    │
              │    └──────────┬──────────┘
              │               │
              │    ┌──────────┴───────────┐
              │    │  has tool calls?     │
              │    └──────────┬───────────┘
              │               │
              │        YES    │    NO
              │    ┌──────────┘    └──────────┐
              │    ▼                          ▼
              │  ┌──────────────────┐    ┌─────────┐
              │  │   tools  node    │    │   END   │
              │  │                  │    └─────────┘
              │  │  search          │
              │  │  search_flights  │
              │  │  book_flight     │
              │  │  search_hotels   │
              │  │  book_hotel      │
              │  │  book_restaurant │
              │  │  book_activity   │
              │  │  get_directions  │
              │  │  process_payment │
              │  │  export_excel    │
              │  │  ... (23 tools)  │
              │  └────────┬─────────┘
              │           │  ToolMessages
              └───────────┘  (loop back)


  State shape:
  ┌────────────────────────────────────────────────────┐
  │  TravelAgentState                                  │
  │                                                    │
  │  messages: list  <── add_messages reducer          │
  │  [HumanMessage, AIMessage, ToolMessage, ...]       │
  │                                                    │
  │  Persisted across turns via MemorySaver            │
  │  keyed by thread_id = "travel-session-1"           │
  └────────────────────────────────────────────────────┘
```

### Project Structure

```
travel_agent/
├── main.py              # CLI chat interface (Rich)
├── agent/
│   ├── graph.py         # LangGraph ReAct agent (AzureChatOpenAI + MemorySaver)
│   ├── state.py         # TypedDict state with add_messages reducer
│   └── prompts.py       # System prompt with full workflow instructions
├── tools/
│   ├── search.py        # Tavily — destination & activity research
│   ├── flights.py       # Duffel — search, book, cancel flights (Air API v1)
│   ├── hotels.py        # Duffel — search, book, cancel hotels (Stays API v2)
│   ├── restaurants.py   # Yelp Fusion — search restaurants & workout areas; mock booking
│   ├── transportation.py# Google Maps — directions, transit, cost estimates
│   ├── activities.py    # Tavily + simulated booking for attractions/tours
│   ├── payment.py       # Stripe — charge, check status, refund
│   └── export.py        # openpyxl — multi-sheet Excel export
├── models/
│   └── itinerary.py     # Pydantic models for itinerary data
├── config/
│   └── settings.py      # Environment variable loading
└── .env.example
```

### Restaurant bookings

There is no universal public restaurant booking API. The agent uses Yelp to discover restaurants and a mock booking system that generates confirmation references. For production, integrate with [OpenTable's API](https://www.opentable.com/partner-with-us) or [Resy's API](https://resy.com/api).

### PCI compliance note

The payment tool collects raw card details and sends them directly to Stripe's API. This requires PCI DSS SAQ D compliance. For a production web application, use [Stripe.js Elements](https://stripe.com/docs/payments/elements) to tokenize cards client-side.
