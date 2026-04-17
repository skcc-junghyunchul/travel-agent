# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in API keys before running

# Run
python main.py

# Verify imports without running the agent
python -c "from agent.graph import create_travel_agent; print('OK')"

# Check a single tool file for syntax errors
python -m py_compile tools/flights.py
```

There are no tests or linter configs in this project yet. To add them: `pip install pytest ruff` and create `tests/`.

## Architecture

**Entry point**: `main.py` — Rich CLI chat loop. Calls `agent.invoke()` each turn with a fixed `thread_id` so `MemorySaver` retains conversation history across turns within a session.

**Agent**: `agent/graph.py` — `create_react_agent(AzureChatOpenAI, tools, checkpointer=MemorySaver)`. Standard ReAct loop: LLM decides tool calls → tools execute → results fed back to LLM → repeat until final text response. System prompt in `agent/prompts.py` governs the full planning and booking workflow.

**Tools** (`tools/`): One file per domain. All functions use `@tool` from `langchain_core.tools` — the docstring becomes the tool description the LLM sees. Registered centrally in `tools/__init__.py:get_all_tools()`.

**External APIs**:
| File | API | Notes |
|---|---|---|
| `tools/search.py`, `tools/activities.py` | Tavily | Real-time web search |
| `tools/flights.py`, `tools/hotels.py` | Duffel | Air API v1 for flights; Stays API v2 for hotels; use `duffel_test_...` token for sandbox |
| `tools/restaurants.py` | Yelp Fusion | Booking is simulated (no public booking API) |
| `tools/transportation.py` | Google Maps | Directions, Places, Distance Matrix APIs must all be enabled |
| `tools/payment.py` | Stripe | Use `sk_test_...`; test card `4242424242424242` |
| `tools/export.py` | openpyxl | No API; writes `.xlsx` locally |

**Azure OpenAI config** (`config/settings.py`): Four env vars required — `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT_NAME` (e.g. `gpt-4o`), `AZURE_OPENAI_API_VERSION` (e.g. `2024-02-01`).

**Excel export** (`tools/export.py`): The LLM must produce a specific JSON schema (documented in `agent/prompts.py` and the `export_itinerary_to_excel` docstring) and pass it as a string argument to the tool. The tool writes 5 sheets: Overview, Daily Itinerary, Flights, Accommodation, Workout Areas.

**Models** (`models/itinerary.py`): Pydantic v2 models matching the export schema. Not wired into agent state — the LLM builds JSON inline. Useful as a reference for the expected shape.

## Adding a new tool

1. Add a `@tool`-decorated function in the relevant `tools/` file (docstring = LLM description, type hints = parameters)
2. Import and append it in `tools/__init__.py:get_all_tools()`

## Key constraints

- All agent context lives in `messages` — there is no separate structured state. The LLM must carry itinerary data as text/JSON within the conversation.
- Restaurant and activity reservations are in-memory dicts (`_reservations` in `restaurants.py`, `_bookings` in `activities.py`) and reset on restart. A DB layer is needed for persistence.
- Duffel test mode (`duffel_test_...`) simulates bookings and returns real-format references, but no actual reservation is made. Switch to `duffel_live_...` for production.
- Raw card details are sent to Stripe's API directly (PCI DSS SAQ D scope). For production, replace with Stripe.js tokenization.
