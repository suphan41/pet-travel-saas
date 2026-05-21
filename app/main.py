from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, bookings, hotels, flights

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pet-Friendly Travel SaaS API",
    description="Multi-tenant travel booking platform for pet owners - CMPE 131 Scenario #9",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://agenta.local:5173",
        "http://agentb.local:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(bookings.router)
app.include_router(hotels.router)
app.include_router(flights.router)


@app.get("/")
def root():
    return {"message": "Pet-Friendly Travel SaaS API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}