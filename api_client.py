<<<<<<< HEAD
import os
import aiohttp
import asyncio
=======
# ai-python/api_client.py

import os
import httpx
import json
>>>>>>> 3a44620cbe4b768ecfff14a3c9b2eeb499317f71
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
<<<<<<< HEAD
        self.headers = {
            "x-api-key": self.api_key,
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def _make_request(self, endpoint: str, params: dict = None):
        url = f"{self.base_url}{endpoint}"
        print(f"Calling bitsCrunch API via aiohttp: {url} with params {params}")
        await asyncio.sleep(0.25)
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, params=params, timeout=60.0) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Error from bitsCrunch API ({endpoint}): {error_text}"
                        )
                    return await response.json()
        except Exception as err:
            if isinstance(err, HTTPException):
                raise err
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(err)}")

    # --- Market Insights Methods ---
    async def get_market_insights_analytics(self, blockchain: str = "ethereum", time_range: str = "24h"):
        params = {"blockchain": blockchain, "time_range": time_range}
        return await self._make_request("/nft/market-insights/analytics", params)

    async def get_market_insights_washtrade(self, blockchain: str = "ethereum", time_range: str = "24h"):
        params = {"blockchain": blockchain, "time_range": time_range}
        return await self._make_request("/nft/market-insights/washtrade", params)

    async def get_market_insights_holders(self, blockchain: str = "ethereum", time_range: str = "24h"):
        params = {"blockchain": blockchain, "time_range": time_range}
        return await self._make_request("/nft/market-insights/holders", params)

    async def get_market_insights_scores(self, blockchain: str = "ethereum", time_range: str = "24h"):
        params = {"blockchain": blockchain, "time_range": time_range}
        return await self._make_request("/nft/market-insights/scores", params)

    # --- Other working methods ---
    async def get_nft_metadata(self, contract_address: str, token_id: str, **kwargs):
        params = {"contract_address": [contract_address], "token_id": [token_id], **kwargs}
        return await self._make_request("/nft/metadata", params)
    
    async def get_wallet_nft_balance(self, wallet_address: str, **kwargs):
        params = {"wallet": wallet_address, "limit": 100, **kwargs}
        return await self._make_request("/wallet/balance/nft", params)

    async def get_wallet_metrics(self, wallet_address: str, **kwargs):
        params = {"wallet": wallet_address, **kwargs}
        return await self._make_request("/wallet/metrics", params)

    async def get_wallet_profile(self, wallet_address: str, **kwargs):
        params = {"wallet": wallet_address, **kwargs}
        return await self._make_request("/nft/wallet/profile", params)

    async def get_nft_transactions(self, wallet_address: str, **kwargs):
        params = {"wallet_address": wallet_address, **kwargs}
        return await self._make_request("/nft/transactions", params)
=======
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
>>>>>>> 3a44620cbe4b768ecfff14a3c9b2eeb499317f71
