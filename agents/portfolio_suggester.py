from datetime import datetime
import json
import os
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

def portfolio_suggestor_node(state: Dict) -> Dict:
    """
    LangGraph node for suggesting portfolio allocations based on technical analysis and current prices.
    
    Args:
        state: Current state containing:
            - technical_analysis: List of technical analysis results for each coin
            - crypto_prices: Dictionary of symbol to price mappings
            - risk_profile: Optional string indicating user's risk tolerance
            - messages: List of conversation messages
            
    Returns:
        Updated state with:
            - portfolio_plan: Dictionary containing portfolio recommendations
            - error: Optional error message
            - metadata: Additional information about the analysis
            - messages: Updated list of messages
    """
    try:
        # Get required data from state
        technical_analysis = state.get('technical_analysis', [])
        prices = state.get('crypto_prices', {})
        risk_profile = state.get('risk_profile', 'moderate')  # Default to moderate risk
        
        if not technical_analysis or not prices:
            raise ValueError("No technical analysis or price data available for portfolio suggestions")
        
        # Initialize LLM
        llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7
        )
        
        # Load prompt
        with open("../prompts/portfolio_suggestor.txt", "r") as f:
            system_prompt = f.read()
        
        # Format technical analysis data for the prompt
        analysis_summary = "\nTechnical Analysis Summary:\n"
        for analysis in technical_analysis:
            coin = analysis['coin']
            analysis_summary += f"\n{coin}:\n"
            analysis_summary += f"- Current Price: ${analysis['current_price']:.2f}\n"
            analysis_summary += f"- RSI: {analysis['indicators']['rsi']:.1f}\n"
            analysis_summary += f"- 7-day MA: ${analysis['indicators']['ma7']:.2f}\n"
            analysis_summary += f"- Support: ${analysis['levels']['support']:.2f}\n"
            analysis_summary += f"- Resistance: ${analysis['levels']['resistance']:.2f}\n"
            analysis_summary += f"- Analysis: {analysis['llm_analysis']}\n"
        
        human_prompt = f"""
        Technical Analysis and Market Data:
        {analysis_summary}
        
        Current cryptocurrency prices:
        {json.dumps(prices, indent=2)}
        
        User's risk profile: {risk_profile}
        
        Based on the technical analysis and current market conditions, please provide:
        1. A detailed portfolio allocation recommendation
        2. Risk assessment for each suggested allocation
        3. Entry and exit points based on technical levels
        4. Portfolio diversification strategy
        5. Suggested holding period
        """
        
        # Create messages
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        # Get LLM response
        response = llm.invoke(messages)
        
        # Create portfolio message
        portfolio_message = {
            "role": "assistant",
            "content": response.content
        }
        
        # Update state with portfolio plan and message
        return {
            'portfolio_plan': {
                'analysis': response.content,
                'timestamp': datetime.now().isoformat(),
                'technical_analysis': technical_analysis,
                'prices_analyzed': prices,
                'risk_profile': risk_profile
            },
            'error': None,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'model': 'gpt-4-turbo-preview',
                'risk_profile': risk_profile,
                'coins_analyzed': [analysis['coin'] for analysis in technical_analysis]
            },
            'messages': [portfolio_message]
        }
        
    except Exception as e:
        # Create error message
        error_message = {
            "role": "assistant",
            "content": f"I encountered an error while generating portfolio suggestions: {str(e)}"
        }
        
        # Handle any errors and update state accordingly
        return {
            'portfolio_plan': {},
            'error': str(e),
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'error_type': type(e).__name__
            },
            'messages': [error_message]
        } 