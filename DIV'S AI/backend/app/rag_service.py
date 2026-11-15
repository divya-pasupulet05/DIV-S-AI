from typing import TypedDict
from pathlib import Path

from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, START, END

from .config import GOOGLE_API_KEY, GEMINI_CHAT_MODEL, GEMINI_EMBEDDING_MODEL, CHROMA_DIR

COLLECTION = "divs_ai_knowledge_base"

def check_key():
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is missing. Configure backend/.env.")

def embeddings():
    check_key()
    return GoogleGenerativeAIEmbeddings(
        model=GEMINI_EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY
    )

def vector_store():
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=embeddings(),
        persist_directory=CHROMA_DIR,
    )

def read_document(path: Path):
    if path.suffix.lower() == ".pdf":
        docs = [
            Document(page_content=p.extract_text() or "",
                     metadata={"source": path.name, "page": i})
            for i, p in enumerate(PdfReader(str(path)).pages, start=1)
        ]
        docs = [d for d in docs if d.page_content.strip()]
    elif path.suffix.lower() in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        docs = [Document(page_content=text, metadata={"source": path.name, "page": 1})] if text.strip() else []
    else:
        raise ValueError("Only PDF, TXT and MD files are supported.")
    if not docs:
        raise ValueError("No readable text found. Scanned PDFs need OCR first.")
    return docs

def ingest(path: Path):
    docs = read_document(path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150, add_start_index=True)
    chunks = splitter.split_documents(docs)
    vector_store().add_documents(chunks)
    return {"filename": path.name, "pages": len(docs), "chunks": len(chunks)}

class RAGState(TypedDict):
    question: str
    context: list[Document]
    answer: str
    sources: list[dict]

def retrieve(state: RAGState):
    docs = vector_store().similarity_search(state["question"], k=4)
    return {"context": docs}

def generate(state: RAGState):
    check_key()
    context = "\n\n".join(
        f"[Source: {d.metadata.get('source')}, page: {d.metadata.get('page')}]\n{d.page_content}"
        for d in state["context"]
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are DIV'S AI, a precise RAG document assistant. Answer using ONLY the supplied context.
If the answer is not present, clearly say you could not find it in the uploaded documents.
Do not invent facts. Explain clearly and refer to source filenames/pages when relevant."""),
        ("human", "Question: {question}\n\nRetrieved context:\n{context}")
    ])
    model = ChatGoogleGenerativeAI(
        model=GEMINI_CHAT_MODEL, google_api_key=GOOGLE_API_KEY, temperature=0.2
    )
    response = (prompt | model).invoke({"question": state["question"], "context": context or "No relevant context found."})
    answer = response.content
    if isinstance(answer, list):
        answer = "\n".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in answer)
    unique, sources = set(), []
    for doc in state["context"]:
        item = (doc.metadata.get("source"), doc.metadata.get("page"))
        if item not in unique:
            unique.add(item)
            sources.append({"filename": item[0], "page": item[1]})
    return {"answer": str(answer), "sources": sources}

def create_rag_graph():
    workflow = StateGraph(RAGState)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile()

rag_graph = create_rag_graph()

def ask(question: str):
    result = rag_graph.invoke({"question": question, "context": [], "answer": "", "sources": []})
    return {"answer": result["answer"], "sources": result["sources"]}
