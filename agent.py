from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from typing import Union
import os
import json

# Criação do agente com built-in tools para procurar informações sobre a partida nos JSONs


def create_match_agent(match_info: Union[dict, str], events: str, player_stats: str, lineups: str):
    @tool
    def get_match_info(input_str: str = "get_data") -> str:
        """Get general information about the match including teams, score, date, and venue"""
        if isinstance(match_info, dict):
            return json.dumps(match_info, indent=2, ensure_ascii=False)
        return str(match_info)

    @tool
    def get_match_events(input_str: str = "get_data") -> str:
        """Get chronological events of the match including passes, shots, and other actions"""
        return str(events)

    @tool
    def get_player_statistics(input_str: str = "get_data") -> str:
        """Get detailed statistics for all players in the match"""
        return str(player_stats)

    @tool
    def get_team_lineups(input_str: str = "get_data") -> str:
        """Get the starting lineups and formations for both teams"""
        return str(lineups)

    tools = [
        Tool.from_function(
            func=get_match_info,
            name="Match Info",
            description="Returns general match information such as score, teams, and date"
        ),
        Tool.from_function(
            func=get_match_events,
            name="Match Events",
            description="Returns match events including goals, shots, and other occurrences"
        ),
        Tool.from_function(
            func=get_player_statistics,
            name="Player Stats",
            description="Returns detailed statistics for all players in the match"
        ),
        Tool.from_function(
            func=get_team_lineups,
            name="Team Lineups",
            description="Returns the starting lineups and formations for both teams"
        ),
    ]

    tool_names = [tool.name for tool in tools]

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.1,
        google_api_key=os.getenv('GEMINI_API_KEY')
    )

    prompt = PromptTemplate(
        template="""You are a football analyst analyzing the following match:
    {context}

    Instructions:
    1. Use the available tools to analyze the match data
    2. Always use "get_data" as Action Input
    3. The returned data will be in JSON format
    4. Analyze the JSON data carefully before responding
    5. Always respond in clear and objective English

    Available tools:
    {tools}

    Follow this format EXACTLY:

    Question: {input}
    Thought: [your reasoning in English]
    Action: [one of the options: {tool_names}]
    Action Input: get_data
    Observation: [result]
    Thought: [analysis of the result in English]
    Final Answer: [final answer in English]

    Current question:
    {input}

    {agent_scratchpad}""",
        input_variables=["context", "input", "agent_scratchpad", "tools"],
        partial_variables={"tool_names": ", ".join(tool_names)}
    )

    agent = create_react_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=3,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )
