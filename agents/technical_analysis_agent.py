import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import os
from openai import OpenAI
from dotenv import load_dotenv

class TechnicalAnalysisAgent:
    def __init__(self, data_file: str = "data/crypto_data.json"):
        self.data_file = data_file
        self.data = self._load_data()
        self.top_coins = ["BTC", "ETH", "BNB", "SOL", "XRP", "USDC", "USDT", "ADA", "AVAX", "DOGE"]
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def _load_data(self) -> Dict:
        """Load crypto data from JSON file"""
        with open(self.data_file, 'r') as f:
            return json.load(f)
    
    def _get_last_7_days_data(self, coin: str) -> List[float]:
        """Get the last 7 days of price data for a specific coin"""
        if coin not in self.data:
            return []
        
        # Get the last 7 days of data from the market_chart.prices array
        # Each entry is [timestamp, price]
        prices = self.data[coin]["market_chart"]["prices"]
        # Extract just the price values (second element of each entry)
        return [price[1] for price in prices[-7:]]
    
    def _calculate_ma(self, prices: List[float], period: int) -> float:
        """Calculate Moving Average"""
        ma = np.mean(prices[-period:])
        print(f"Calculating {period}-day Moving Average: ${ma:.2f}")
        return ma
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            print("Not enough data for RSI calculation, defaulting to neutral (50.0)")
            return 50.0  # Default to neutral if not enough data
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            print("RSI calculation: No losses in period, RSI = 100.0")
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        print(f"Calculating RSI: {rsi:.1f} (Avg Gain: {avg_gain:.2f}, Avg Loss: {avg_loss:.2f})")
        return rsi
    
    def _identify_support_resistance(self, data: List[List[float]]) -> Tuple[float, float]:
        """Identify support and resistance levels"""
        lows = [candle[3] for candle in data]  # Low prices
        highs = [candle[2] for candle in data]  # High prices
        
        support = min(lows)
        resistance = max(highs)
        
        return support, resistance
    
    def _prepare_market_data(self, data: List[List[float]]) -> Dict:
        """Prepare market data in a format suitable for the LLM"""
        closes = [candle[4] for candle in data]
        volumes = [candle[5] if len(candle) > 5 else 0 for candle in data]
        
        return {
            "price": {
                "current": closes[-1],
                "historical": closes
            },
            "market_chart": {
                "price_trend": "up" if closes[-1] > closes[0] else "down",
                "volume_trend": "up" if volumes[-1] > volumes[0] else "down"
            },
            "ohlcv": {
                "open": [candle[1] for candle in data],
                "high": [candle[2] for candle in data],
                "low": [candle[3] for candle in data],
                "close": closes,
                "volume": volumes
            }
        }
    
    def _get_llm_analysis(self, coin: str, market_data: Dict) -> str:
        """Get analysis from OpenAI using the technical analysis prompt"""
        try:
            with open("prompts/technical_analysis.txt", "r") as f:
                prompt_template = f.read()
            
            # Prepare the prompt with market data
            prompt = prompt_template.format(
                coin=coin,
                price=market_data["price"],
                market_chart=market_data["market_chart"],
                ohlcv=market_data["ohlcv"]
            )
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a Technical Analysis Agent focused on short-term cryptocurrency price action."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating LLM analysis: {str(e)}"
    
    def analyze_coin(self, coin: str) -> Dict:
        """Analyze a single coin's data"""
        print(f"\n{'='*50}")
        print(f"Starting analysis for {coin}")
        print(f"{'='*50}")
        
        prices = self._get_last_7_days_data(coin)
        if not prices:
            print(f"No data available for {coin}")
            return {"error": f"No data available for {coin}"}
        
        print(f"\nPrice data for last 7 days:")
        for i, price in enumerate(prices):
            print(f"Day {i+1}: ${price:.2f}")
        
        # Calculate indicators
        print("\nCalculating technical indicators...")
        ma7 = self._calculate_ma(prices, 7)
        ma3 = self._calculate_ma(prices, 3)
        rsi = self._calculate_rsi(prices)
        
        # For support and resistance, use min and max of prices
        support = min(prices)
        resistance = max(prices)
        print(f"\nSupport/Resistance Levels:")
        print(f"Support: ${support:.2f}")
        print(f"Resistance: ${resistance:.2f}")
        
        # Prepare market data for LLM
        print("\nPreparing data for market analysis...")
        market_data = {
            "price": {
                "current": prices[-1],
                "historical": prices
            },
            "market_chart": {
                "price_trend": "up" if prices[-1] > prices[0] else "down",
                "volume_trend": "neutral"  # No volume data available
            },
            "ohlcv": {
                "close": prices,
                "volume": [0] * len(prices)  # No volume data available
            }
        }
        
        # Get LLM analysis
        print("\nGenerating market analysis...")
        llm_analysis = self._get_llm_analysis(coin, market_data)
        
        # Generate analysis
        analysis = {
            "coin": coin,
            "current_price": prices[-1],
            "indicators": {
                "ma7": ma7,
                "ma3": ma3,
                "rsi": rsi
            },
            "levels": {
                "support": support,
                "resistance": resistance
            },
            "llm_analysis": llm_analysis
        }
        
        print(f"\nAnalysis complete for {coin}")
        print(f"{'='*50}\n")
        return analysis
    
    def analyze_top_coins(self) -> List[Dict]:
        """Analyze all top coins"""
        analyses = []
        for coin in self.top_coins:
            analysis = self.analyze_coin(coin)
            if "error" not in analysis:
                analyses.append(analysis)
        return analyses

"""def main():
    print("Starting Technical Analysis Agent...")
    agent = TechnicalAnalysisAgent()
    analyses = agent.analyze_top_coins()
    print("\nTechnical Analysis Report (Past 7 Days)")
    print("=" * 50)
    
    for analysis in analyses:
        print(f"\n{analysis['coin']} Analysis:")
        print("-" * 30)
        print(analysis['llm_analysis'])
        print(f"\nTechnical Indicators:")
        print(f"Current Price: ${analysis['current_price']:.2f}")
        print(f"RSI: {analysis['indicators']['rsi']:.1f}")
        print(f"7-day MA: ${analysis['indicators']['ma7']:.2f}")
        print(f"Support: ${analysis['levels']['support']:.2f}")
        print(f"Resistance: ${analysis['levels']['resistance']:.2f}")

if __name__ == "__main__":
    main() """