from os import environ

from dotenv import load_dotenv
from langchain import hub
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.messages import HumanMessage
from langgraph.graph import START, StateGraph
from typing_extensions import Annotated, TypedDict


load_dotenv()


class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str


class QueryOutput(TypedDict):
    """Generated SQL query."""
    query: Annotated[str, ..., "Syntactically valid SQL query."]


uri = environ["SUPABASE_POST_URI"]
db = SQLDatabase.from_uri(uri)

llm = init_chat_model("gemini-2.0-flash-001", model_provider="google_vertexai")

query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

def write_query(state: State):
    """Generate SQL query to fetch information."""
    # Construct the prompt with the required 'contents' field
    prompt_value = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 10,
            "table_info": db.get_table_info(),
            "input": state["question"],
        }
    )
    print(db.get_table_info())
    structured_llm = llm.with_structured_output(QueryOutput)

    # Convert the prompt to a format that the model can understand
    prompt = ChatPromptValue(messages=[HumanMessage(content=prompt_value.to_string())])

    result = structured_llm.invoke(prompt)

    return {"query": result["query"]}


def execute_query(state: State):
    """Execute SQL query."""
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return {"result": execute_query_tool.invoke(state["query"])}


def generate_answer(state: State):
    """Answer question using retrieved information as context."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {state["question"]}\n'
        f'SQL Query: {state["query"]}\n'
        f'SQL Result: {state["result"]}'
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}


def process_question(question: str):
    graph_builder = StateGraph(State).add_sequence(
        [write_query, execute_query, generate_answer]
    )
    graph_builder.add_edge(START, "write_query")
    graph = graph_builder.compile()

    return [step for step in graph.stream({"question": "How many stores are there?"}, stream_mode="updates")]


print(process_question("How many stores are there?"))
