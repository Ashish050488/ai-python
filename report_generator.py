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

    # --- Fetch NFT Wash Trade Data ---
    test_nft_contract_address = "0xbd3531da5cf5857e7cfaa92426877b022e612cf8" 
    test_nft_token_id = "1550" 

    try:
        print(f"Fetching wash trade data for NFT: {test_nft_contract_address} (Token ID: {test_nft_token_id})")
        wash_trade_api_response = bits_crunch_client.get_nft_wash_trade(
            contract_address=test_nft_contract_address,
            token_id=test_nft_token_id,
            blockchain="ethereum"
        )
        
        raw_wash_trade_data_list = wash_trade_api_response.get('data', [])
        if raw_wash_trade_data_list and isinstance(raw_wash_trade_data_list, list) and len(raw_wash_trade_data_list) > 0:
            all_wallet_data['wash_trade'] = raw_wash_trade_data_list 
        else:
            all_wallet_data['wash_trade'] = [] 
        
    except HTTPException as e:
        print(f"[Report Generator] Error fetching NFT wash trade data: {e.detail}")
        all_wallet_data['wash_trade'] = {"error": f"Failed to fetch NFT wash trade data: {e.detail}"}
    except Exception as e:
        print(f"[Report Generator] Unexpected error fetching NFT wash trade data: {e}")
        all_wallet_data['wash_trade'] = {"error": f"Unexpected error fetching NFT wash trade data: {str(e)}"}
    # --- END Fetch NFT Wash Trade Data ---

    # --- Fetch NFT Scores Data (Forgery/Authenticity Candidate) ---
    test_nft_contract_address = "0xbd3531da5cf5857e7cfaa92426877b022e612cf8" 
    test_nft_token_id = "1550" 

    try:
        print(f"Fetching NFT scores for NFT: {test_nft_contract_address} (Token ID: {test_nft_token_id})")
        nft_scores_api_response = bits_crunch_client.get_nft_scores(
            contract_address=test_nft_contract_address,
            token_id=test_nft_token_id,
            blockchain="ethereum",
            sort_by="estimated_price" 
        )
        raw_nft_scores_data_list = nft_scores_api_response.get('data', [])
        if raw_nft_scores_data_list and isinstance(raw_nft_scores_data_list, list) and len(raw_nft_scores_data_list) > 0:
            all_wallet_data['nft_scores'] = raw_nft_scores_data_list[0] 
        else:
            all_wallet_data['nft_scores'] = {} 
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
        # create_llm_prompt now returns a tuple: (prompt_messages, overall_risk_level_string, formatted_metrics_dict)
        prompt_messages, overall_risk_level_string, formatted_metrics_dict = create_llm_prompt(all_wallet_data, wallet_address)
        
        markdown_report = invoke_llm(prompt_messages)
        
        # Return all three pieces of data to main.py
        return {
            "report": markdown_report, 
            "overallRiskLevel": overall_risk_level_string, 
            "formattedMetrics": formatted_metrics_dict # NEW: Pass formatted metrics here
        }
    except HTTPException as e:
        print(f"[Report Generator] Error from LLM Service: {e.detail}")
        raise e
    except Exception as e:
        print(f"[Report Generator] Unexpected error during LLM processing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred during AI report generation: {str(e)}"
        )