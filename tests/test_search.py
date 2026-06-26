# test_search.py
import asyncio
from omega_mcp.tools.web import search_the_web

async def test():
    print("Testing Omega Web Search Client...")
    # Directly invoke the semantic tool function
    result = search_the_web(query="Latest Formula 1 race winner")
    print("\n--- Results Output ---")
    print(result)

if __name__ == "__main__":
    asyncio.run(test())