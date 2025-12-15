from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.retrievers import WikipediaRetriever
from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langgraph.checkpoint.memory import InMemorySaver
from .env import settings
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from prompts.background_search import BACKGROUND_SEARCH_PROMPT
from prompts.information_gatherer import INFOMRATION_GATHERER_PROMPT
from prompts.question_generator import QUESTION_GENERATOR_PROMPT
from prompts.validator import VALIDATOR_PROMPT
from prompts.conversation_agent import CONVERSATION_PROMPT
from .res_models import ResponseState, ValidatorOutputFormat, ConversationState
from newsapi import NewsApiClient
from datetime import date
from braintrust import init_logger, traced
from braintrust_langchain import BraintrustCallbackHandler, set_global_handler



init_logger(project="Prodapt", api_key=settings.BRAINTRUST_API_KEY)
handler = BraintrustCallbackHandler()
set_global_handler(handler)

@tool
def wikipedia_tool(query: str):
    """A tool that takes in a query and returns the relevant wikipedia article"""
    wiki_agent = WikipediaRetriever()
    docs = wiki_agent.invoke(query)
    return docs[0].page_content

@tool
def news_gatherer(query: str):
    """A tool that gathers news information based on the query provided"""
    newsapi = NewsApiClient(api_key=settings.NEWSAPI_API_KEY)
    all_articles = newsapi.get_everything(q=query)
    return all_articles


def validator_agent(state: ResponseState):
    """Gets the initial name and topic from the user and searches for them on the internet to ensure that the model finds details on the right person."""
    model = create_agent(
        model=ChatOpenAI(model="gpt-5-mini", api_key=settings.OPENAI_API_KEY).bind_tools(tools=[{"type": "web_search"}, wikipedia_tool]),
        response_format=ProviderStrategy(ValidatorOutputFormat)
    )
    chat_prompt = ChatPromptTemplate.from_template(VALIDATOR_PROMPT)
    prompt = chat_prompt.invoke({"person_name": state['name'], "one_liner": state['one_liner'], "additional_info": state['issues']}).to_messages()
    res = model.invoke({"messages": prompt})

    return {"updated_name": res['structured_response'].name, "updated_desc": res['structured_response'].desc}

def interrupter(state: ResponseState):
    """Interrupter node to verify the details gathered by the validator agent"""
    is_correct = interrupt({
        "name": state['updated_name'],
        "desc": state['updated_desc']
    })

    if is_correct['isValid']:
        return ["background_search_agent", "information_gatherer_agent"]
    else:
        state['issues'] = is_correct['issues']
        return "validator_agent"

def background_search_agent(state: ResponseState):
    model = ChatOpenAI(model="gpt-5-mini", api_key=settings.OPENAI_API_KEY).bind_tools(tools=[{"type": "web_search"}, wikipedia_tool])
    prompt = ChatPromptTemplate.from_template(BACKGROUND_SEARCH_PROMPT)
    chain = prompt | model
    res = chain.invoke({"person_name": state['updated_name'], "person_one_liner": state['updated_desc']})
    return {"background_info": res.content}

def information_gatherer_agent(state: ResponseState):
    model = ChatOpenAI(model="gpt-5.2", api_key=settings.OPENAI_API_KEY).bind_tools(tools=[{"type": "web_search"}, wikipedia_tool, news_gatherer])
    prompt = ChatPromptTemplate.from_template(INFOMRATION_GATHERER_PROMPT)
    chain = prompt | model
    res = chain.invoke({"person_name": state['updated_name'], "person_one_liner": state['one_liner']})
    return {"topic_information": res.content}

def question_generation_agent(state: ResponseState):
    model = ChatOpenAI(model="gpt-5-mini", api_key=settings.OPENAI_API_KEY)
    prompt = ChatPromptTemplate.from_template(QUESTION_GENERATOR_PROMPT)
    chain = prompt | model
    res = chain.invoke({"background_info": state['background_info'], "topic": state['updated_desc'], "information": state['topic_information'], "current_date": str(date.today().strftime("%Y-%m-%d"))})
    return {"question_generator": res.content}

workflow = StateGraph(ResponseState)

workflow.add_node(validator_agent, "validator_agent")
workflow.add_node(interrupter, "interrupter")
workflow.add_node(background_search_agent, "background_search_agent")
workflow.add_node(information_gatherer_agent, "information_gatherer_agent")
workflow.add_node(question_generation_agent, "question_generation_agent")

workflow.add_edge(START, "validator_agent")
workflow.add_conditional_edges("validator_agent", interrupter)
workflow.add_edge("background_search_agent", "question_generation_agent")
workflow.add_edge("information_gatherer_agent", "question_generation_agent")
workflow.add_edge("question_generation_agent", END)


checkpointer = InMemorySaver()
agent = workflow.compile(checkpointer=checkpointer)

@traced(name="Journalist Question Generator")
def invoke_researcher(thread_id: str, resume_val: dict, name: str = "", one_liner: str = ""):
    config = {"configurable": {"thread_id": thread_id}}
    if not resume_val:
        res = agent.invoke({"name": name, "one_liner": one_liner, "issues": ""}, config=config)
    else: 
        res = agent.invoke(Command(resume=resume_val), config=config)
    return res


"""==========CONVERSATION AGENT=========="""



def conversation_agent(state: ConversationState):
    model = ChatOpenAI(model="gpt-5-mini", api_key=settings.OPENAI_API_KEY)
    prompt = ChatPromptTemplate.from_template(CONVERSATION_PROMPT).invoke({}).to_string()
    full_msgs = [SystemMessage(content=prompt)] + state["messages"]
    res = model.invoke(full_msgs)
    return {"messages": AIMessage(content=res.content)}

ConversationGraph = StateGraph(ConversationState)

ConversationGraph.add_node("conversation_agent", conversation_agent)
ConversationGraph.set_entry_point("conversation_agent")
ConversationGraph.add_edge("conversation_agent", END)

convo_checkpointer = InMemorySaver()
convo_agent = ConversationGraph.compile(checkpointer=convo_checkpointer)

@traced(name="Conversation Agent")
def invoke_conversation(thread_id: str, message: str):
    config = {"configurable": {"thread_id": thread_id}}
    res = convo_agent.invoke({"messages": [HumanMessage(content=message)]}, config=config)
    return res
