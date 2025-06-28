from langgraph.graph import StateGraph
from state import State
from agents.price_fetcher import price_fetcher_node
from agents.technical_analysis_agent import technical_analysis_agent_node
from agents.portfolio_suggester import portfolio_suggestor_node

async def run_graph(user_query, risk_profile):
    graph = StateGraph(State)
    graph.add_node("price_fetcher", price_fetcher_node)
    graph.add_node("technical_analysis_agent", technical_analysis_agent_node)
    graph.add_node("portfolio_suggester", portfolio_suggestor_node)

    graph.set_entry_point("price_fetcher")
    graph.add_edge("price_fetcher", "technical_analysis_agent")
    graph.add_edge("technical_analysis_agent", "portfolio_suggester")
    graph.add_edge("portfolio_suggester", "END")

    # Compile the graph
    app = graph.compile()

    inputs = {"query": user_query, "risk_profile": risk_profile}
    result = await app.ainvoke(inputs)
    return result