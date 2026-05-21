from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Booking, BookingStatus, User
from app.dependencies import get_current_user
from datetime import datetime
import uuid
from typing import Optional

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/")
def create_booking(
    booking_type: str,      # "hotel" or "flight"
    item_name: str,         # hotel name or airline/flight name
    start_date: str,        # hotel check-in or flight departure date
    end_date: str,          # hotel check-out or flight return date
    total_amount: float = 0.0,
    pet_fee_total: float = 0.0,
    external_id: str = None,  # hotel_id or flight_id from API if available
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    trip_id: str = None,
    departure_time: str = None,
    arrival_time: str = None,
    origin_airport_code: str = None,
    destination_airport_code: str = None,
):
    if booking_type not in ["hotel", "flight"]:
        raise HTTPException(
            status_code=400,
            detail="booking_type must be 'hotel' or 'flight'"
        )

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    if end_dt < start_dt:
        raise HTTPException(
            status_code=400,
            detail="End date must be after start date"
        )

    trip_uuid = trip_id if trip_id else uuid.uuid4()

    booking = Booking(
        id=uuid.uuid4(),
        trip_id=trip_uuid,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        booking_type=booking_type,
        item_name=item_name,
        external_id=external_id,
        check_in=start_dt,
        check_out=end_dt,
        total_amount=total_amount,
        pet_fee_total=pet_fee_total,
        departure_time=departure_time,
        arrival_time=arrival_time,
        origin_airport_code=origin_airport_code,
        destination_airport_code=destination_airport_code,
        status=BookingStatus.pending
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return {
        "message": "Booking saved successfully",
        "booking_id": str(booking.id),
        "booking_type": booking.booking_type,
        "item_name": booking.item_name,
        "external_id": booking.external_id,
        "start_date": start_date,
        "end_date": end_date,
        "total_amount": booking.total_amount,
        "pet_fee_total": booking.pet_fee_total,
        "status": booking.status
    }


@router.get("/me")
def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id,
        Booking.tenant_id == current_user.tenant_id
    ).order_by(Booking.check_in.asc()).all()

    grouped_trips = {}

    for b in bookings:
        group_key = str(b.trip_id or b.id)

        if group_key not in grouped_trips:
            grouped_trips[group_key] = {
                "bookingId": group_key,
                "userId": str(b.user_id),
                "tenantId": str(b.tenant_id),
                "startDate": b.check_in.strftime("%Y-%m-%d") if b.check_in else None,
                "endDate": b.check_out.strftime("%Y-%m-%d") if b.check_out else None,
                "status": str(b.status.value if hasattr(b.status, "value") else b.status),
                "flightReservations": [],
                "hotelReservations": [],
            }

        trip = grouped_trips[group_key]

        if b.check_in and trip["startDate"]:
            if b.check_in.strftime("%Y-%m-%d") < trip["startDate"]:
                trip["startDate"] = b.check_in.strftime("%Y-%m-%d")

        if b.check_out and trip["endDate"]:
            if b.check_out.strftime("%Y-%m-%d") > trip["endDate"]:
                trip["endDate"] = b.check_out.strftime("%Y-%m-%d")

        booking_type = b.booking_type.value if hasattr(b.booking_type, "value") else b.booking_type
        booking_type = str(booking_type).lower()

        if booking_type == "flight":
            trip["flightReservations"].append({
                "Reservation_No": str(b.id),
                "Airline_Code": "N/A",
                "Flight_Number": b.item_name,
                "Origin_Airport_Code": b.origin_airport_code or "N/A",
                "Destination_Airport_Code": b.destination_airport_code or "N/A",
                "Departure_Date": b.check_in.strftime("%Y-%m-%d") if b.check_in else None,
                "Departure_Time": b.departure_time or "N/A",
                "Arrive_Date": b.check_out.strftime("%Y-%m-%d") if b.check_out else None,
                "Arrive_Time": b.arrival_time or "N/A",
                "Rate": float(b.total_amount or 0),
            })

        elif booking_type == "hotel":
            trip["hotelReservations"].append({
                "Reservation_No": str(b.id),
                "Hotel_Name": b.item_name,
                "Check_In_Date": b.check_in.strftime("%Y-%m-%d") if b.check_in else None,
                "Check_In_Time": "3:00 PM",
                "Check_Out_Date": b.check_out.strftime("%Y-%m-%d") if b.check_out else None,
                "Check_Out_Time": "11:00 AM",
                "Rate": float(b.total_amount or 0),
            })

    return list(grouped_trips.values())

@router.patch("/trips/{trip_id}/cancel")
def cancel_trip_booking(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trip_uuid = uuid.UUID(trip_id)

    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id,
        Booking.tenant_id == current_user.tenant_id,
        (
            (Booking.trip_id == trip_uuid) |
            (Booking.id == trip_uuid)
        )
    ).all()

    if not bookings:
        raise HTTPException(status_code=404, detail="Trip booking not found")

    if all(booking.status == BookingStatus.cancelled for booking in bookings):
        raise HTTPException(status_code=400, detail="Trip already cancelled")

    for booking in bookings:
        booking.status = BookingStatus.cancelled

    db.commit()

    return {
        "message": "Trip booking cancelled",
        "trip_id": trip_id,
        "cancelled_count": len(bookings)
    }