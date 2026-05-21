from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid
import enum
from datetime import datetime


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, nullable=False)
    pet_filter_default = Column(Boolean, default=False)
    badge_label = Column(String, default="Pet Friendly")
    badge_color = Column(String, default="green")

    users = relationship("User", back_populates="tenant")
    bookings = relationship("Booking", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")

    tenant = relationship("Tenant", back_populates="users")
    bookings = relationship("Booking", back_populates="user")


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amadeus_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    star_rating = Column(Integer)
    pet_allowed = Column(Boolean, default=False)
    max_pet_weight = Column(Integer)
    pet_fee_per_night = Column(Float, default=0.0)

    bookings = relationship("Booking", back_populates="hotel")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    trip_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Optional because bookings can come from RapidAPI hotel OR flight results
    hotel_id = Column(UUID(as_uuid=True), ForeignKey("hotels.id"), nullable=True)

    # New fields for saving API hotel/flight results
    booking_type = Column(String, nullable=False)   # "hotel" or "flight"
    item_name = Column(String, nullable=False)      # hotel name or flight name
    external_id = Column(String, nullable=True)     # API hotel_id or flight_id if available

    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)

    total_amount = Column(Float, nullable=False, default=0.0)
    pet_fee_total = Column(Float, default=0.0)

    status = Column(Enum(BookingStatus), default=BookingStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)

    departure_time = Column(String, nullable=True)
    arrival_time = Column(String, nullable=True)
    origin_airport_code = Column(String, nullable=True)
    destination_airport_code = Column(String, nullable=True)

    tenant = relationship("Tenant", back_populates="bookings")
    user = relationship("User", back_populates="bookings")
    hotel = relationship("Hotel", back_populates="bookings")