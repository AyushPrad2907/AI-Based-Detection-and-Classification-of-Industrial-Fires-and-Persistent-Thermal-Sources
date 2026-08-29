import asyncio
import httpx

query = """[out:json][timeout:10];
(
  node["landuse"="industrial"](around:5000,28.6139,77.2090);
  way["landuse"="industrial"](around:5000,28.6139,77.2090);
  node["power"~"plant|generator|substation"](around:5000,28.6139,77.2090);
  way["power"~"plant|generator|substation"](around:5000,28.6139,77.2090);
  node["man_made"~"works|petroleum_refinery|flare|pipeline|storage_tank|kiln|chimney"](around:5000,28.6139,77.2090);
  way["man_made"~"works|petroleum_refinery|flare|pipeline|storage_tank|kiln|chimney"](around:5000,28.6139,77.2090);
);
out center;
"""

mirrors = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter"
]

async def test():
    headers = {"User-Agent": "SIH26162-FireDetector/1.0 (academic research)"}
    async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
        for m in mirrors:
            try:
                r = await client.post(m, data={"data": query})
                print(f"{m} -> status {r.status_code}, len: {len(r.text)}")
                if r.status_code == 200:
                    d = r.json()
                    print("  Elements count:", len(d.get("elements", [])))
            except Exception as e:
                print(f"{m} -> ERROR {e}")

if __name__ == "__main__":
    asyncio.run(test())
