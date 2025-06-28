"""import httpx
from langchain_community.chat_models import ChatOpenAI

def fetch_crypto_prices(symbols):
    # For mock/demo, return fixed data
    mock_data = {"BTC": 68000, "ETH": 3600, "SOL": 160}
    return {symbol: mock_data.get(symbol, 0) for symbol in symbols}
"""
import requests
import json
from typing import List, Dict, Union
import time
import datetime

class CoinGeckoError(Exception):
    """Base exception for CoinGecko API errors"""
    pass

class CoinGeckoAPI:
    def __init__(self):
        self.base_url = 'https://api.coingecko.com/api/v3'

    def _make_request(self, endpoint: str, params: Dict = None) -> Union[Dict, List]:
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            if response.status_code != 200:
                raise CoinGeckoError(f"HTTP {response.status_code}: {response.text}")
            return response.json()
        except requests.RequestException as e:
            raise CoinGeckoError(f"Request Error: {str(e)}")

    def get_latest_quotes(self, coin_ids: List[str], vs_currency: str = 'usd') -> Dict:
        params = {
            'vs_currency': vs_currency,
            'ids': ','.join(coin_ids)
        }
        response = self._make_request('/coins/markets', params)
        result = {coin['symbol'].upper(): coin for coin in response}
        return result

    def _date_to_unix(self, year, month, day):
        dt = datetime.datetime(year, month, day)
        return int(time.mktime(dt.timetuple()))

    def get_market_chart_range(
        self, 
        coin_id: str, 
        from_date: tuple,  # e.g., (2025, 5, 1)
        to_date: tuple,    # e.g., (2025, 5, 31)
        vs_currency: str = 'usd'
    ) -> dict:
        from_ts = self._date_to_unix(*from_date)
        to_ts = self._date_to_unix(*to_date)

        params = {
            'vs_currency': vs_currency,
            'from': from_ts,
            'to': to_ts
        }
        response = self._make_request(f'/coins/{coin_id}/market_chart/range', params)
        return response

    def get_ohlcv_data(self, coin_id: str, vs_currency: str = 'usd', days: Union[int, str] = 30) -> List:
        params = {
            'vs_currency': vs_currency,
            'days': str(days)
        }
        response = self._make_request(f'/coins/{coin_id}/ohlc', params)
        return response

# Example usage
"""if __name__ == "__main__":
    api = CoinGeckoAPI()
    try:
        print("\n=== Current Prices ===")
        quotes = api.get_latest_quotes(['bitcoin', 'ethereum'])
        print(json.dumps(quotes, indent=2))

        print("\n=== Market Chart ===")
        data = api.get_market_chart_range(
            coin_id='bitcoin',
            from_date=(2025, 5, 1),
            to_date=(2025, 5, 31),
            vs_currency='usd'
        )
        print(data)

        print("\n=== OHLCV Data (BTC, past 7 days) ===")
        ohlcv = api.get_ohlcv_data('bitcoin', days=7)
        print(json.dumps(ohlcv, indent=2))

    except CoinGeckoError as e:
        print(f"API Error: {e}")"""