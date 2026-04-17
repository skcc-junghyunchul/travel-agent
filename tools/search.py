from langchain_core.tools import tool
from tavily import TavilyClient
from config.settings import TAVILY_API_KEY


def _get_client() -> TavilyClient:
    return TavilyClient(api_key=TAVILY_API_KEY)


@tool
def search_popular_destinations(query: str) -> str:
    """Search for the most popular and trending travel destinations.
    Use this to find up-to-date recommendations from travel blogs, social media,
    TripAdvisor, Booking.com, and other travel platforms.

    Args:
        query: Search query e.g. "most popular travel destinations Europe 2024"
    """
    try:
        client = _get_client()
        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=8,
            include_domains=[
                "tripadvisor.com", "booking.com", "lonelyplanet.com",
                "travelandleisure.com", "cntraveler.com", "timeout.com",
                "reddit.com", "instagram.com", "nomadlist.com"
            ]
        )
        output = []
        for r in results.get("results", []):
            output.append(f"**{r['title']}**\n{r['content'][:300]}\nSource: {r['url']}\n")
        return "\n---\n".join(output) if output else "No results found."
    except Exception as e:
        return f"Search error: {str(e)}"


@tool
def search_travel_info(query: str) -> str:
    """Search for specific travel information such as attractions, restaurants,
    transportation options, local tips, visa requirements, weather, and more.
    Also useful for finding workout areas, running routes, trails, and gyms.

    Args:
        query: Specific search query e.g. "best running trails Paris France"
    """
    try:
        client = _get_client()
        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=6
        )
        output = []
        for r in results.get("results", []):
            output.append(f"**{r['title']}**\n{r['content'][:400]}\nSource: {r['url']}\n")
        return "\n---\n".join(output) if output else "No results found."
    except Exception as e:
        return f"Search error: {str(e)}"
