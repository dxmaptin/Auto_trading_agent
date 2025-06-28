🚀 Overview

This repository contains a modular, multi-agent trading bot designed to collect user preferences, fetch market data, perform technical and sentiment analysis, and generate risk-adjusted portfolio recommendations. Each “agent” component can be mixed, matched, or extended to fit your own strategy.

Key Features
	•	User Intake Agent
Gathers and normalizes investor profile (budget, risk tolerance, time horizon).
	•	Price Fetcher Agent
Retrieves real-time and historical OHLCV data via the CoinGecko API.
	•	Technical Analysis Agent
Calculates indicators (MA, RSI, MACD) and generates trend/volatility signals.
	•	Sentiment Analysis Agent
(Optional) Scrapes news and social feeds to gauge market mood.
	•	Portfolio Suggestion Agent
Combines signals and user profile to propose an optimized allocation.
	•	Critic Agent
Validates the proposed portfolio against original requirements and flags risks.

Tech Stack
	•	Language: Python 3.10+
	•	Framework: LangChain for chaining LLM calls and managing agent workflows
	•	Data: CoinGecko API for market data; optional news/sentiment APIs
	•	Indicators: TA-Lib / pandas_ta for technical metrics
	•	LLM: OpenAI (or compatible) for natural-language prompts and reasoning
 
Quick Start
1.	Clone the repo
```
git clone https://github.com/dxmaptin/Auto_trading_agent.git
cd crypto-trading-bot
```
2.	Install dependencies
```
pip install -r requirements.txt
```
3.	Configure your API keys
```
Set COINGECKO_API_KEY
Set OPENAI_API_KEY
```


