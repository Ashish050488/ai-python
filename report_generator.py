# ai-python/report_generator.py

from fastapi import HTTPException
from .api_client import BitsCrunchAPIClient
from .llm_service import create_llm_prompt, invoke_llm 

# Initialize API Client (reusing the instance from api_client.py)
bits_crunch_client = BitsCrunchAPIClient()

async def generate_comprehensive_report(wallet_address: str):
    """
    Orchestrates fetching data from bitsCrunch and generating an AI report.
    """
    all_wallet_data = {} 

    # Fetch Wallet Metrics
    try:
        metrics_data = bits_crunch_client.get_wallet_metrics(wallet_address)
        all_wallet_data['metrics'] = metrics_data.get('data', [{}])[0]
    except HTTPException as e:
        print(f"[Report Generator] Error fetching wallet metrics: {e.detail}")
        all_wallet_data['metrics'] = {"error": f"Failed to fetch metrics: {e.detail}"}
        raise e 
    except Exception as e:
        print(f"[Report Generator] Unexpected error fetching wallet metrics: {e}")
        all_wallet_data['metrics'] = {"error": f"Unexpected error fetching metrics: {str(e)}"}
        raise HTTPException(status_code=500, detail=f"Failed to fetch wallet metrics: {str(e)}")


    # Fetch Wallet Profile
    try:
        profile_data = bits_crunch_client.get_wallet_profile(wallet_address)
        all_wallet_data['profile'] = profile_data.get('data', [{}])[0]
    except HTTPException as e:
        print(f"[Report Generator] Error fetching wallet profile: {e.detail}")
        all_wallet_data['profile'] = {"error": f"Failed to fetch profile: {e.detail}"}
        raise e
    except Exception as e:
        print(f"[Report Generator] Unexpected error fetching wallet profile: {e}")
        all_wallet_data['profile'] = {"error": f"Unexpected error fetching profile: {str(e)}"}
        raise HTTPException(status_code=500, detail=f"Failed to fetch wallet profile: {str(e)}")

    # Fetch NFT Wash Trade Data
    test_nft_contract_address = "0xbd3531da5cf5857e7cfaa92426877b022e612cf8" # A common contract address with wash trade data from your curl output
    test_nft_token_id = "1550" # A specific token ID from your curl output

    try:
        print(f"Fetching wash trade data for NFT: {test_nft_contract_address} (Token ID: {test_nft_token_id})")
        wash_trade_api_response = bits_crunch_client.get_nft_wash_trade(
            contract_address=test_nft_contract_address,
            token_id=test_nft_token_id,
            blockchain="ethereum"
        )
        raw_wash_trade_data_list = wash_trade_api_response.get('data', [])
        if raw_wash_trade_data_list and isinstance(raw_wash_trade_data_list, list) and len(raw_wash_trade_data_list) > 0:
            all_wallet_data['wash_trade'] = raw_wash_trade_data_list # Store the list directly
        else:
            all_wallet_data['wash_trade'] = [] # Default to empty list if no data or error
    except HTTPException as e:
        print(f"[Report Generator] Error fetching NFT wash trade data: {e.detail}")
        all_wallet_data['wash_trade'] = {"error": f"Failed to fetch NFT wash trade data: {e.detail}"}
    except Exception as e:
        print(f"[Report Generator] Unexpected error fetching NFT wash trade data: {e}")
        all_wallet_data['wash_trade'] = {"error": f"Unexpected error fetching NFT wash trade data: {str(e)}"}
    
    # --- NEW: Fetch NFT Scores Data (Forgery/Authenticity Candidate) ---
    # Use the same test NFT for consistency
    try:
        print(f"Fetching NFT scores for NFT: {test_nft_contract_address} (Token ID: {test_nft_token_id})")
        nft_scores_api_response = bits_crunch_client.get_nft_scores(
            contract_address=test_nft_contract_address,
            token_id=test_nft_token_id,
            blockchain="ethereum",
            sort_by="estimated_price" # Or "rarity_score", "washtrade_status" - choose based on what's most relevant for "forgery"
        )
        # Assuming NFT Scores data is also a list under 'data' key, similar to wash_trade
        raw_nft_scores_data_list = nft_scores_api_response.get('data', [])
        if raw_nft_scores_data_list and isinstance(raw_nft_scores_data_list, list) and len(raw_nft_scores_data_list) > 0:
            all_wallet_data['nft_scores'] = raw_nft_scores_data_list[0] # Take the first dict from the list
        else:
            all_wallet_data['nft_scores'] = {} # No data found, assign empty dict
    except HTTPException as e:
        print(f"[Report Generator] Error fetching NFT scores data: {e.detail}")
        all_wallet_data['nft_scores'] = {"error": f"Failed to fetch NFT scores data: {e.detail}"}
    except Exception as e:
        print(f"[Report Generator] Unexpected error fetching NFT scores data: {e}")
        all_wallet_data['nft_scores'] = {"error": f"Unexpected error fetching NFT scores data: {str(e)}"}
    # --- END NEW ---

    # Generate LLM Prompt and Invoke LLM
    try:
        print("Data received from bitsCrunch. Sending to AI for analysis and report generation...")
        prompt_messages = create_llm_prompt(all_wallet_data, wallet_address)
        markdown_report = invoke_llm(prompt_messages)
        return {"report": markdown_report}
    except HTTPException as e:
        print(f"[Report Generator] Error from LLM Service: {e.detail}")
        raise e
    except Exception as e:
        print(f"[Report Generator] Unexpected error during LLM processing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred during AI report generation: {str(e)}"
        )