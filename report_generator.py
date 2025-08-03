# In ai-python/report_generator.py

import asyncio
import os
from fastapi import HTTPException
from .api_client import BitsCrunchAPIClient
from .data_processor import process_and_format_data
from .llm_service import invoke_llm_chain

bits_crunch_client = BitsCrunchAPIClient()

async def generate_comprehensive_report(wallet_address: str):
    try:
        all_wallet_data = {}

        api_calls = [
            ('metrics', lambda: bits_crunch_client.get_wallet_metrics(wallet_address, blockchain='ethereum')),
            ('profile', lambda: bits_crunch_client.get_wallet_profile(wallet_address, blockchain='ethereum')),
            ('wallet_nft_transactions', lambda: bits_crunch_client.get_nft_transactions(wallet_address=wallet_address, limit=10, sort_by='timestamp')),
        ]

        print("--- Starting Report Generation ---")
        print("Step 1: Fetching API data from bitsCrunch...")
        for key, task_func in api_calls:
            try:
                result = await task_func()
                if key in ['metrics', 'profile']:
                    all_wallet_data[key] = result.get('data', [{}])[0] if isinstance(result.get('data'), list) and result.get('data') else {}
                else:
                    all_wallet_data[key] = result.get('data', [])
                print(f"  ✅ Successfully fetched '{key}'.")
            except Exception as e:
                # This will now log the specific error without crashing
                error_detail = getattr(e, 'detail', str(e))
                print(f"  ❌ [ERROR] Failed to fetch '{key}': {error_detail}")
                all_wallet_data[key] = {} # Assign empty dict to prevent further errors

        print("\nStep 2: Processing all fetched data...")
        processed_data = process_and_format_data(all_wallet_data, wallet_address)
        print("  ✅ Data processed.")

        print("\nStep 3: Invoking LLM for AI analysis...")
        markdown_report = await invoke_llm_chain(processed_data, wallet_address)
        print("  ✅ AI report generated.")

        print("\n--- Report Generation Complete ---")
        return {
            "report": markdown_report,
            "overallRiskLevel": processed_data['overall_risk_level'],
            "formattedMetrics": processed_data['formatted_metrics'],
            "graph_data": processed_data['graph_data'],
            "transactions": processed_data['transactions']
        }

    except Exception as e:
        # This is a master catch-all to prevent the server from ever crashing
        print(f"🔥🔥🔥 [FATAL ERROR] A critical error occurred in generate_comprehensive_report: {e}")
        # Import traceback to get more details
        import traceback
        traceback.print_exc()
        # Return a proper HTTP error instead of crashing
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred. Check the logs. Error: {str(e)}")