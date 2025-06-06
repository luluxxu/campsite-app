"""
Campsite Service Layer - Business Logic with Domain Models
Now uses Domain DTOs instead of dictionaries
"""
from typing import List, Optional
from repositories import CampsiteRepositoryInterface, RepositoryFactory
from models import (
    Campsite, CampsiteFilter, UserPreferencesDomain, 
    CampsiteRecommendation, PriceStatistics, DomainMapper
)


class CampsiteService:
    """Service class for campsite business logic operations using domain models"""
    
    def __init__(self, repository: Optional[CampsiteRepositoryInterface] = None):
        """
        Initialize service with repository
        
        Args:
            repository: Data access repository (defaults to in-memory)
        """
        self.repository = repository or RepositoryFactory.create_campsite_repository("memory")
        self.mapper = DomainMapper()
    
    def get_all_campsites(self) -> List[Campsite]:
        """
        Retrieve all available campsites as domain models
        
        Returns:
            List of Campsite domain objects
        """
        campsite_dicts = self.repository.get_all()
        return [self.mapper.dict_to_campsite(data) for data in campsite_dicts]
    
    def get_campsite_by_id(self, campsite_id: int) -> Optional[Campsite]:
        """
        Find a specific campsite by its ID
        
        Args:
            campsite_id: The unique identifier for the campsite
            
        Returns:
            Campsite domain object if found, None otherwise
        """
        if campsite_id <= 0:
            return None
        
        campsite_dict = self.repository.get_by_id(campsite_id)
        return self.mapper.dict_to_campsite(campsite_dict) if campsite_dict else None
    
    def filter_campsites(self, filter_criteria: CampsiteFilter) -> List[Campsite]:
        """
        Filter campsites based on domain filter criteria
        
        Args:
            filter_criteria: CampsiteFilter domain object with filtering rules
            
        Returns:
            List of Campsite domain objects matching the criteria
        """
        # Get all campsites as domain objects
        all_campsites = self.get_all_campsites()
        
        # Apply domain-level filtering
        filtered_campsites = [
            campsite for campsite in all_campsites
            if filter_criteria.matches_campsite(campsite)
        ]
        
        # Apply search if present
        if filter_criteria.search_query:
            query_lower = filter_criteria.search_query.lower()
            filtered_campsites = [
                campsite for campsite in filtered_campsites
                if (query_lower in campsite.name.lower() or
                    query_lower in campsite.description.lower() or
                    query_lower in campsite.location.lower())
            ]
        
        return filtered_campsites
    
    def search_campsites(self, query: str) -> List[Campsite]:
        """
        Search campsites using domain models
        
        Args:
            query: Search term
            
        Returns:
            List of matching Campsite domain objects
        """
        if not query or not query.strip():
            return self.get_all_campsites()
        
        campsite_dicts = self.repository.search(query.strip())
        return [self.mapper.dict_to_campsite(data) for data in campsite_dicts]
    
    def get_available_states(self) -> List[str]:
        """
        Get list of all unique states that have campsites
        
        Returns:
            Sorted list of state names
        """
        return self.repository.get_states()
    
    def get_campsite_count(self) -> int:
        """
        Get total number of available campsites
        
        Returns:
            Total count of campsites
        """
        return self.repository.count()
    
    def get_price_statistics(self) -> PriceStatistics:
        """
        Get price statistics using domain model
        
        Returns:
            PriceStatistics domain object
        """
        campsites = self.get_all_campsites()
        return PriceStatistics.from_campsites(campsites)
    
    def get_campsites_by_price_range(
        self, 
        min_price: Optional[float] = None, 
        max_price: Optional[float] = None
    ) -> List[Campsite]:
        """
        Get campsites within a specific price range using domain logic
        
        Args:
            min_price: Minimum price per night
            max_price: Maximum price per night
            
        Returns:
            List of Campsite domain objects within the price range
        """
        filter_criteria = CampsiteFilter(min_price=min_price, max_price=max_price)
        return self.filter_campsites(filter_criteria)
    
    def get_recommended_campsites(
        self, 
        preferences: UserPreferencesDomain
    ) -> List[CampsiteRecommendation]:
        """
        Get recommended campsites based on user preferences using domain models
        
        Args:
            preferences: UserPreferencesDomain object
            
        Returns:
            List of CampsiteRecommendation objects sorted by score
        """
        all_campsites = self.get_all_campsites()
        recommendations = []
        
        for campsite in all_campsites:
            score = 0.0
            matching_criteria = []
            
            # State preference scoring
            if preferences.preferred_state:
                if campsite.state.lower() == preferences.preferred_state.lower():
                    score += 3.0
                    matching_criteria.append("Preferred state match")
            
            # Budget scoring
            if preferences.max_budget:
                if campsite.is_budget_friendly(preferences.max_budget):
                    score += 2.0
                    matching_criteria.append("Within budget")
                    # Bonus for being significantly under budget
                    budget_ratio = campsite.price_per_night / preferences.max_budget
                    if budget_ratio < 0.7:
                        score += 1.0
                        matching_criteria.append("Great value")
            
            # Amenity scoring using domain method
            if preferences.required_amenities:
                if campsite.has_all_amenities(preferences.required_amenities):
                    score += len(preferences.required_amenities) * 1.5
                    matching_criteria.append(f"All {len(preferences.required_amenities)} required amenities")
                else:
                    # Partial credit for some amenities
                    amenity_map = {
                        'water': campsite.has_water,
                        'electricity': campsite.has_electricity,
                        'restrooms': campsite.has_restrooms
                    }
                    matched = sum(1 for amenity in preferences.required_amenities 
                                if amenity_map.get(amenity, False))
                    if matched > 0:
                        score += matched * 0.5
                        matching_criteria.append(f"{matched} of {len(preferences.required_amenities)} amenities")
            
            # Activity matching (simplified for this example)
            if preferences.preferred_activities:
                # Check if description mentions activities
                description_lower = campsite.description.lower()
                for activity in preferences.preferred_activities:
                    if activity.lower() in description_lower:
                        score += 0.5
                        matching_criteria.append(f"Offers {activity}")
            
            if score > 0:
                recommendations.append(CampsiteRecommendation(
                    campsite=campsite,
                    score=score,
                    matching_criteria=matching_criteria
                ))
        
        # Sort by score (highest first) using domain model comparison
        recommendations.sort(reverse=True)
        
        return recommendations
    
    def calculate_trip_cost(self, campsite_id: int, nights: int) -> Optional[float]:
        """
        Calculate total cost for a trip using domain logic
        
        Args:
            campsite_id: Campsite identifier
            nights: Number of nights
            
        Returns:
            Total cost or None if campsite not found
        """
        campsite = self.get_campsite_by_id(campsite_id)
        return campsite.calculate_total_cost(nights) if campsite else None