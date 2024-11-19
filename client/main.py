from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# josh's tools
from toolbox import get_id_for_username, get_recent_tweets, post_to_linkedin


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)

tools = [get_id_for_username, get_recent_tweets, post_to_linkedin]
model = ChatOpenAI(model="gpt-4o")
graph = create_react_agent(model, tools=tools)

user_query = input("Enter your query: ")
inputs = {"messages": [
    ("user", user_query)]}
for s in graph.stream(inputs, stream_mode="values"):
    message = s["messages"][-1]
    if isinstance(message, tuple):
        print(message)
    else:
        message.pretty_print()
