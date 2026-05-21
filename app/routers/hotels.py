from fastapi import APIRouter, HTTPException, Query
import os
import requests
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/hotels-api", tags=["Hotels"])

@router.get("/search")
def search_hotels(
    location: str = Query(...),
    check_in: str = Query(...),
    check_out: str = Query(...),
    pet_friendly: bool = Query(True),
    max_pet_weight: int = Query(50),
):
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
    }

    # Step 1: get destination id
    location_url = "https://booking-com.p.rapidapi.com/v1/hotels/locations"

    location_params = {
        "name": location,
        "locale": "en-us"
    }

    try:
        location_response = requests.get(
            location_url,
            headers=headers,
            params=location_params,
            timeout=10
        )
        location_response.raise_for_status()
        location_data = location_response.json()

        if not location_data:
            raise HTTPException(status_code=404, detail="No destination found")

        dest_id = location_data[0]["dest_id"]
        dest_type = location_data[0]["dest_type"]

        # Step 2: search real hotels
        search_url = "https://booking-com.p.rapidapi.com/v1/hotels/search"

        search_params = {
            "dest_id": dest_id,
            "dest_type": dest_type,
            "checkin_date": check_in,
            "checkout_date": check_out,
            "adults_number": 1,
            "room_number": 1,
            "units": "metric",
            "filter_by_currency": "USD",
            "locale": "en-us",
            "order_by": "popularity"
        }

        search_response = requests.get(
            search_url,
            headers=headers,
            params=search_params,
            timeout=15
        )
        search_response.raise_for_status()
        hotel_data = search_response.json()

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"RapidAPI error: {str(e)}"
        )

    results = hotel_data.get("result", [])[:10]

    for hotel in results:
        hotel["pet_friendly"] = pet_friendly
        hotel["pet_fee"] = 25
        hotel["max_pet_weight"] = max_pet_weight
        hotel["check_in"] = check_in
        hotel["check_out"] = check_out

    return {
        "location": location,
        "check_in": check_in,
        "check_out": check_out,
        "pet_friendly": pet_friendly,
        "max_pet_weight": max_pet_weight,
        "results": results
    }