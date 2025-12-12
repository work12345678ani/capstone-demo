from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from .env import settings
from prompts.search import BASIC_SEARCH_PROMPT

agent = create_agent(
    model=ChatOpenAI(model="gpt-5-mini", api_key=settings.OPENAI_API_KEY).bind_tools(tools=[{"type": "web_search"}]),
    system_prompt=BASIC_SEARCH_PROMPT,
)