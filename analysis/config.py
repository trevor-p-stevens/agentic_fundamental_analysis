from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3:8b",
    temperature=0.1
)