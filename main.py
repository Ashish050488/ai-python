# ai-python/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Import the new report generator
from .report_generator import generate_comprehensive_report

# Load environment variables
load_dotenv()

app = FastAPI()

class AnalysisRequest(BaseModel):
    address: str

# Health check route
@app.get("/")
def read_root():
    return {"message": "CrunchGuardian AI service is running!"}

# The main endpoint that will generate the report
@app.post("/generate-report")
async def generate_report(request: AnalysisRequest):
    """
    Receives an address and triggers the comprehensive report generation.
    """
    try:
        report_data = await generate_comprehensive_report(request.address)
        return report_data
    except HTTPException as e:
        # Re-raise HTTPExceptions that came from deeper layers
        raise e
    except Exception as e:
        # Catch any unexpected errors from the report_generator
        print(f"[main.py] Unexpected error in main endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred in the AI service: {str(e)}"
        )