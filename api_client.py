import requests
import pandas as pd
import datetime
from typing import Tuple, Optional
import time
from functools import lru_cache

class PolygonAPIClient:
    def __init__(self):
        """Initialize the Polygon.io API client"""
        self.base_url = "https://api.polygon.io"
        self.api_key = None
        self._cache = {}
        
    def set_api_key(self, api_key: str) -> None:
        """Set the API key for requests"""
        self.api_key = api_key
    
    def _make_request(self, endpoint: str, params: dict) -> dict:
        """Make a request to the Polygon.io API with error handling"""
        if not self.api_key:
            raise ValueError("API key not set")
        
        params['apiKey'] = self.api_key
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching data from Polygon.io: {e}")
    
    def get_daily_data(self, ticker: str, period_days: int = 90) -> Tuple[pd.DataFrame, str]:
        """Fetch daily stock data for a given ticker"""
        cache_key = f"daily_{ticker}_{period_days}"
        
        # Check cache (simple time-based caching)
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < 3600:  # 1 hour cache
                return cached_data, ""
        
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=period_days)
        
        endpoint = f"/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{today}"
        params = {'adjusted': 'true', 'sort': 'asc', 'limit': 5000}
        
        try:
            data = self._make_request(endpoint, params)
            
            if not data.get('results'):
                return pd.DataFrame(), f"No daily data found for {ticker}."
            
            df = pd.DataFrame(data['results'])
            df.rename(columns={
                'o': 'Open', 'h': 'High', 'l': 'Low', 
                'c': 'Close', 'v': 'Volume', 't': 'Date'
            }, inplace=True)
            df['Date'] = pd.to_datetime(df['Date'], unit='ms').dt.date
            df.set_index('Date', inplace=True)
            
            # Cache the result
            self._cache[cache_key] = (df, time.time())
            
            return df, ""
            
        except Exception as e:
            return pd.DataFrame(), str(e)
    
    def get_weekly_data(self, ticker: str) -> Tuple[pd.DataFrame, str]:
        """Fetch weekly stock data for a given ticker"""
        cache_key = f"weekly_{ticker}"
        
        # Check cache
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < 3600:  # 1 hour cache
                return cached_data, ""
        
        today = datetime.date.today()
        one_year_ago = today - datetime.timedelta(days=365)
        
        endpoint = f"/v2/aggs/ticker/{ticker}/range/1/week/{one_year_ago}/{today}"
        params = {'sort': 'asc', 'limit': 5000}
        
        try:
            data = self._make_request(endpoint, params)
            
            if not data.get('results'):
                return pd.DataFrame(), f"No weekly data found for {ticker}."
            
            df = pd.DataFrame(data['results'])
            df.rename(columns={
                'o': 'Open', 'h': 'High', 'l': 'Low', 
                'c': 'Close', 'v': 'Volume', 't': 'Date'
            }, inplace=True)
            df['Date'] = pd.to_datetime(df['Date'], unit='ms').dt.date
            df.set_index('Date', inplace=True)
            
            # Cache the result
            self._cache[cache_key] = (df, time.time())
            
            return df, ""
            
        except Exception as e:
            return pd.DataFrame(), str(e)
    
    def get_current_price(self, ticker: str) -> Tuple[Optional[float], str]:
        """Fetch the current price for a ticker"""
        cache_key = f"price_{ticker}"
        
        # Check cache (shorter cache time for prices)
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < 600:  # 10 minute cache
                return cached_data, ""
        
        endpoint = f"/v2/aggs/ticker/{ticker}/prev"
        params = {}
        
        try:
            data = self._make_request(endpoint, params)
            
            if data.get('results') and data['results']:
                price = data['results'][0]['c']
                # Cache the result
                self._cache[cache_key] = (price, time.time())
                return price, ""
            else:
                return None, "Price not found."
                
        except Exception as e:
            return None, str(e)
    
    def get_next_earnings_date(self, ticker: str) -> Tuple[Optional[str], str]:
        """Fetch the next upcoming earnings date for a ticker"""
        cache_key = f"earnings_{ticker}"
        
        # Check cache (24 hour cache for earnings)
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < 86400:  # 24 hour cache
                return cached_data, ""
        
        endpoint = f"/v3/reference/tickers/{ticker}/events"
        params = {}
        
        try:
            data = self._make_request(endpoint, params)
            
            if not data.get('results'):
                return None, "No upcoming earnings found."
            
            # Look for earnings events
            results = data['results']
            if 'events' in results:
                events = results['events']
                earnings_events = [event for event in events if event.get('type') == 'earnings']
                
                if earnings_events:
                    # Sort by date and get the next one
                    earnings_events.sort(key=lambda x: x.get('date', ''))
                    next_earnings = earnings_events[0]['date']
                    # Cache the result
                    self._cache[cache_key] = (next_earnings, time.time())
                    return next_earnings, ""
            
            return None, "No upcoming earnings found."
            
        except Exception as e:
            return None, str(e)
    
    def clear_cache(self) -> None:
        """Clear the API cache"""
        self._cache.clear()