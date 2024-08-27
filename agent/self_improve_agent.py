# %%
from email import message
import getpass
import os
from pyexpat.errors import messages


def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")

_set_if_undefined("LANGCHAIN_API_KEY")

# Optional, add tracing in LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Self Improvement"

# %% [markdown]
# # Tools

# %%
from utils.tools import construct_tools, get_tools_descriptions
from langgraph.prebuilt import ToolNode

tools = construct_tools()
tools_descriptions = get_tools_descriptions(tools)
tool_node = ToolNode(tools)
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

llm = ChatOpenAI(temperature=0, model="gpt-4o-mini", base_url="https://api.chsdw.top/v1", top_p=1)
claude = ChatOpenAI(temperature=0, model="claude-3-haiku-20240307", timeout=None, base_url="https://api.chsdw.top/v1", top_p=1, api_key="sk-4CWpQEDH29gILTbO95D722AdE9A64a52A6Ab212bA95e64Da")
# %% [markdown]
# # Define State

# %%
from typing import Literal
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

MAX_ITERATIONS = 4

class State(TypedDict):
    input: str
    critique: Annotated[list[str], add]
    messages: list
    final_answer: Annotated[list[str], add]
    iteration: int

# %% [markdown]
# # Define Reacter

# %%
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage,HumanMessage

react_prompt = ChatPromptTemplate.from_messages([
    ("system", "Identify all the candidate tools you may need to use and the corresponding tool input text based on the user's current step. "
     "Always remmeber that there may be multiple tools that can be used to complete a step! So if there are more than one tool that can be used, "
     "your response should contain multiple tools and their inputs. Make sure that the current step is completed before moving to the next step. "
     "Always remember to check if the information you need is already present in the previous conversation when you need to call the tool!")
    #  "You have access to the following tools:\n\n"
    #  "{tools_descriptions}\n\n")
     ])

react_prompt = react_prompt.format(tools_descriptions=tools_descriptions)

reacter = create_react_agent(model=llm, tools=tools, state_modifier=SystemMessage(content=react_prompt))

def react(state):
    if state["critique"]:
        inputs = {"messages": state["messages"] + [HumanMessage(content="Based on the previous critique, answer the question again. ")]}
        result = reacter.invoke(input=inputs, config={"recursion_limit": 20})
    else:
        inputs = {"messages": [("user", state["input"])]}
        result = reacter.invoke(input=inputs, config={"recursion_limit": 20})
    return {
        "messages": result["messages"]
    }

# %% [markdown]
# # Define Critic

# %%
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage

# critic_prompt = ("Inspect the previous messages and identify any potential issues or errors. "
#                  "Is the selection of tools calling reasnonable? "
#                  "Check the input to the tools step by step. "
#                  "Is the final answer truthful?"
#                  "And give a better solution or input to the tools. \n"
#                  "Your response should be no more than 250 words. ")



critic_prompt = ("Briefly summarize the plan and actions taken to solve the problem <{question}>in the previous message, "
                 "then identify potential errors and unreasonable areas. Provide a better solution plan! Your response should be as concise as possible.")

final_answer_prompt = ("Based on the conversation, provide the final answer to the user's question. "
                       "{question} \n"
                       "The final answer should be a number or phrase, not a sentence. Follow the format: \n"
                       "FINAL ANSWER: <answer> \n")

def criticize(state):
    final_answer = llm.invoke(state["messages"] + [HumanMessage(content=final_answer_prompt.format(question=state["input"]))])
    if not (len(state["critique"]) == 3 or len(state["final_answer"]) > 0 and state["final_answer"][-1] == final_answer.content.split("FINAL ANSWER:")[-1].strip()):
        critique = llm.invoke(state["messages"] + [HumanMessage(content=critic_prompt.format(question=state["input"]))])
    if "critique" in locals():
        return {
            "critique": [critique.content],
            "final_answer": [final_answer.content.split("FINAL ANSWER:")[-1].strip()],
            "iteration": 1 if not state["iteration"] else state["iteration"] + 1 ,
            "messages": state["messages"] + [HumanMessage(content=critic_prompt), critique]
        }
    else:
        return {
            "final_answer": [final_answer.content.split("FINAL ANSWER:")[-1].strip()],
            "iteration": 1 if not state["iteration"] else state["iteration"] + 1 ,
            "messages": state["messages"] + [HumanMessage(content=critic_prompt)]
        }
    
# Either agent can decide to end
from typing import Literal

def should_end(state) -> Literal["react", "__end__"]:
    if state["iteration"] >= MAX_ITERATIONS or len(state["final_answer"]) > 1 and state["final_answer"][-1] == state["final_answer"][-2]:
        return "__end__"
    else:
        return "react"


# %% [markdown]
# # Construct Graph

# %%
builder = StateGraph(State)

builder.add_node("react", react)
builder.add_node("critic", criticize)

builder.add_edge(START, "react")
builder.add_edge("react", "critic")

builder.add_conditional_edges("critic", should_end)

graph = builder.compile()


