# ai-python/llm_service.py

from fastapi import HTTPException
from .llm_setup import llm
from .prompt_builder import build_llm_prompt_messages

async def invoke_llm_chain(processed_data: dict, wallet_address: str):
    """
    Builds the prompt and invokes the LLM.
    """
    try:
        prompt_messages = build_llm_prompt_messages(processed_data, wallet_address)
        print("Invoking LLM with constructed prompt...")
        
        llm_response = await llm.ainvoke(prompt_messages)
        
        # Directly return the clean content from the AI
        return llm_response.content
        
    except Exception as err:
        print(f"[LLM Service Error] Failed to invoke LLM: {err}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI report: {str(err)}.")