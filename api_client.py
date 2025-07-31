# ai-python/api_client.py

import os
import httpx
import json
from dotenv import load_dotenv
from fastapi import HTTPException

current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_dir, '.env')
load_dotenv(dotenv_path=dotenv_path)

class BitsCrunchAPIClient:
    def __init__(self):
        self.api_key = os.getenv("BITSCRUNCH_API_KEY")
        if not self.api_key:
            raise ValueError("BITSCRUNCH_API_KEY not found in .env file.")
        self.base_url = "https://api.unleashnfts.com/api/v2"
        self.async_client = httpx.AsyncClient()
        self.headers = {"x-api-key": self.api_key, "Accept": "application/json"}

    async def _make_request(self, endpoint: str, params: dict = None):
        url = f"{self.base_url}{endpoint}"
        print(f"Calling bitsCrunch API: {url} with params {params}")
        try:
            response = await self.async_client.get(url, headers=self.headers, params=params, timeout=60.0)
            response.raise_for_status()
            try:
                return response.json()
            except json.JSONDecodeError:
                raise HTTPException(status_code=502, detail=f"Bad Gateway: API ({endpoint}) returned a non-JSON response.")
        except httpx.HTTPStatusError as http_err:
            raise HTTPException(status_code=http_err.response.status_code, detail=f"Error from bitsCrunch API ({endpoint}): {http_err.response.text}")
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail=f"The request to bitsCrunch API ({endpoint}) timed out.")
        except Exception as err:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(err)}")

    async def get_wallet_metrics(self, wallet_address: str, blockchain: str = "ethereum"):
        return await self._make_request("/wallet/metrics", {"blockchain": blockchain, "wallet": wallet_address})

    async def get_wallet_profile(self, wallet_address: str, blockchain: str = "ethereum"):
        return await self._make_request("/nft/wallet/profile", {"blockchain": blockchain, "wallet": [wallet_address]})

    async def get_nft_wash_trade(self, contract_address: str, token_id: str, blockchain: str = "ethereum"):
        params = {"blockchain": blockchain, "contract_address": [contract_address], "token_id": [token_id], "sort_by": "washtrade_volume"}
        return await self._make_request("/nft/washtrade", params)

    async def get_nft_scores(self, contract_address: str, token_id: str, blockchain: str = "ethereum", sort_by: str = "estimated_price"):
        params = {"blockchain": blockchain, "contract_address": [contract_address], "token_id": [token_id], "sort_by": sort_by}
        return await self._make_request("/nft/scores", params)

    async def get_nft_price_estimate(self, contract_address: str, token_id: str, blockchain: str = "ethereum"):
        params = {"blockchain": blockchain, "contract_address": contract_address, "token_id": token_id}
        return await self._make_request("/nft/liquify/price_estimate", params)

    async def get_nft_metadata(self, contract_address: str, token_id: str, blockchain: str = "ethereum"):
        params = {"blockchain": blockchain, "contract_address": [contract_address], "token_id": [token_id]}
        return await self._make_request("/nft/metadata", params)
    
    async def get_nft_transactions(self, wallet_address: str = None, contract_address: str = None, token_id: str = None, blockchain: str = "ethereum", time_range: str = "30d", limit: int = 10):
        params = {"blockchain": blockchain, "sort_by": "timestamp", "sort_order": "desc", "time_range": time_range, "limit": limit}
        if wallet_address: params["wallet_address"] = wallet_address
        if contract_address and token_id:
            params["contract_address"] = [contract_address]
            params["token_id"] = [token_id]
        return await self._make_request("/nft/transactions", params)

    async def get_wallet_activity(self, wallet_address: str, time_interval: str = "1d", blockchain: str = "ethereum"):
        params = {"wallet": wallet_address, "time_interval": time_interval, "blockchain": blockchain}
        return await self._make_request("/wallet/activity", params)

    async def get_token_portfolio(self, wallet_address: str, blockchain: str = "ethereum"):
        params = {"wallet": wallet_address, "blockchain": blockchain}
        return await self._make_request("/token/portfolio", params)