import asyncio
import httpx

async def test_api():
    url = "http://localhost:8000/api/v1/digest/461874849"
    print(f"Testing API: {url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("Success! Data received.")
                print(f"Top Stories: {len(data.get('top_stories', []))}")
                print(f"Other News: {len(data.get('other_news', []))}")
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
