from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from .report_generator import generate_comprehensive_report
from .api_client import BitsCrunchAPIClient

# --- Setup ---
load_dotenv()
app = FastAPI()

# --- PRODUCTION CORS SETUP ---
# For a live, hosted application, you must replace the wildcard "*"
# with the specific URL of your hosted frontend.
origins = [
    "https://your-frontend-app-name.netlify.app", # Replace with your Netlify/Vercel URL
    "http://localhost:5173", 
    "http://localhost:3000",
] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class NftIdentifier(BaseModel):
    contract_address: str
    token_id: str

class BatchMetadataRequest(BaseModel):
    nfts: List[NftIdentifier]
    blockchain: str = "ethereum"

class PortfolioRequest(BaseModel):
    address: str
    blockchain: str = "ethereum"

class AnalysisRequest(BaseModel):
    address: str

class MarketRequest(BaseModel):
    blockchain: str = "ethereum"
    time_range: str = "7d"

# --- API Endpoints ---
@app.get("/")
async def read_root():
    return {"message": "CrunchGuardian AI Backend is running"}

@app.post("/market-insights")
async def get_market_insights_endpoint(request: MarketRequest):
    client = BitsCrunchAPIClient()
    try:
        tasks = {
            "analytics": client.get_market_insights_analytics(request.blockchain, time_range=request.time_range),
            "washtrade": client.get_market_insights_washtrade(request.blockchain, time_range=request.time_range),
            "holders": client.get_market_insights_holders(request.blockchain, time_range=request.time_range),
            "scores": client.get_market_insights_scores(request.blockchain, time_range=request.time_range)
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        response_payload = {}
        for key, result in dict(zip(tasks.keys(), results)).items():
            if not isinstance(result, Exception) and isinstance(result, dict) and "data" in result:
                response_payload[key] = {"data": result.get("data", [])}
            else:
                response_payload[key] = {"data": []}
        return response_payload
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to fetch market insights: {str(e)}")

@app.post("/nft-portfolio")
async def get_nft_portfolio(request: PortfolioRequest):
    client = BitsCrunchAPIClient()
    try:
        portfolio_response = await client.get_wallet_nft_balance(request.address, blockchain=request.blockchain, limit=100)
        return portfolio_response.get("data", [])
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to fetch NFT portfolio list: {str(e)}")

@app.post("/batch-nft-metadata")
async def get_batch_nft_metadata(request: BatchMetadataRequest):
    client = BitsCrunchAPIClient()
    enriched_nfts: Dict[str, dict] = {}
    
    for nft in request.nfts:
        try:
            print(f"Fetching metadata for {nft.token_id}...")
            metadata_response = await client.get_nft_metadata(nft.contract_address, nft.token_id, blockchain=request.blockchain)
            
            identifier = f"{nft.contract_address}:{nft.token_id}"
            if metadata_response and metadata_response.get("data"):
                enriched_nfts[identifier] = metadata_response["data"][0]
            else:
                enriched_nfts[identifier] = {"error": True}
            await asyncio.sleep(0.35)
        except Exception as e:
            print(f"Could not fetch metadata for {nft.token_id}: {e}")
            enriched_nfts[f"{nft.contract_address}:{nft.token_id}"] = {"error": True}
            continue
            
    return enriched_nfts

@app.post("/generate-report")
async def generate_report(request: AnalysisRequest):
    try:
        report_data = await generate_comprehensive_report(request.address)
        return report_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))