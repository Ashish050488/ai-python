# ai-python/llm_service.py

import os
import json
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from fastapi import HTTPException 

load_dotenv()

llm = ChatOllama(model="llama3", base_url="http://localhost:11434")

# Function to create the prompt for the LLM based on combined data
def create_llm_prompt(combined_wallet_data: dict, wallet_address: str) -> list:
    # Safely get all data sources
    metrics = combined_wallet_data.get('metrics', {})
    profile = combined_wallet_data.get('profile', {})
    raw_wash_trade_entries = combined_wallet_data.get('wash_trade', []) # This is a list
    nft_scores = combined_wallet_data.get('nft_scores', {}) # NEW: Get NFT Scores data

    # --- Metrics Data Extraction (existing) ---
    balance_eth = float(metrics.get('balance_eth', 0.0)) if metrics.get('balance_eth') is not None else 0.0
    balance_usd = float(metrics.get('balance_usd', 0.0)) if metrics.get('balance_usd') is not None else 0.0
    first_active_day = metrics.get('first_active_day', 'N/A').split('T')[0]
    last_active_day = metrics.get('last_active_day', 'N/A').split('T')[0]
    wallet_age_days = int(metrics.get('wallet_age', 0)) if metrics.get('wallet_age') is not None else 0
    total_txn = int(metrics.get('total_txn', 0)) if metrics.get('total_txn') is not None else 0
    in_txn = int(metrics.get('in_txn', 0)) if metrics.get('in_txn') is not None else 0
    out_txn = int(metrics.get('out_txn', 0)) if metrics.get('out_txn') is not None else 0
    illicit_volume_metrics = float(metrics.get('illicit_volume', 0.0)) if metrics.get('illicit_volume') is not None else 0.0
    mixer_volume_metrics = float(metrics.get('mixer_volume', 0.0)) if metrics.get('mixer_volume') is not None else 0.0
    sanction_volume_metrics = float(metrics.get('sanction_volume', 0.0)) if metrics.get('sanction_volume') is not None else 0.0
    token_cnt = int(metrics.get('token_cnt', 0)) if metrics.get('token_cnt') is not None else 0
    inflow_addresses = int(metrics.get('inflow_addresses', 0)) if metrics.get('inflow_addresses') is not None else 0
    outflow_addresses = int(metrics.get('outflow_addresses', 0)) if metrics.get('outflow_addresses') is not None else 0

    # --- Profile Data Extraction (existing) ---
    aml_is_sanctioned = profile.get('aml_is_sanctioned', False)
    aml_risk_level = profile.get('aml_risk_level', 'N/A')
    aml_risk_inbound_volume = float(profile.get('aml_risk_inbound_volume', 0.0)) if profile.get('aml_risk_inbound_volume') is not None else 0.0
    aml_risk_outbound_volume = float(profile.get('aml_risk_outbound_volume', 0.0)) if profile.get('aml_risk_outbound_volume') is not None else 0.0
    washtrade_nft_count_profile = int(profile.get('washtrade_nft_count', 0)) if profile.get('washtrade_nft_count') is not None else 0
    is_shark = profile.get('is_shark', False)
    is_whale = profile.get('is_whale', False)
    is_contract = profile.get('is_contract', False)
    nft_count_profile = int(profile.get('nft_count', 0)) if profile.get('nft_count') is not None else 0

    # --- Wash Trade Data Summary (from raw_wash_trade_entries) ---
    total_wash_traded_nfts = 0
    total_wash_trade_volume_usd = 0.0
    wash_trade_summary_message = ""
    if isinstance(raw_wash_trade_entries, list) and len(raw_wash_trade_entries) > 0 and 'error' not in raw_wash_trade_entries[0]:
        total_wash_traded_nfts = len(raw_wash_trade_entries)
        for entry in raw_wash_trade_entries:
            volume = float(entry.get('washtrade_volume', 0.0)) if entry.get('washtrade_volume') is not None else 0.0
            total_wash_trade_volume_usd += volume
        wash_trade_summary_message = f"Detected wash trading activity across {total_wash_traded_nfts} specific NFTs, totaling approx. ${total_wash_trade_volume_usd:,.2f} USD in suspicious volume. Examples include NFT contract {raw_wash_trade_entries[0].get('contract_address', 'N/A')} and token ID {raw_wash_trade_entries[0].get('token_id', 'N/A')} (and potentially others)."
        has_wash_trade_data_flag = True
    elif isinstance(raw_wash_trade_entries, dict) and raw_wash_trade_entries.get('error'):
        wash_trade_summary_message = f"WARNING: Detailed NFT wash trade analysis could not be fetched for the test NFT ({raw_wash_trade_entries.get('error')})."
        has_wash_trade_data_flag = False
    else:
        wash_trade_summary_message = "No explicit wash trading detected for the test NFT based on detailed analysis."
        has_wash_trade_data_flag = False

    # --- NFT Scores Data Extraction (NEW) ---
    # Extract relevant scores. Adjust these keys based on the actual API response for /nft/scores
    # Assuming 'score_insight' might contain a summary or a flag
    # Assuming 'rarity_score' and 'estimated_price' are direct numbers
    estimated_price_score = float(nft_scores.get('estimated_price', 0.0)) if nft_scores.get('estimated_price') is not None else 0.0
    rarity_score = float(nft_scores.get('rarity_score', 0.0)) if nft_scores.get('rarity_score') is not None else 0.0
    # Also check for 'washtrade_status' as it's a sort_by option, could be a flag or score
    nft_washtrade_status_score = nft_scores.get('washtrade_status', 'N/A')
    nft_scores_error_msg = nft_scores.get('error', '') # Error from fetching NFT scores data


    # --- Improved Formatting and Conditional Logic for LLM (combining all sources) ---
    formatted_balance_usd = f"${balance_usd:,.2f}" if abs(balance_usd) >= 0.01 else "negligible USD"
    formatted_balance_eth = f"{balance_eth:.8f} ETH" if abs(balance_eth) > 1e-6 else "negligible ETH"

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

    activity_description = ""
    if wallet_age_days > 730 and total_txn > 10000:
        activity_description = "This is an established and highly active wallet, indicating long-term engagement."
    elif wallet_age_days > 365 and total_txn > 1000:
        activity_description = "This is a well-aged and active wallet, showing consistent participation."
    elif wallet_age_days > 0:
        activity_description = "This wallet is relatively new or has moderate activity."
    else:
        activity_description = "This wallet is extremely new, with minimal recorded activity."

    in_out_ratio_comment = ""
    if total_txn > 0:
        if in_txn > out_txn * 5:
            in_out_ratio_comment = "It primarily receives funds, suggesting a role as a collection, distribution, or holding wallet rather than a frequent sender."
        elif out_txn > in_txn * 5:
            in_out_ratio_comment = "It predominantly sends funds, indicating active disbursement or frequent outgoing transactions."
        else:
            in_out_ratio_comment = "It shows a balanced mix of incoming and outgoing transactions."

    # --- Combined Risk Flags and Assessment ---
    risk_flags_list = []
    
    # From metrics
    if illicit_volume_metrics > 0.01:
        risk_flags_list.append(f"HIGH RISK: Detected illicit volume of {illicit_volume_metrics:,.2f} USD from metrics.")
    if mixer_volume_metrics > 0.01:
        risk_flags_list.append(f"MODERATE RISK: Detected mixer volume of {mixer_volume_metrics:,.2f} USD from metrics, which can indicate privacy attempts or suspicious activity.")
    if sanction_volume_metrics > 0.01:
        risk_flags_list.append(f"CRITICAL RISK: Detected transactions with sanctioned entities totaling {sanction_volume_metrics:,.2f} USD from metrics.")
    
    # From profile
    if aml_is_sanctioned:
        risk_flags_list.append(f"CRITICAL RISK: Wallet flagged as sanctioned by AML analysis (Risk Level: {aml_risk_level}).")
    if washtrade_nft_count_profile > 0: # Using profile's wash trade count if available
        risk_flags_list.append(f"MODERATE RISK: Profile indicates {washtrade_nft_count_profile} NFTs involved in wash trading (preliminary flag).")
    if is_shark:
        risk_flags_list.append("NOTABLE HOLDER: Identified as a 'shark' (significant holder).")
    if is_whale:
        risk_flags_list.append("NOTABLE HOLDER: Identified as a 'whale' (very large holder).")
    if is_contract:
        risk_flags_list.append("IDENTITY: This is a contract address, not an EOA. Analysis refers to contract activity.")

    # From new wash_trade endpoint data (summarized)
    if wash_trade_summary_message and "WARNING" in wash_trade_summary_message: 
        risk_flags_list.append(wash_trade_summary_message)
    elif has_wash_trade_data_flag and total_wash_traded_nfts > 0:
        risk_flags_list.append(f"HIGH RISK: Detected wash trading activity across {total_wash_traded_nfts} NFTs, totaling approx. ${total_wash_trade_volume_usd:,.2f} USD in suspicious volume for the test NFT's collection.")
    else: 
        risk_flags_list.append("No explicit wash trading detected for the test NFT based on detailed analysis.")

    # From NFT Scores data (NEW)
    if nft_scores_error_msg:
        risk_flags_list.append(f"WARNING: NFT scores analysis could not be fetched for the test NFT ({nft_scores_error_msg}).")
    else:
        if estimated_price_score > 0 and rarity_score > 0:
             risk_flags_list.append(f"NFT Score Insights for Test NFT: Estimated Price: ${estimated_price_score:,.2f}, Rarity Score: {rarity_score:.2f}.")
        if nft_washtrade_status_score != 'N/A': # Check if washtrade_status is provided
            risk_flags_list.append(f"NFT Wash Trade Status (Scores API): {nft_washtrade_status_score}.")
        # Consider adding more detailed interpretation of scores based on expected ranges/values

    risk_assessment_summary = "No significant illicit, mixer, or sanctioned activity detected from the provided metrics."
    overall_risk_level = "Low Risk"
    if risk_flags_list:
        risk_assessment_summary = "Potential Red Flags & Notable Observations:\n- " + "\n- ".join(risk_flags_list)
        if "CRITICAL RISK" in risk_assessment_summary:
            overall_risk_level = "High Risk"
        elif "HIGH RISK" in risk_assessment_summary:
            overall_risk_level = "High Risk"
        elif "MODERATE RISK" in risk_assessment_summary:
            overall_risk_level = "Moderate Risk"
        elif "NOTABLE HOLDER" in risk_assessment_summary and not ("HIGH RISK" in risk_assessment_summary or "CRITICAL RISK" in risk_assessment_summary):
             overall_risk_level = "Low Risk (Notable Holder)"
    else:
        if total_txn > 0 or nft_count_profile > 0:
            overall_risk_level = "Low Risk"
        else:
            overall_risk_level = "New/Inactive Wallet (Further Assessment Needed)"

    # Construct the human message with all combined data for the LLM
    human_message_content = f"""
    Analyze the following extracted wallet metrics and profile data for wallet address: {wallet_address}

    --- METRICS DATA ---
    - Wallet Age: {formatted_age}
    - Current Balance (USD): {formatted_balance_usd}
    - Current Balance (ETH): {formatted_balance_eth}
    - First Active: {first_active_day}
    - Last Active: {last_active_day}
    - Total Transactions: {total_txn}
    - Incoming Transactions: {in_txn}
    - Outgoing Transactions: {out_txn}
    - Illicit Volume (Metrics): {illicit_volume_metrics} USD
    - Mixer Volume (Metrics): {mixer_volume_metrics} USD
    - Sanction Volume (Metrics): {sanction_volume_metrics} USD
    - Unique Tokens Held: {token_cnt}
    - Inflow Addresses: {inflow_addresses}
    - Outflow Addresses: {outflow_addresses}

    --- PROFILE DATA ---
    - AML is Sanctioned: {aml_is_sanctioned}
    - AML Risk Level: {aml_risk_level}
    - AML Risk Inbound Volume: {aml_risk_inbound_volume} USD
    - AML Risk Outbound Volume: {aml_risk_outbound_volume} USD
    - Washtrade NFT Count (from Profile): {washtrade_nft_count_profile}
    - Is Shark: {is_shark}
    - Is Whale: {is_whale}
    - Is Contract: {is_contract}
    - NFT Count (Profile): {nft_count_profile}

    --- NFT WASH TRADE DATA SUMMARY (from /nft/washtrade endpoint) ---
    - Wash Trade Analysis Message: {wash_trade_summary_message}
    - Total Wash Traded NFTs Found: {total_wash_traded_nfts}
    - Total Wash Trade Volume: {total_wash_trade_volume_usd} USD

    --- NFT SCORES DATA (from /nft/scores endpoint) ---
    - Estimated Price Score: {estimated_price_score} USD
    - Rarity Score: {rarity_score}
    - NFT Wash Trade Status (from Scores API): {nft_washtrade_status_score}
    - NFT Scores Error Message: {nft_scores_error_msg if nft_scores_error_msg else 'None'}

    --- CONTEXTUAL ANALYSIS FROM PYTHON ---
    - Activity Description: {activity_description}
    - Inflow/Outflow Ratio Comment: {in_out_ratio_comment}
    - Risk Flags & Notable Observations: {risk_assessment_summary}

    Based on all these details, generate a comprehensive due-diligence report adhering to the specified structure and guidelines.
    """

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", f"""
        You are CrunchGuardian AI, an expert Web3 and NFT analyst. Your primary goal is to provide clear, actionable, and professional due-diligence reports based on provided wallet metrics and profile data.
        
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
        [Analyze the wallet's activity patterns based on active days, incoming/outgoing transactions. Elaborate on the activity description and inflow/outflow ratio comments provided in the input. Discuss the significance of illicit, mixer, sanctioned activities, wash trading, and notable holder status. State "No [type of] activity detected" if volumes are negligible/zero. Mention inflow/outflow addresses numbers if they are significant. Clearly state if it's a contract address or EOA. Explicitly mention any wash trading detected for associated collections. Integrate insights from NFT Scores, specifically estimated price and rarity, and whether these indicate any anomalies that could hint at unusual NFT status (e.g., potential low value for high rarity, or missing data suggesting an issue with the NFT's known status, or a low NFT score for a seemingly valuable NFT).]
        
        #### Analyst's Verdict
        [Provide a final, one-sentence expert opinion or key takeaway. Reinforce the overall risk assessment.]
        
        ---
        
        **Important Guidelines:**
        - Do NOT include the raw JSON data in the final report.
        - Use the specific formatted values and comments provided in the human message content when creating the report sections.
        - Maintain a neutral, professional, and data-driven tone.
        - Ensure all sections are present even if some data is minimal.
        - Focus on providing insights that a human analyst would find valuable.
        - If 'aml_is_sanctioned' is true for a very well-known and generally legitimate address (like Vitalik Buterin's), you must add a disclaimer such as "Note: This wallet is flagged as sanctioned by AML analysis (Risk Level: [level]) based on the provided API data. For well-known public figures, this flag may represent a test data artifact or requires further independent verification." Include this note prominently.
        """),
        ("human", human_message_content)
    ])
    
    return prompt_template.format_messages(wallet_data=human_message_content)


# Function to invoke the LLM
def invoke_llm(prompt_messages: list):
    """Invokes the initialized LLM with the given prompt messages."""
    try:
        llm_response = llm.invoke(prompt_messages)
        return llm_response.content
    except Exception as err:
        print(f"[LLM Service Error] Failed to invoke LLM: {err}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI report: {str(err)}. Ensure Ollama server is running and model is downloaded correctly."
        )