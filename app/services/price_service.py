import httpx
import pandas as pd
from datetime import datetime
import asyncio

COINGECKO_API = "https://api.coingecko.com/api/v3"
MAX_RETRIES = 3

async def _get_with_retries(client: httpx.AsyncClient, url: str, params: dict) -> httpx.Response:
    """
    Perform an HTTP GET request with retry logic for handling rate-limiting responses.

    Args:
        client (httpx.AsyncClient): The HTTP client to use for making the request.
        url (str): The URL to send the GET request to.
        params (dict): Query parameters to include in the request.

    Returns:
        httpx.Response: The HTTP response object.

    Raises:
        httpx.HTTPStatusError: If the response status code is not successful after retries.
    """
    backoff = 10
    for _ in range(1, MAX_RETRIES + 1):
        resp = await client.get(url, params=params, timeout=10.0)
        # TODO: как-то решить проблему с rate limit
        if resp.status_code == 429:
            await asyncio.sleep(backoff)
            backoff *= 2
            continue
        resp.raise_for_status()
        return resp
    resp.raise_for_status()
    return resp

async def fetch_current_prices(symbols: list[str], vs_currency: str = "usd") -> dict[str, float]:
    """
    Fetch the current prices of the specified cryptocurrency symbols in the given currency.

    Args:
        symbols (list[str]): A list of cryptocurrency symbols (e.g., ["bitcoin", "ethereum"]).
        vs_currency (str, optional): The target currency to convert the prices into. Defaults to "usd".

    Returns:
        dict[str, float]: A dictionary mapping each cryptocurrency symbol to its current price 
                          in the specified currency. If a symbol's price is unavailable, its value 
                          will default to 0.0.
    """
    ids = ",".join(symbols)
    url = f"{COINGECKO_API}/simple/price"
    params = {"ids": ids, "vs_currencies": vs_currency}
    async with httpx.AsyncClient() as client:
        resp = await _get_with_retries(client, url, params)
        data = resp.json()
    return {sym: data.get(sym, {}).get(vs_currency, 0.0) for sym in symbols}

async def fetch_historical_prices(symbols: list[str], vs_currency: str = "usd", days: int = 30) -> pd.DataFrame:
    """
    Fetch historical price data for a list of cryptocurrency symbols.
    This function retrieves historical price data for the specified cryptocurrencies
    over a given number of days, using the CoinGecko API. The data is returned as a
    pandas DataFrame, where each column corresponds to a cryptocurrency symbol, and
    the rows represent daily prices indexed by date.
    Args:
        symbols (list[str]): A list of cryptocurrency symbols (e.g., ["bitcoin", "ethereum"]).
        vs_currency (str, optional): The currency to compare against (default is "usd").
        days (int, optional): The number of days of historical data to fetch (default is 30).
    Returns:
        pd.DataFrame: A pandas DataFrame containing historical price data. Each column
        corresponds to a cryptocurrency symbol, and the rows are indexed by date.
    Raises:
        httpx.HTTPError: If there is an issue with the HTTP request to the CoinGecko API.
        ValueError: If the response from the API does not contain valid price data.
    """
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
