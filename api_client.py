# ai-python/api_client.py

import os
import requests
from dotenv import load_dotenv
from fastapi import HTTPException 

# Get the directory of the current file (api_client.py)
# This helps load_dotenv find the .env file reliably if it's in the same dir
current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_dir, '.env')
load_dotenv(dotenv_path=dotenv_path) # Explicitly load .env from the current directory

class BitsCrunchAPIClient:
    def __init__(self):
        self.api_key = os.getenv("BITSCRUNCH_API_KEY")
        if not self.api_key:
            # Provide a more specific error message if the key is missing
            raise ValueError("BITSCRUNCH_API_KEY not found in .env file in ai-python/ directory.")
        self.base_url = "https://api.unleashnfts.com/api/v2" # Base URL for bitsCrunch API v2

        self.headers = {
            "x-api-key": self.api_key,
            "Accept": "application/json" # Ensure we always request JSON
        }

    def _make_request(self, endpoint: str, params: dict = None):
        """Helper to make authenticated GET requests to bitsCrunch API."""
        url = f"{self.base_url}{endpoint}"
        print(f"Calling bitsCrunch API: {url} with params {params}")

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=20)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx status codes)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"[API Client HTTP ERROR] {http_err} for {url}")
            print(f"→ Response Body: {http_err.response.text if http_err.response else 'No response body'}")
            # Re-raise as HTTPException for FastAPI to catch and propagate
            raise HTTPException(
                status_code=http_err.response.status_code if http_err.response else 500,
                detail=f"Error from bitsCrunch API ({endpoint}): {http_err.response.text if http_err.response else str(http_err)}"
            )
        except requests.exceptions.Timeout:
            print(f"[API Client Timeout ERROR] Request to {url} timed out.")
            # Raise as HTTPException for FastAPI to catch and propagate
            raise HTTPException(
                status_code=408, # 408 is Request Timeout
                detail=f"The request to bitsCrunch API ({endpoint}) timed out."
            )
        except Exception as err:
            print(f"[API Client General ERROR] {err} for {url}")
            # Raise as HTTPException for FastAPI to catch and propagate
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occurred calling bitsCrunch API ({endpoint}): {str(err)}"
            )

    def get_wallet_metrics(self, wallet_address: str, blockchain: str = "ethereum"):
        """Fetches wallet metrics for a given address using /wallet/metrics endpoint."""
        endpoint = "/wallet/metrics"
        params = {
            "blockchain": blockchain,
            "wallet": wallet_address
        }
        return self._make_request(endpoint, params)

    def get_wallet_profile(self, wallet_address: str, blockchain: str = "ethereum"):
        """
        Fetches detailed wallet profile for a specific wallet using the /nft/wallet/profile endpoint.
        Sends wallet address as an array of strings in query params.
        """
        endpoint = "/nft/wallet/profile" # Correct v2 NFT Wallet Profile endpoint path
        params = {
            "blockchain": blockchain,
            "wallet": [wallet_address] # Send wallet address as an array of strings as per v2 docs
        }
        return self._make_request(endpoint, params)

    def get_nft_wash_trade(self, contract_address: str, token_id: str, blockchain: str = "ethereum"):
        """
        Fetches wash trade analysis for a specific NFT (by contract_address, token_id).
        Uses the v2/nft/washtrade endpoint with all required parameters.
        """
        endpoint = "/nft/washtrade" # Correct endpoint path for v2/nft/washtrade
        params = {
            "blockchain": blockchain,        # Required: string (e.g., "ethereum")
            "contract_address": [contract_address], # Required: array of strings
            "token_id": [token_id],          # Required: array of strings
            "sort_by": "washtrade_volume",   # Required: string, as per docs default
            # time_range, sort_order, offset, limit are optional
        }
        return self._make_request(endpoint, params)

    def get_nft_scores(self, contract_address: str, token_id: str, blockchain: str = "ethereum", sort_by: str = "estimated_price"):
        """
        Fetches detailed scores for a specific NFT (candidate for authenticity/risk).
        Uses the v2/nft/scores endpoint with all required parameters.
        """
        endpoint = "/nft/scores" # Exact endpoint path from docs
        params = {
            "blockchain": blockchain,        # Required: string (e.g., "ethereum")
            "contract_address": [contract_address], # Required: array of strings
            "token_id": [token_id],          # Required: array of strings
            "sort_by": sort_by               # Required: string (e.g., "estimated_price", "rarity_score")
        }
        return self._make_request(endpoint, params)