import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme
from langchain_core.messages import HumanMessage

from agent.graph import create_travel_agent

THEME = Theme({
    "user": "bold cyan",
    "agent": "bold green",
    "system": "bold yellow",
    "error": "bold red",
})

console = Console(theme=THEME)

WELCOME = """
# ✈️  Travel Itinerary Agent

I can help you:
- 🗺️  Plan detailed day-by-day itineraries based on trending destinations
- 🏨  Find and book flights, hotels, restaurants, and activities
- 🏋️  Locate running paths, trails, and gyms at your destination
- 📊  Export your itinerary to Excel
- 💳  Handle all reservations and payments in one go
- ✏️  Modify or cancel any booking

**To get started, just tell me where you'd like to go — or ask for destination suggestions!**

Type `exit` or `quit` to end the session.
"""


def run_chat():
    console.print(Panel(Markdown(WELCOME), border_style="blue", title="[bold blue]Travel Agent[/bold blue]"))

    try:
        agent = create_travel_agent()
    except Exception as e:
        console.print(f"[error]Failed to initialize agent: {e}[/error]")
        console.print("[system]Make sure your .env file is configured with all required API keys.[/system]")
        sys.exit(1)

    config = {"configurable": {"thread_id": "travel-session-1"}}

    while True:
        try:
            user_input = Prompt.ask("\n[user]You[/user]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[system]Goodbye! Safe travels! ✈️[/system]")
            break

        if user_input.strip().lower() in ("exit", "quit", "bye", "goodbye"):
            console.print("[system]Goodbye! Safe travels! ✈️[/system]")
            break

        if not user_input.strip():
            continue

        console.print()
        with console.status("[agent]Agent is thinking...[/agent]", spinner="dots"):
            try:
                result = agent.invoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    config=config,
                )
                response = result["messages"][-1].content
            except Exception as e:
                console.print(f"[error]Error: {e}[/error]")
                continue

        console.print(Panel(
            Markdown(response) if response.strip().startswith(("#", "*", "-", "`")) else response,
            title="[agent]✈️  Travel Agent[/agent]",
            border_style="green",
        ))


if __name__ == "__main__":
    run_chat()
