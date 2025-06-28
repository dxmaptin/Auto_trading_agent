from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import os

llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def critic_node(state):
    plan = state["portfolio_plan"]
    prompt = f"Please review this portfolio: {plan} and suggest improvements."
    response = llm([HumanMessage(content=prompt)])
    state["portfolio_review"] = response.content
    return state