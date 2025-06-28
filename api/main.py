import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from graph.graph_builder import run_graph
import asyncio
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
load_dotenv() 

app = FastAPI()

@app.post("/portfolio")
async def get_portfolio(request: Request):
    body = await request.json()
    user_query = body.get("query", ["BTC", "ETH"])
    risk_profile = body.get("risk_profile", "moderate")

    result = await run_graph(user_query, risk_profile)
    return {"result": result}