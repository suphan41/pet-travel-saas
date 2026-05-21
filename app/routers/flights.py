from fastapi import APIRouter, HTTPException
import requests
import os

router = APIRouter(prefix="/flights", tags=["Flights"])


@router.get("/search")
def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str,
    pet_friendly: bool = False,
    pet_size: str = "small"
):

    url = "https://booking-com15.p.rapidapi.com/api/v1/flights/searchFlights"

    querystring = {
        "fromId": origin.upper() + ".AIRPORT",
        "toId": destination.upper() + ".AIRPORT",
        "departDate": departure_date,
        "returnDate": return_date,
        "stops": "none",
        "pageNo": "1",
        "adults": "1",
        "children": "",
        "sort": "BEST",
        "cabinClass": "ECONOMY",
        "currency_code": "USD"
    }

    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "booking-com15.p.rapidapi.com"
    }

    response = requests.get(
        url,
        headers=headers,
        params=querystring
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    data = response.json()

    pet_note = None

    if pet_friendly:
        if pet_size.lower() == "small":
            pet_note = (
                "Small pets may be allowed in cabin depending "
                "on airline policy."
            )
        else:
            pet_note = (
                "Large pets may require cargo transport or "
                "special airline approval."
            )

    return {
        "origin": origin.upper(),
        "destination": destination.upper(),
        "departure_date": departure_date,
        "return_date": return_date,
        "pet_friendly": pet_friendly,
        "pet_size": pet_size,
        "pet_note": pet_note,
        "flight_results": data
    }