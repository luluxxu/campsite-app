"""
Pydantic Schemas for Request/Response Validation
Defines the data models for API validation and documentation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class CampsiteBase(BaseModel):
    """Base campsite schema with common fields"""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the campsite")
    description: str = Field(..., min_length=10, max_length=500, description="Detailed description")
    location: str = Field(..., min_length=1, max_length=100, description="City or area location")
    state: str = Field(..., min_length=2, max_length=50, description="State name")
    has_water: bool = Field(..., description="Water availability")
    has_electricity: bool = Field(..., description="Electricity availability")
    has_restrooms: bool = Field(..., description="Restroom facilities availability")
    price_per_night: float = Field(..., ge=0, le=1000, description="Price per night in USD")
    image_url: str = Field(..., description="URL to campsite image")
    
    @validator('state')
    def validate_state(cls, v):
        """Validate state name format"""
        if not v.strip():
            raise ValueError('State cannot be empty')
        return v.strip().title()
    
    @validator('price_per_night')
    def validate_price(cls, v):
        """Validate price is reasonable"""
        if v < 0:
            raise ValueError('Price cannot be negative')
        if v > 1000:
            raise ValueError('Price seems unreasonably high')
        return round(v, 2)


class CampsiteResponse(CampsiteBase):
    """Schema for campsite response data"""
    id: int = Field(..., gt=0, description="Unique campsite identifier")
    
    class Config:
        """Pydantic configuration"""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Pine Valley Campground",
                "description": "Nestled among towering pines with easy access to hiking trails.",
                "location": "Mountain View",
                "state": "California",
                "has_water": True,
                "has_electricity": True,
                "has_restrooms": True,
                "price_per_night": 25.0,
                "image_url": "https://example.com/image.jpg"
            }
        }


class CampsiteCreate(CampsiteBase):
    """Schema for creating a new campsite"""
    pass


class CampsiteUpdate(BaseModel):
    """Schema for updating campsite data"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=50)
    has_water: Optional[bool] = None
    has_electricity: Optional[bool] = None
    has_restrooms: Optional[bool] = None
    price_per_night: Optional[float] = Field(None, ge=0, le=1000)
    image_url: Optional[str] = None


class CampsiteFilter(BaseModel):
    """Schema for campsite filtering parameters"""
    state: Optional[str] = Field(None, description="Filter by state")
    has_water: Optional[bool] = Field(None, description="Filter by water availability")
    has_electricity: Optional[bool] = Field(None, description="Filter by electricity")
    has_restrooms: Optional[bool] = Field(None, description="Filter by restrooms")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price per night")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price per night")
    search: Optional[str] = Field(None, min_length=1, description="Search query")
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        """Ensure max_price is greater than min_price"""
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than min_price')
        return v


class CampsiteListResponse(BaseModel):
    """Schema for campsite list response"""
    campsites: List[CampsiteResponse]
    total_count: int = Field(..., ge=0, description="Total number of campsites")
    filtered_count: int = Field(..., ge=0, description="Number of campsites after filtering")
    
    class Config:
        json_schema_extra = {
            "example": {
                "campsites": [
                    {
                        "id": 1,
                        "name": "Pine Valley Campground",
                        "description": "Beautiful campsite...",
                        "location": "Mountain View",
                        "state": "California",
                        "has_water": True,
                        "has_electricity": True,
                        "has_restrooms": True,
                        "price_per_night": 25.0,
                        "image_url": "https://example.com/image.jpg"
                    }
                ],
                "total_count": 5,
                "filtered_count": 1
            }
        }


class UserPreferences(BaseModel):
    """Schema for user preferences for recommendations"""
    preferred_state: Optional[str] = Field(None, description="Preferred state for camping")
    max_budget: Optional[float] = Field(None, ge=0, le=1000, description="Maximum budget per night")
    required_amenities: List[str] = Field(
        default_factory=list, 
        description="List of required amenities (water, electricity, restrooms)"
    )
    preferred_activities: List[str] = Field(
        default_factory=list,
        description="Preferred activities (hiking, fishing, swimming)"
    )
    
    @validator('required_amenities')
    def validate_amenities(cls, v):
        """Validate amenity options"""
        valid_amenities = {'water', 'electricity', 'restrooms'}
        for amenity in v:
            if amenity.lower() not in valid_amenities:
                raise ValueError(f'Invalid amenity: {amenity}. Valid options: {valid_amenities}')
        return [amenity.lower() for amenity in v]
    
    class Config:
        json_schema_extra = {
            "example": {
                "preferred_state": "California",
                "max_budget": 30.0,
                "required_amenities": ["water", "electricity"],
                "preferred_activities": ["hiking", "fishing"]
            }
        }


class RecommendationResponse(BaseModel):
    """Schema for recommendation response"""
    recommendations: List[Dict[str, Any]] = Field(..., description="List of recommended campsites with scores")
    total_count: int = Field(..., ge=0, description="Total number of recommendations")
    preferences_used: UserPreferences = Field(..., description="Preferences used for recommendations")


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str = Field(..., description="API health status")
    total_campsites: int = Field(..., ge=0, description="Total number of campsites")
    price_range: Dict[str, float] = Field(..., description="Price range information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")


class StatsResponse(BaseModel):
    """Schema for statistics response"""
    total_campsites: int = Field(..., ge=0, description="Total number of campsites")
    available_states: int = Field(..., ge=0, description="Number of states with campsites")
    states: List[str] = Field(..., description="List of all states")
    price_range: Dict[str, float] = Field(..., description="Price range statistics")


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Campsite not found",
                "error_code": "CAMPSITE_NOT_FOUND",
                "timestamp": "2025-05-30T10:30:00"
            }
        }


class MessageResponse(BaseModel):
    """Schema for simple message responses"""
    message: str = Field(..., description="Response message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Welcome to Campsite Reservation API"
            }
        }