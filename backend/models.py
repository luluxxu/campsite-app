"""
Domain Models - Business Logic DTOs
These models are used internally between the API and Service layers
They are independent of external API contracts
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Campsite:
    """Domain model representing a campsite in the business layer"""
    id: int
    name: str
    description: str
    location: str
    state: str
    has_water: bool
    has_electricity: bool
    has_restrooms: bool
    price_per_night: float
    image_url: str
    
    def has_all_amenities(self, required_amenities: List[str]) -> bool:
        """Check if campsite has all required amenities"""
        amenity_map = {
            'water': self.has_water,
            'electricity': self.has_electricity,
            'restrooms': self.has_restrooms
        }
        return all(amenity_map.get(amenity, False) for amenity in required_amenities)
    
    def calculate_total_cost(self, nights: int) -> float:
        """Calculate total cost for multiple nights"""
        return self.price_per_night * nights
    
    def is_budget_friendly(self, max_budget: float) -> bool:
        """Check if campsite is within budget"""
        return self.price_per_night <= max_budget


@dataclass
class CampsiteFilter:
    """Domain model for filtering criteria used in business logic"""
    state: Optional[str] = None
    has_water: Optional[bool] = None
    has_electricity: Optional[bool] = None
    has_restrooms: Optional[bool] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    search_query: Optional[str] = None
    
    def matches_campsite(self, campsite: Campsite) -> bool:
        """Check if a campsite matches this filter"""
        if self.state and campsite.state.lower() != self.state.lower():
            return False
        if self.has_water is not None and campsite.has_water != self.has_water:
            return False
        if self.has_electricity is not None and campsite.has_electricity != self.has_electricity:
            return False
        if self.has_restrooms is not None and campsite.has_restrooms != self.has_restrooms:
            return False
        if self.min_price and campsite.price_per_night < self.min_price:
            return False
        if self.max_price and campsite.price_per_night > self.max_price:
            return False
        return True


@dataclass
class UserPreferencesDomain:
    """Domain model for user preferences used in recommendation logic"""
    preferred_state: Optional[str] = None
    max_budget: Optional[float] = None
    required_amenities: List[str] = None
    preferred_activities: List[str] = None
    
    def __post_init__(self):
        if self.required_amenities is None:
            self.required_amenities = []
        if self.preferred_activities is None:
            self.preferred_activities = []


@dataclass
class CampsiteRecommendation:
    """Domain model for campsite recommendations with scoring"""
    campsite: Campsite
    score: float
    matching_criteria: List[str]
    
    def __lt__(self, other):
        """Allow sorting by score"""
        return self.score < other.score


@dataclass
class PriceStatistics:
    """Domain model for price statistics"""
    min_price: float
    max_price: float
    average_price: float
    
    @classmethod
    def from_campsites(cls, campsites: List[Campsite]) -> 'PriceStatistics':
        """Calculate statistics from a list of campsites"""
        if not campsites:
            return cls(0.0, 0.0, 0.0)
        
        prices = [c.price_per_night for c in campsites]
        return cls(
            min_price=min(prices),
            max_price=max(prices),
            average_price=sum(prices) / len(prices)
        )


# Mapper functions to convert between layers
class DomainMapper:
    """Utility class to map between domain models and other representations"""
    
    @staticmethod
    def dict_to_campsite(data: dict) -> Campsite:
        """Convert dictionary to Campsite domain model"""
        return Campsite(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            location=data['location'],
            state=data['state'],
            has_water=data['has_water'],
            has_electricity=data['has_electricity'],
            has_restrooms=data['has_restrooms'],
            price_per_night=data['price_per_night'],
            image_url=data['image_url']
        )
    
    @staticmethod
    def campsite_to_dict(campsite: Campsite) -> dict:
        """Convert Campsite domain model to dictionary"""
        return {
            'id': campsite.id,
            'name': campsite.name,
            'description': campsite.description,
            'location': campsite.location,
            'state': campsite.state,
            'has_water': campsite.has_water,
            'has_electricity': campsite.has_electricity,
            'has_restrooms': campsite.has_restrooms,
            'price_per_night': campsite.price_per_night,
            'image_url': campsite.image_url
        }
    
    @staticmethod
    def api_filter_to_domain(state: Optional[str] = None,
                           has_water: Optional[bool] = None,
                           has_electricity: Optional[bool] = None,
                           has_restrooms: Optional[bool] = None,
                           search: Optional[str] = None,
                           min_price: Optional[float] = None,
                           max_price: Optional[float] = None) -> CampsiteFilter:
        """Convert API parameters to domain filter model"""
        return CampsiteFilter(
            state=state,
            has_water=has_water,
            has_electricity=has_electricity,
            has_restrooms=has_restrooms,
            min_price=min_price,
            max_price=max_price,
            search_query=search
        )