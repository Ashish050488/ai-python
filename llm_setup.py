# ai-python/llm_setup.py
import os
from langchain_groq import ChatGroq

# This tells the application to use the blazing-fast Groq cloud service.
llm = ChatGroq(
    temperature=0,
    model_name="llama3-8b-8192",
    groq_api_key=os.getenv("GROQ_API_KEY")
)

print("LLM Service is now using Groq with model 'llama3-8b-8192'.")