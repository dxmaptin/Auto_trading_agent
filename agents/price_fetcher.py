from datetime import datetime, timedelta
import json
import os
import sys
import time
from typing import Dict, Any

# Get the absolute path to the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.crypto_price_api import CoinGeckoAPI

# Mapping of common symbols to CoinGecko IDs
COIN_MAPPING = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'SOL': 'solana',
    'USDT': 'tether',
    'BNB': 'binancecoin',
    'XRP': 'ripple',
    'ADA': 'cardano',
    'DOGE': 'dogecoin',
    'DOT': 'polkadot',
    'AVAX': 'avalanche-2'
}

# Valid data types
VALID_DATA_TYPES = ["price", "market_chart", "ohlcv"]

# Maximum number of retries for rate limit errors
MAX_RETRIES = 3
# Sleep time in seconds when rate limit is hit
RATE_LIMIT_SLEEP = 65

def save_to_json(data: Dict[str, Any], filename: str = "crypto_data.json") -> str:
    """Save data to a JSON file in the data directory"""
    try:
        # Create data directory if it doesn't exist
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        filepath = os.path.join(data_dir, filename)
        
        # If file exists, load existing data and update it
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    existing_data = json.load(f)
                    # Deep merge the new data with existing data
                    if isinstance(existing_data, dict) and isinstance(data, dict):
                        for symbol, symbol_data in data.items():
                            if symbol not in existing_data:
                                existing_data[symbol] = {}
                            if isinstance(symbol_data, dict):
                                existing_data[symbol].update(symbol_data)
                            else:
                                existing_data[symbol] = symbol_data
                        data = existing_data
            except json.JSONDecodeError:
                print(f"Warning: Could not parse existing data file {filepath}. Starting fresh.")
            except Exception as e:
                print(f"Warning: Error reading existing data file: {str(e)}. Starting fresh.")
        
        # Save the data
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    except Exception as e:
        print(f"Error saving data to JSON: {str(e)}")
        return ""

