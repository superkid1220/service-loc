from fastapi import FastAPI, Query
import httpx
import math

app = FastAPI()

SHEETDB_URL = "https://sheetdb.io/api/v1/y7b56e2q4vutg"

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # 地球半徑 (km)
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

@app.get("/")
async def root():
    return {"message": "Service Locator API is running."}

@app.get("/nearest")
async def nearest(lat: float = Query(...), lon: float = Query(...)):
    """
    Query parameters:
    - lat: 使用者緯度
    - lon: 使用者經度

    回傳最近保養據點名稱與地址
    """
    # Step 1: 讀取 SheetDB 資料
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(SHEETDB_URL, timeout=10.0)
            resp.raise_for_status()
        except Exception as e:
            return {"error": f"Failed to fetch data: {e}"}

    data = resp.json()

    # Step 2: 找出最近據點
    closest = None
    min_dist = float("inf")

    for row in data:
        try:
            unit_lat = float(row.get("LAT", 0))
            unit_lon = float(row.get("LON", 0))
        except:
            continue

        dist = haversine(lat, lon, unit_lat, unit_lon)

        if dist < min_dist:
            min_dist = dist
            closest = row

    if not closest:
        return {"error": "No valid UNIT location found"}

    # Step 3: 回傳結果 (只回 UNIT_NM 與 UNIT_ADDR，可加距離)
    return {
        "UNIT_NM": closest.get("UNIT_NM"),
        "UNIT_ADDR": closest.get("UNIT_ADDR"),
        "distance_km": round(min_dist, 2)
    }
