# ai-python/test_bitscrunch.py

import os
import httpx
from dotenv import load_dotenv

# Load the API key from your .env file
load_dotenv()
API_KEY = os.getenv("BITSCRUNCH_API_KEY")

if not API_KEY:
    print("❌ Error: BITSCRUNCH_API_KEY not found in .env file.")
    exit()

# The exact parameters that are failing in our app
TEST_URL = "https://api.unleashnfts.com/api/v2/nft/collection/analytics"
PARAMS = {
    "contract_address": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
    "blockchain": "ethereum",
    "time_range": "all"
}
HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json"
}

print(f"🚀 Testing BitsCrunch API endpoint: {TEST_URL}")
print(f"📋 With parameters: {PARAMS}")

try:
    # Make a direct request using the httpx library, just like our app does
    with httpx.Client() as client:
        response = client.get(TEST_URL, headers=HEADERS, params=PARAMS, timeout=60.0)
        
        # Raise an exception for bad status codes (like 500)
        response.raise_for_status()
        
        # If the request is successful, print the data
        print("\n✅ SUCCESS! API call worked.")
        print("--- Data Received ---")
        print(response.json())

except httpx.HTTPStatusError as e:
    # If the request fails, print the error details
    print(f"\n❌ FAILURE! The API returned an error.")
    print(f"Status Code: {e.response.status_code}")
    print(f"Response Body: {e.response.text}")

except Exception as e:
    print(f"\n❌ An unexpected error occurred: {str(e)}")