def load_existing_data(filename: str = "crypto_data.json") -> Dict[str, Any]:
    """Load existing data from JSON file"""
    try:
        filepath = os.path.join(project_root, "data", filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse data file {filepath}. Starting fresh.")
            except Exception as e:
                print(f"Warning: Error reading data file: {str(e)}. Starting fresh.")
        return {}
    except Exception as e:
        print(f"Error loading existing data: {str(e)}")
        return {}

def handle_rate_limit(func):
    """Decorator to handle rate limit errors with retries"""
    def wrapper(*args, **kwargs):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Rate Limit" in error_str:
                    retries += 1
                    if retries < MAX_RETRIES:
                        print(f"Rate limit hit. Retrying in {RATE_LIMIT_SLEEP} seconds... (Attempt {retries}/{MAX_RETRIES})")
                        time.sleep(RATE_LIMIT_SLEEP)
                        continue
                raise e
        return None
    return wrapper

@handle_rate_limit
def fetch_with_retry(api, method, **kwargs):
    """Helper function to fetch data with retry logic"""
    if method == "price":
        return api.get_latest_quotes(**kwargs)
    elif method == "market_chart":
        return api.get_market_chart_range(**kwargs)
    elif method == "ohlcv":
        return api.get_ohlcv_data(**kwargs)
    raise ValueError(f"Invalid method: {method}")

def get_coin_id(symbol):
    """Convert symbol to CoinGecko coin ID"""
    coin_id = COIN_MAPPING.get(symbol.upper(), symbol.lower())
    if coin_id not in COIN_MAPPING.values():
        raise ValueError(f"Invalid cryptocurrency symbol: {symbol}")
    return coin_id

def validate_date_range(date_range):
    """Validate date range format and values"""
    if not isinstance(date_range, tuple) or len(date_range) != 2:
        raise ValueError("date_range must be a tuple of (from_date, to_date)")
    
    from_date, to_date = date_range
    if not all(isinstance(d, tuple) and len(d) == 3 for d in [from_date, to_date]):
        raise ValueError("Dates must be tuples of (year, month, day)")
    
    # Convert to datetime objects for easier comparison
    try:
        from_dt = datetime(*from_date)
        to_dt = datetime(*to_date)
    except ValueError as e:
        raise ValueError(f"Invalid date format: {str(e)}")
    
    # Check if dates are in the past
    now = datetime.now()
    if from_dt > now or to_dt > now:
        raise ValueError("Cannot request data for future dates")
    
    # Check if from_date is before to_date
    if from_dt > to_dt:
        raise ValueError("from_date must be before to_date")
    
    # Check if date range is within 365 days
    max_range = timedelta(days=365)
    if to_dt - from_dt > max_range:
        raise ValueError("Date range cannot exceed 365 days")
    
    # Check if from_date is not more than 365 days ago
    min_date = now - max_range
    if from_dt < min_date:
        raise ValueError("Cannot request data from more than 365 days ago")

def validate_days(days):
    """Validate days parameter for OHLCV data"""
    if isinstance(days, str):
        if days not in ['1', '7', '14', '30', '90', '180', '365']:
            raise ValueError("days must be one of: 1, 7, 14, 30, 90, 180, 365")
    elif isinstance(days, int):
        if days not in [1, 7, 14, 30, 90, 180, 365]:
            raise ValueError("days must be one of: 1, 7, 14, 30, 90, 180, 365")
    else:
        raise ValueError("days must be an integer or string")

def price_fetcher_node(state):
    """
    LangGraph node for fetching cryptocurrency data.
    
    Args:
        state: Current state containing:
            - query: List of cryptocurrency symbols to fetch data for (defaults to top 10 coins)
            - data_type: Type of data to fetch ('price', 'market_chart', 'ohlcv')
            - date_range: Optional tuple of (from_date, to_date) for historical data
            - days: Optional number of days for OHLCV data
            - messages: List of conversation messages
            
    Returns:
        Updated state with:
            - crypto_data: Dictionary containing the requested data
            - error: Optional error message
            - metadata: Additional information about the request
            - messages: Updated list of messages
            - data_file: Path to the JSON file containing the data
    """
    try:
        # Get parameters from state, default to top 10 coins if not specified
        symbols = state.get("query", list(COIN_MAPPING.keys()))
        days = state.get("days", 7)  # Default to 7 days
        
        print(f"\nStarting price fetcher with:")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Days: {days}")
        
        # Initialize API client
        api = CoinGeckoAPI()
        
        # Load existing data
        print("\nLoading existing data...")
        result = load_existing_data()
        print(f"Loaded data for {len(result)} symbols")
        
        errors = []
        processed_symbols = set()
        
        # Convert symbols to coin IDs and validate
        coin_ids = []
        for symbol in symbols:
            try:
                coin_id = get_coin_id(symbol)
                coin_ids.append(coin_id)
            except ValueError as e:
                errors.append(f"Invalid symbol in query: {str(e)}")
        
        # Calculate date range for last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_range = ((start_date.year, start_date.month, start_date.day),
                     (end_date.year, end_date.month, end_date.day))
        
        # Process each coin
        for symbol, coin_id in zip(symbols, coin_ids):
            print(f"\nProcessing {symbol} ({coin_id})...")
            
            # Initialize data structure for this coin if it doesn't exist
            if symbol not in result:
                result[symbol] = {}
            
            # 1. Fetch price data
            try:
                print(f"Fetching price data for {symbol}...")
                price_data = fetch_with_retry(api, "price", coin_ids=[coin_id], vs_currency='usd')
                if price_data and coin_id in price_data:
                    result[symbol]['price'] = price_data[coin_id]
                    print(f"✓ Price data fetched for {symbol}")
                    # Save after each successful data type fetch
                    save_to_json(result)
                else:
                    errors.append(f"No price data found for {symbol}")
            except Exception as e:
                errors.append(f"Error fetching price data for {symbol}: {str(e)}")
            
            # 2. Fetch market chart data
            try:
                print(f"Fetching market chart data for {symbol}...")
                chart_data = fetch_with_retry(
                    api, 
                    "market_chart",
                    coin_id=coin_id,
                    from_date=date_range[0],
                    to_date=date_range[1],
                    vs_currency='usd'
                )
                if chart_data:
                    result[symbol]['market_chart'] = chart_data
                    print(f"✓ Market chart data fetched for {symbol}")
                    # Save after each successful data type fetch
                    save_to_json(result)
                else:
                    errors.append(f"No market chart data found for {symbol}")
            except Exception as e:
                errors.append(f"Error fetching market chart data for {symbol}: {str(e)}")
            
            # 3. Fetch OHLCV data
            try:
                print(f"Fetching OHLCV data for {symbol}...")
                ohlcv_data = fetch_with_retry(
                    api,
                    "ohlcv",
                    coin_id=coin_id,
                    vs_currency='usd',
                    days=days
                )
                if ohlcv_data:
                    result[symbol]['ohlcv'] = ohlcv_data
                    print(f"✓ OHLCV data fetched for {symbol}")
                    # Save after each successful data type fetch
                    save_to_json(result)
                else:
                    errors.append(f"No OHLCV data found for {symbol}")
            except Exception as e:
                errors.append(f"Error fetching OHLCV data for {symbol}: {str(e)}")
            
            processed_symbols.add(symbol)
            
            # Add a small delay between coins to avoid rate limits
            time.sleep(1)
        
        # Create response message
        message_content = f"Data retrieved for {len(processed_symbols)} out of {len(symbols)} cryptocurrencies.\n"
        if processed_symbols:
            message_content += f"Successfully processed: {', '.join(sorted(processed_symbols))}\n"
        if errors:
            message_content += f"\nErrors:\n" + "\n".join(errors)
        
        response_message = {
            "role": "assistant",
            "content": message_content
        }
        
        # Final save of all data
        data_file = save_to_json(result)
        
        # Update state with data, metadata, and message
        return {
            'crypto_data': result,
            'error': None if not errors else "\n".join(errors),
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'source': 'CoinGecko',
                'symbols': symbols,
                'processed_symbols': list(processed_symbols),
                'coin_ids': coin_ids,
                'errors': errors if errors else None,
                'data_file': data_file
            },
            'messages': [response_message]
        }
        
    except Exception as e:
        # Create error message
        error_message = {
            "role": "assistant",
            "content": f"I encountered an error while fetching cryptocurrency data: {str(e)}"
        }
        
        # Handle any errors and update state accordingly
        return {
            'crypto_data': result if 'result' in locals() else {},
            'error': str(e),
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'error_type': type(e).__name__,
                'symbols': symbols if 'symbols' in locals() else None,
                'processed_symbols': list(processed_symbols) if 'processed_symbols' in locals() else []
            },
            'messages': [error_message]
        }

