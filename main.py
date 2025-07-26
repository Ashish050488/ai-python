# ai-python/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
import json
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Pydantic model for the request body
class AnalysisRequest(BaseModel):
    address: str

# Load API Key for bitsCrunch
BITSCRUNCH_API_KEY = os.getenv("BITSCRUNCH_API_KEY")
if not BITSCRUNCH_API_KEY:
    raise RuntimeError("BITSCRUNCH_API_KEY not found in .env file. Please check your ai-python/.env file.")

# Initialize the LLM with Ollama
# Ensure Ollama desktop application is running and 'llama3' model is pulled.
llm = ChatOllama(model="llama3", base_url="http://localhost:11434")

# bitsCrunch API base URL (Ensure this is correct for the v2 API)
BASE_URL = "https://api.unleashnfts.com/api/v2"

# Function to create the prompt for the LLM
def create_llm_prompt(wallet_data: dict, wallet_address: str) -> list:
    # Ensure we get the actual wallet data dictionary from the 'data' list
    # Added a check if 'data' is not a list or is empty
    wallet_metrics = wallet_data.get('data')
    if not isinstance(wallet_metrics, list) or not wallet_metrics:
        # If 'data' is missing or empty, use an empty dictionary to prevent errors
        wallet_metrics_data = {}
    else:
        wallet_metrics_data = wallet_metrics[0] # Get the first (and likely only) item

    # Dynamically extract and format relevant metrics
    # --- IMPORTANT CHANGE: Coerce to float/int and handle None for all numerical values ---
    # Use float() or int() conversion and explicit None check to ensure numerical types
    balance_eth = float(wallet_metrics_data.get('balance_eth', 0.0)) if wallet_metrics_data.get('balance_eth') is not None else 0.0
    balance_usd = float(wallet_metrics_data.get('balance_usd', 0.0)) if wallet_metrics_data.get('balance_usd') is not None else 0.0
    
    # Safely get dates and strip time part
    first_active_day = wallet_metrics_data.get('first_active_day', 'N/A').split('T')[0]
    last_active_day = wallet_metrics_data.get('last_active_day', 'N/A').split('T')[0]
    
    wallet_age_days = int(wallet_metrics_data.get('wallet_age', 0)) if wallet_metrics_data.get('wallet_age') is not None else 0
    total_txn = int(wallet_metrics_data.get('total_txn', 0)) if wallet_metrics_data.get('total_txn') is not None else 0
    in_txn = int(wallet_metrics_data.get('in_txn', 0)) if wallet_metrics_data.get('in_txn') is not None else 0
    out_txn = int(wallet_metrics_data.get('out_txn', 0)) if wallet_metrics_data.get('out_txn') is not None else 0
    
    illicit_volume = float(wallet_metrics_data.get('illicit_volume', 0.0)) if wallet_metrics_data.get('illicit_volume') is not None else 0.0
    mixer_volume = float(wallet_metrics_data.get('mixer_volume', 0.0)) if wallet_metrics_data.get('mixer_volume') is not None else 0.0
    sanction_volume = float(wallet_metrics_data.get('sanction_volume', 0.0)) if wallet_metrics_data.get('sanction_volume') is not None else 0.0
    
    token_cnt = int(wallet_metrics_data.get('token_cnt', 0)) if wallet_metrics_data.get('token_cnt') is not None else 0
    inflow_addresses = int(wallet_metrics_data.get('inflow_addresses', 0)) if wallet_metrics_data.get('inflow_addresses') is not None else 0
    outflow_addresses = int(wallet_metrics_data.get('outflow_addresses', 0)) if wallet_metrics_data.get('outflow_addresses') is not None else 0

    # --- Improved Formatting and Conditional Logic for LLM ---

    # Format USD balance, handling very small values
    formatted_balance_usd = f"${balance_usd:,.2f}" if abs(balance_usd) >= 0.01 else "negligible USD"
    # Format ETH balance, handling scientific notation or very small values
    formatted_balance_eth = f"{balance_eth:.8f} ETH" if abs(balance_eth) > 1e-6 else "negligible ETH"

    # Human-readable wallet age
    if wallet_age_days >= 365:
        years = wallet_age_days // 365
        remaining_days = wallet_age_days % 365
        formatted_age = f"{wallet_age_days} days (approx. {years} {'year' if years == 1 else 'years'}"
        if remaining_days > 0:
            formatted_age += f" and {remaining_days} days)"
        else:
            formatted_age += ")"
    elif wallet_age_days > 0:
        formatted_age = f"{wallet_age_days} days"
    else:
        formatted_age = "Very new (less than a day)"

    # Activity description based on age and transactions
    activity_description = ""
    if wallet_age_days > 730 and total_txn > 10000:
        activity_description = "This is an established and highly active wallet, indicating long-term engagement."
    elif wallet_age_days > 365 and total_txn > 1000:
        activity_description = "This is a well-aged and active wallet, showing consistent participation."
    elif wallet_age_days > 0:
        activity_description = "This wallet is relatively new or has moderate activity."
    else:
        activity_description = "This wallet is extremely new, with minimal recorded activity."

    # Inflow/Outflow ratio analysis
    in_out_ratio_comment = ""
    if total_txn > 0: # Only comment if there are transactions
        if in_txn > out_txn * 5:
            in_out_ratio_comment = "It primarily receives funds, suggesting a role as a collection, distribution, or holding wallet rather than a frequent sender."
        elif out_txn > in_txn * 5:
            in_out_ratio_comment = "It predominantly sends funds, indicating active disbursement or frequent outgoing transactions."
        else:
            in_out_ratio_comment = "It shows a balanced mix of incoming and outgoing transactions."

    # Risk flags and assessment
    risk_flags_list = []
    if illicit_volume > 0.01: # Check for meaningful illicit volume
        risk_flags_list.append(f"HIGH RISK: Detected illicit volume of {illicit_volume:,.2f} USD.")
    if mixer_volume > 0.01: # Check for meaningful mixer volume
        risk_flags_list.append(f"MODERATE RISK: Detected mixer volume of {mixer_volume:,.2f} USD, which can indicate privacy attempts or suspicious activity.")
    if sanction_volume > 0.01: # Check for meaningful sanction volume
        risk_flags_list.append(f"CRITICAL RISK: Detected transactions with sanctioned entities totaling {sanction_volume:,.2f} USD.")

    risk_assessment_summary = "No significant illicit, mixer, or sanctioned activity detected from the provided metrics."
    overall_risk_level = "Low Risk"
    if risk_flags_list:
        risk_assessment_summary = "Potential Red Flags:\n- " + "\n- ".join(risk_flags_list)
        if "CRITICAL RISK" in risk_assessment_summary:
            overall_risk_level = "High Risk"
        elif "HIGH RISK" in risk_assessment_summary:
            overall_risk_level = "High Risk"
        elif "MODERATE RISK" in risk_assessment_summary:
            overall_risk_level = "Moderate Risk"
    else:
        # If no explicit flags, and activity is normal
        if total_txn > 0:
            overall_risk_level = "Low Risk"
        else:
            overall_risk_level = "New/Inactive Wallet (Assess Further)" # For very new/inactive wallets

    # Construct the human message with more context and structured key metrics for the LLM
    human_message_content = f"""
    Analyze the following extracted wallet metrics for wallet address: {wallet_address}

    Wallet Data Summary:
    - Wallet Age: {formatted_age}
    - Current Balance (USD): {formatted_balance_usd}
    - Current Balance (ETH): {formatted_balance_eth}
    - First Active: {first_active_day}
    - Last Active: {last_active_day}
    - Total Transactions: {total_txn}
    - Incoming Transactions: {in_txn}
    - Outgoing Transactions: {out_txn}
    - Illicit Volume: {illicit_volume} USD
    - Mixer Volume: {mixer_volume} USD
    - Sanction Volume: {sanction_volume} USD
    - Unique Tokens Held: {token_cnt}
    - Inflow Addresses: {inflow_addresses}
    - Outflow Addresses: {outflow_addresses}

    Additional Context for Analysis:
    - Activity Description: {activity_description}
    - Inflow/Outflow Ratio Comment: {in_out_ratio_comment}
    - Risk Flags Summary: {risk_assessment_summary}

    Based on these details, generate a comprehensive due-diligence report adhering to the specified structure and guidelines.
    """

    # Updated prompt template for the LLM
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", f"""
        You are CrunchGuardian AI, an expert Web3 and NFT analyst. Your primary goal is to provide clear, actionable, and professional due-diligence reports based on provided wallet metrics.
        
        **Your report MUST follow this exact Markdown structure:**
        
        ### CrunchGuardian AI Report for {wallet_address}
        
        **Overall Risk Assessment:** {overall_risk_level}
        
        #### Summary
        [Provide a concise, 1-2 sentence overview of the wallet's main characteristics and general activity.]
        
        #### Key Metrics
        - **Wallet Age:** [Present the formatted age from input, e.g., 'X days (approx. Y years)']
        - **Current Balance:** [Present the formatted USD and ETH balances from input, e.g., '$123,456.78 USD / 0.00000005 ETH' or 'negligible USD / nearly zero ETH']
        - **Total Transactions:** [Total number of transactions]
        - **Unique Tokens Held:** [Number of unique tokens/NFTs held]
        
        #### Activity Analysis
        [Analyze the wallet's activity patterns based on first/last active days, incoming/outgoing transactions. Elaborate on the activity description and inflow/outflow ratio comments provided in the input. State if there's no illicit/mixer/sanction activity if volumes are negligible. Mention inflow/outflow addresses numbers if they are significant.]
        
        #### Analyst's Verdict
        [Provide a final, one-sentence expert opinion or key takeaway. Reinforce the overall risk assessment.]
        
        ---
        
        **Important Guidelines:**
        - Do NOT include the raw JSON data in the final report.
        - Use the specific formatted values and comments provided in the human message content when creating the report sections.
        - Maintain a neutral, professional, and data-driven tone.
        - Ensure all sections are present even if some data is minimal.
        - For volumes (illicit, mixer, sanction), state "No [type of] activity detected" if the value is zero or negligible.
        """),
        ("human", human_message_content)
    ])
    
    # format_messages returns a list of Message objects for the LLM
    return prompt_template.format_messages(wallet_data=human_message_content)


# Health check route
@app.get("/")
def read_root():
    return {"message": "CrunchGuardian AI service is running!"}

# The main endpoint that will generate the report
@app.post("/generate-report")
async def generate_report(request: AnalysisRequest):
    """
    Receives an address, fetches real data from bitsCrunch,
    and returns an AI-generated analysis report.
    """
    wallet_address = request.address.strip().lower()
    print(f"Generating report for: {wallet_address}")

    # bitsCrunch API call details
    url = f"{BASE_URL}/wallet/metrics"
    params = {
        "blockchain": "ethereum", # Assuming Ethereum as the primary blockchain for now
        "wallet": wallet_address
    }
    headers = {
        "x-api-key": BITSCRUNCH_API_KEY
    }

    try:
        # Step 1: Get data from bitsCrunch API
        print(f"Calling bitsCrunch API for wallet metrics: {url} with params {params}")
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        bitscrunch_data = response.json()
        
        # Step 2: Call the LLM to analyze the data and generate a report
        print("Data received from bitsCrunch. Sending to AI for analysis using Ollama...")
        
        # Pass the bitsCrunch data and the original wallet_address to the prompt creation function
        prompt_messages = create_llm_prompt(bitscrunch_data, wallet_address)
        
        # Invoke the LLM with the generated prompt messages
        llm_response = llm.invoke(prompt_messages)
        
        # The content of the LLM's response is the markdown report
        markdown_report = llm_response.content
        
        # Return the markdown report wrapped in a dictionary for the frontend
        return {"report": markdown_report}

    except requests.exceptions.HTTPError as http_err:
        # Catch specific HTTP errors from bitsCrunch API
        print(f"[HTTP ERROR from bitsCrunch] {http_err}")
        print(f"→ Response Body: {http_err.response.text if http_err.response else 'No response body'}")
        raise HTTPException(
            status_code=http_err.response.status_code if http_err.response else 500,
            detail=f"Error from bitsCrunch API: {http_err.response.text if http_err.response else str(http_err)}"
        )
    except requests.exceptions.Timeout:
        # Catch timeout errors from bitsCrunch API
        print("Request to bitsCrunch API timed out.")
        raise HTTPException(
            status_code=408, # 408 is Request Timeout
            detail="The request to bitsCrunch API timed out."
        )
    except Exception as err:
        # Catch any other unexpected errors during report generation (e.g., Ollama connection issues)
        print(f"Unexpected error during report generation: {err}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred: {str(err)}. Ensure Ollama server is running and model is downloaded correctly."
        )