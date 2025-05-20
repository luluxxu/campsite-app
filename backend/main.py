from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from data import CAMPSITES

app = FastAPI(title="Simple Campsite API")

# CORS setup for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in this simplified version
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Campsite Reservation API"}

@app.get("/campsites", response_model=List[dict])
def get_campsites(
    state: Optional[str] = None,
    has_water: Optional[bool] = None,
    has_electricity: Optional[bool] = None,
    has_restrooms: Optional[bool] = None
):
    # Filter campsites based on query parameters
    filtered_campsites = CAMPSITES
    
    if state:
        filtered_campsites = [c for c in filtered_campsites if c["state"].lower() == state.lower()]
    if has_water is not None:
        filtered_campsites = [c for c in filtered_campsites if c["has_water"] == has_water]
    if has_electricity is not None:
        filtered_campsites = [c for c in filtered_campsites if c["has_electricity"] == has_electricity]
    if has_restrooms is not None:
        filtered_campsites = [c for c in filtered_campsites if c["has_restrooms"] == has_restrooms]
        
    return filtered_campsites

@app.get("/campsites/{campsite_id}")
def get_campsite(campsite_id: int):
    for campsite in CAMPSITES:
        if campsite["id"] == campsite_id:
            return campsite
    raise HTTPException(status_code=404, detail="Campsite not found")