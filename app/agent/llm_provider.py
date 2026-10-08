import ollama
from app.settings import OLLAMA_MODEL


def call_llm(messages: list, tools: list = None):
    """
    Ollama ko call karta hai. 'messages' conversation history hai,
    'tools' woh functions hain jo agent use kar sakta hai.
    """
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=messages,
        tools=tools if tools else []
    )
    return response