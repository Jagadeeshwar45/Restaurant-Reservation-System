from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Restaurant(BaseModel):
    id: int
    name: str
    address: str
    lat: float
    lon: float
    capacity: int
    cuisine: str
    features: List[str] = []

class Reservation(BaseModel):
    id: int
    restaurant_id: int
    datetime: datetime
    seats: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    status: str = "confirmed"
