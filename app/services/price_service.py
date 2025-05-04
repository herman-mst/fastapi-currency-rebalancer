import httpx
import pandas as pd
from datetime import datetime
from typing import List, Dict
import asyncio

COINGECKO_API = "https://api.coingecko.com/api/v3"
MAX_RETRIES = 3

async def _get_with_retries(client: httpx.AsyncClient, url: str, params: dict) -> httpx.Response:
    backoff = 10
    for attempt in range(1, MAX_RETRIES + 1):
        resp = await client.get(url, params=params, timeout=10.0)
        if resp.status_code == 429:
            # Too Many Requests: wait and retry
            await asyncio.sleep(backoff)
            backoff *= 2
            continue
        resp.raise_for_status()
        return resp
    # Last attempt
    resp.raise_for_status()
    return resp

async def fetch_current_prices(symbols: List[str], vs_currency: str = "usd") -> dict[str, float]:
    ids = ",".join(symbols)
    url = f"{COINGECKO_API}/simple/price"
    params = {"ids": ids, "vs_currencies": vs_currency}
    async with httpx.AsyncClient() as client:
        resp = await _get_with_retries(client, url, params)
        data = resp.json()
    return {sym: data.get(sym, {}).get(vs_currency, 0.0) for sym in symbols}

async def fetch_historical_prices(
    symbols: List[str],
    vs_currency: str = "usd",
    days: int = 30
) -> pd.DataFrame:
    tasks = []
    async with httpx.AsyncClient() as client:
        for sym in symbols:
            url = f"{COINGECKO_API}/coins/{sym}/market_chart"
            params = {"vs_currency": vs_currency, "days": days, "interval": "daily"}
            tasks.append(_get_with_retries(client, url, params))
        responses = await asyncio.gather(*tasks)

    data = {}
    for resp, sym in zip(responses, symbols):
        json_data = resp.json()
        prices = json_data.get("prices", [])
        dates = [datetime.utcfromtimestamp(p[0] / 1000).date() for p in prices]
        vals = [p[1] for p in prices]
        data[sym] = pd.Series(data=vals, index=dates)

    df = pd.DataFrame(data)
    return df
