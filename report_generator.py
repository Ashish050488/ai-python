# ai-python/report_generator.py

import asyncio
import os
from fastapi import HTTPException
from .api_client import BitsCrunchAPIClient
from .data_processor import process_and_format_data
from .llm_service import invoke_llm_chain

bits_crunch_client = BitsCrunchAPIClient()

async def generate_comprehensive_report(wallet_address: str):
    all_wallet_data = {}

    # We only call the reliable bitsCrunch endpoints. /token/portfolio is disabled.
    api_calls = [
        ('metrics', lambda: bits_crunch_client.get_wallet_metrics(wallet_address)),
        ('profile', lambda: bits_crunch_client.get_wallet_profile(wallet_address)),
        ('wallet_nft_transactions', lambda: bits_crunch_client.get_nft_transactions(wallet_address=wallet_address, limit=10)),
    ]

    print("Fetching API data sequentially from bitsCrunch...")
    for key, task_func in api_calls:
        try:
            result = await task_func()
            if key in ['metrics', 'profile']:
                all_wallet_data[key] = result.get('data', [{}])[0] if isinstance(result.get('data'), list) and result.get('data') else {}
            else:
                all_wallet_data[key] = result.get('data', [])
            print(f"Successfully fetched '{key}' from bitsCrunch.")
        except Exception as e:
            error_detail = getattr(e, 'detail', str(e))
            status_code = getattr(e, 'status_code', 'N/A')
            print(f"[Report Generator] Error fetching '{key}'. Status: {status_code}. Message: {error_detail[:150]}...")
            all_wallet_data[key] = {"error": f"Failed to fetch {key}"}
        await asyncio.sleep(0.5)

    try:
        print("Processing all fetched data...")
        processed_data = process_and_format_data(all_wallet_data, wallet_address)
        print("Data processed. Sending to AI service for report generation...")
        markdown_report = await invoke_llm_chain(processed_data, wallet_address)

        return {
            "report": markdown_report,
            "overallRiskLevel": processed_data['overall_risk_level'],
            "formattedMetrics": processed_data['formatted_metrics'],
            "graph_data": processed_data['graph_data'],
            "transactions": processed_data['transactions']
        }
    except Exception as e:
        print(f"[Report Generator] Unexpected error during final processing: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")