from typing import TypedDict, Optional, Annotated, List
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[List, add_messages]
    crypto_prices: dict
    risk_profile: Optional[str]
    portfolio_plan: str
    portfolio_review: Optional[str]