def test_price_fetcher():
    """Test the price fetcher with default settings"""
    # Create a test state with default values
    test_state = {
        "messages": []  # Empty messages list as we're testing default behavior
    }
    
    # Call the price fetcher node
    result = price_fetcher_node(test_state)
    
    # Print the results in a readable format
    print("\n=== Price Fetcher Test Results ===")
    print("\nMetadata:")
    print(f"Timestamp: {result['metadata']['timestamp']}")
    print(f"Symbols: {', '.join(result['metadata']['symbols'])}")
    print(f"Processed Symbols: {', '.join(result['metadata']['processed_symbols'])}")
    print(f"Data File: {result['metadata'].get('data_file', 'No file saved')}")
    
    print("\nCrypto Data Summary:")
    for symbol, data in result['crypto_data'].items():
        print(f"\n{symbol}:")
        if isinstance(data, dict):
            for data_type, type_data in data.items():
                print(f"  {data_type}:")
                if isinstance(type_data, list):
                    print(f"    Number of data points: {len(type_data)}")
                    if type_data:
                        print(f"    First data point: {type_data[0]}")
                        print(f"    Last data point: {type_data[-1]}")
                else:
                    print(f"    Data: {type_data}")
        else:
            print(f"Data type: {type(data)}")
            print(f"Data: {data}")
    
    if result['error']:
        print("\nErrors:")
        print(result['error'])
    
    print("\nMessage Content:")
    print(result['messages'][0]['content'])

if __name__ == "__main__":
    test_price_fetcher()