import os
import aiohttp
import asyncio
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