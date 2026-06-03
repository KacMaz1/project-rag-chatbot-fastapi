from dotenv import load_dotenv
import os
from typing import TypedDict, Annotated, Sequence

from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.types import interrupt, Command
from langgraph.prebuilt import ToolNode

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.tools import tool

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings

from langgraph_azure_sql_db_checkpoint import AzureSQLCheckpointSaver


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

model = ChatOllama(
    model="gemma4:e4b",
    temperature=0.0,
    reasoning=False,
)

embeddings = OllamaEmbeddings(
    model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
)

persist_directory = os.path.join(BASE_DIR, "stock_market_db")
collection_name = "stock_market_db"

os.makedirs(persist_directory, exist_ok=True)

db_file = os.path.join(persist_directory, "chroma.sqlite3")

if os.path.exists(db_file):
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )
else:
    pdf_path = os.path.join(BASE_DIR, "stock_market_guide_full.pdf")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            "Nie znaleziono bazy wektorowej ani pliku PDF. "
            f"Dodaj plik {pdf_path} albo gotowy folder {persist_directory}."
        )

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
    )

    pages_split = text_splitter.split_documents(documents)

    vectorstore = Chroma.from_documents(
        documents=pages_split,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=persist_directory,
    )

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)

@tool
def retrieve_tool(query: str) -> str:
    """
    Tool do wyszukiwania informacji w bazie dokumentów.
    """
    docs = retriever.invoke(query)

    if not docs:
        return "Nie znaleziono żadnych dokumentów związanych z zapytaniem."

    results = []

    for i, doc in enumerate(docs):
        results.append(f"Dokument {i + 1}:\n{doc.page_content}\n")

    return "\n".join(results)

tools = [retrieve_tool]
model_with_tools = model.bind_tools(tools)

def human_node(state: AgentState):
    last_message = state["messages"][-1]

    if hasattr(last_message, "content"):
        last_message_text = last_message.content
    else:
        last_message_text = str(last_message)

    user_response = interrupt({
        "type": "human_review",
        "question": "Co chcesz powiedzieć modelowi?",
        "llm_answer": last_message_text,
    })

    return Command(
        update={
            "messages": [HumanMessage(content=user_response)],
        },
        goto="agent_node",
    )

def llm_node(state: AgentState):
    system_prompt = SystemMessage(
        content=(
            "Jesteś asystentem, który pomaga użytkownikowi znaleźć informacje "
            "w dokumentach. Używaj narzędzia retrieve_tool do wyszukiwania "
            "informacji w bazie dokumentów. Odpowiadaj na podstawie dokumentów. "
            "Jeśli nie masz wystarczających informacji, powiedz to użytkownikowi."
        )
    )

    response = model_with_tools.invoke([system_prompt] + list(state["messages"]))

    return {
        "messages": [response]
    }


def router_agent(state: AgentState):
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_node"

    return "human_node"

def router_human(state: AgentState):
    last_message = state["messages"][-1]

    if isinstance(last_message, HumanMessage):
        if "koniec" in last_message.content.lower():
            return "END"

    return "agent_node"


graph = StateGraph(AgentState)

tool_node = ToolNode(tools)

graph.add_node("agent_node", llm_node)
graph.add_node("tool_node", tool_node)
graph.add_node("human_node", human_node)

graph.add_edge(START, "agent_node")
graph.add_edge("tool_node", "agent_node")

graph.add_conditional_edges(
    "agent_node",
    router_agent,
    {
        "tool_node": "tool_node",
        "human_node": "human_node",
    },
)

graph.add_conditional_edges(
    "human_node",
    router_human,
    {
        "agent_node": "agent_node",
        "END": END,
    },
)

checkpointer = AzureSQLCheckpointSaver(os.getenv("SQLSERVER_CONN_STR"))
checkpointer.setup()

app = graph.compile(checkpointer=checkpointer)

# tutaj przygotowanie pod api

def chat_with_agent(user_message: str, thread_id: str = "default"):
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    state = app.get_state(config)

    if not state.values or "messages" not in state.values:
        events = app.stream(
            {"messages": [HumanMessage(content=user_message)]},
            config,
            stream_mode="values",
        )
    elif state.tasks and state.tasks[0].interrupts:
        events = app.stream(
            Command(resume=user_message),
            config,
            stream_mode="values",
        )
    else:
        events = app.stream(
            {"messages": [HumanMessage(content=user_message)]},
            config,
            stream_mode="values",
        )

    ostatni_event = None

    for event in events:
        ostatni_event = event

    if ostatni_event is None:
        return "Brak odpowiedzi od modelu."

    messages = ostatni_event.get("messages", [])

    if not messages:
        return "Brak wiadomosci w grafie."

    last_message = messages[-1]

    if hasattr(last_message, "content"):
        return last_message.content

    return str(last_message)
