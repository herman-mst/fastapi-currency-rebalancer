import httpx
from typing import List, Dict

COINGECKO_API = "https://api.coingecko.com/api/v3"

async def fetch_current_prices(symbols: List[str], vs_currency: str = "usd") -> Dict[str, float]:
    """
    Получить текущие цены по списку тикеров из CoinGecko.
    symbols: список id CoinGecko, например ["bitcoin", "ethereum"]
    vs_currency: базовая валюта ("usd")
    """
    ids = ",".join(symbols)
    url = f"{COINGECKO_API}/simple/price"
    params = {"ids": ids, "vs_currencies": vs_currency}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    return {sym: data.get(sym, {}).get(vs_currency, 0.0) for sym in symbols}

