# ai-python/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from .report_generator import generate_comprehensive_report

load_dotenv()

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173", # Default for Vite/React
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    address: str

@app.get("/")
def read_root():
    return {"message": "CrunchGuardian AI service is running!"}

@app.post("/generate-report")
async def generate_report(request: AnalysisRequest):
    try:
        report_data = await generate_comprehensive_report(request.address)
        return report_data
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"[main.py] Unexpected error in main endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred in the AI service: {str(e)}"
        )