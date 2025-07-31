# ai-python/prompt_builder.py

from langchain_core.prompts import ChatPromptTemplate

def build_llm_prompt_messages(processed_data: dict, wallet_address: str):
    human_message_llm_input = processed_data['human_message_llm_input']
    overall_risk_level = processed_data['overall_risk_level']

    def escape(text: str) -> str:
        return str(text).replace('{', '{{').replace('}', '}}')

    human_message_content = f"""
    Analyze the following data summary for wallet address: {wallet_address}
    --- DATA SUMMARY ---
    {escape(human_message_llm_input['context_summary'])}
    --- END OF SUMMARY ---
    Based on all the details in the summary, generate a professional due-diligence report in Markdown format.
    """
    
    system_prompt_content = f"""
    You are CrunchGuardian AI, an expert Web3 analyst. Your goal is to provide a concise, high-level due-diligence report in clean Markdown.

    **CRITICAL RULE: Under no circumstances should you generate code, code snippets, filenames, or programming syntax. Your response must be pure, clean Markdown text.**

    Your report MUST contain ONLY these sections:
    ### CrunchGuardian AI Report for {wallet_address}
    **Overall Risk Assessment:** {overall_risk_level}
    #### Summary
    [1-2 sentence overview of the wallet's main characteristics.]
    #### Additional Insights & Red Flags
    [Elaborate on critical findings from the data summary.]
    #### Analyst's Verdict
    [A final, concise expert opinion.]
    ---
    **Important Disclaimer:** This report reflects the provided API data and is not investment advice.
    """

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt_content), ("human", human_message_content)])
    return prompt.format_messages()