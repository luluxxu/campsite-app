"""
Data Access Layer (Repository Pattern)
Handles all data access operations and abstracts data storage details
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from data import CAMPSITES


class CampsiteRepositoryInterface(ABC):
    """Abstract interface for campsite data access"""
    
    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all campsites"""
        pass
    
    @abstractmethod
    def get_by_id(self, campsite_id: int) -> Optional[Dict[str, Any]]:
        """Get campsite by ID"""
        pass
    
    @abstractmethod
    def get_by_state(self, state: str) -> List[Dict[str, Any]]:
        """Get campsites by state"""
        pass
    
    @abstractmethod
    def filter_by_amenities(
        self, 
        has_water: Optional[bool] = None,
        has_electricity: Optional[bool] = None,
        has_restrooms: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Filter campsites by amenities"""
        pass
    
    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search campsites by text query"""
        pass
    
    @abstractmethod
    def get_states(self) -> List[str]:
        """Get all available states"""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total count of campsites"""
        pass


class InMemoryCampsiteRepository(CampsiteRepositoryInterface):
    """
    In-memory implementation of campsite repository
    Uses the static data from data.py
    """
    
    def __init__(self):
        self._data = CAMPSITES
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all campsites from in-memory storage"""
        return self._data.copy()
    
    def get_by_id(self, campsite_id: int) -> Optional[Dict[str, Any]]:
        """Find campsite by ID in in-memory storage"""
        return next((c for c in self._data if c["id"] == campsite_id), None)
    
    def get_by_state(self, state: str) -> List[Dict[str, Any]]:
        """Get campsites filtered by state"""
        return [
            campsite for campsite in self._data 
            if campsite["state"].lower() == state.lower()
        ]
    
    def filter_by_amenities(
        self, 
        has_water: Optional[bool] = None,
        has_electricity: Optional[bool] = None,
        has_restrooms: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Filter campsites by amenities"""
        filtered = self._data.copy()
        
        if has_water is not None:
            filtered = [c for c in filtered if c["has_water"] == has_water]
        
        if has_electricity is not None:
            filtered = [c for c in filtered if c["has_electricity"] == has_electricity]
        
        if has_restrooms is not None:
            filtered = [c for c in filtered if c["has_restrooms"] == has_restrooms]
        
        return filtered
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search campsites by name, description, or location"""
        if not query:
            return self._data.copy()
        
        query_lower = query.lower()
        return [
            campsite for campsite in self._data
            if (query_lower in campsite["name"].lower() or 
                query_lower in campsite["description"].lower() or
                query_lower in campsite["location"].lower())
        ]
    
    def get_states(self) -> List[str]:
        """Get unique list of states"""
        states = set(campsite["state"] for campsite in self._data)
        return sorted(list(states))
    
    def count(self) -> int:
        """Get total count of campsites"""
        return len(self._data)
    
    def get_price_range(self) -> Dict[str, float]:
        """Get price range information"""
        if not self._data:
            return {"min_price": 0.0, "max_price": 0.0}
        
        prices = [campsite["price_per_night"] for campsite in self._data]
        return {
            "min_price": min(prices),
            "max_price": max(prices)
        }


class DatabaseCampsiteRepository(CampsiteRepositoryInterface):
    """
    Database implementation of campsite repository
    This would connect to a real database (PostgreSQL, MySQL, etc.)
    """
    
    def __init__(self, connection_string: str):
        # In a real implementation, this would set up database connection
        # self.db = database_connection(connection_string)
        self.connection_string = connection_string
        print(f"Database repository initialized with: {connection_string}")
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all campsites from database"""
        # Example of what this would look like:
        # return self.db.query("SELECT * FROM campsites").fetchall()
        raise NotImplementedError("Database implementation not yet available")
    
    def get_by_id(self, campsite_id: int) -> Optional[Dict[str, Any]]:
        """Get campsite by ID from database"""
        # return self.db.query("SELECT * FROM campsites WHERE id = ?", campsite_id).fetchone()
        raise NotImplementedError("Database implementation not yet available")
    
    def get_by_state(self, state: str) -> List[Dict[str, Any]]:
        """Get campsites by state from database"""
        # return self.db.query("SELECT * FROM campsites WHERE state = ?", state).fetchall()
        raise NotImplementedError("Database implementation not yet available")
    
    def filter_by_amenities(
        self, 
        has_water: Optional[bool] = None,
        has_electricity: Optional[bool] = None,
        has_restrooms: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Filter campsites by amenities from database"""
        # Build dynamic SQL query based on filters
        raise NotImplementedError("Database implementation not yet available")
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search campsites in database"""
        # return self.db.query("SELECT * FROM campsites WHERE name LIKE ? OR description LIKE ?", 
        #                      f"%{query}%", f"%{query}%").fetchall()
        raise NotImplementedError("Database implementation not yet available")
    
    def get_states(self) -> List[str]:
        """Get unique states from database"""
        # return self.db.query("SELECT DISTINCT state FROM campsites ORDER BY state").fetchall()
        raise NotImplementedError("Database implementation not yet available")
    
    def count(self) -> int:
        """Get total count from database"""
        # return self.db.query("SELECT COUNT(*) FROM campsites").fetchone()[0]
        raise NotImplementedError("Database implementation not yet available")


# Repository Factory Pattern
class RepositoryFactory:
    """Factory to create appropriate repository based on configuration"""
    
    @staticmethod
    def create_campsite_repository(repo_type: str = "memory") -> CampsiteRepositoryInterface:
        """
        Create campsite repository based on type
        
        Args:
            repo_type: Type of repository ("memory" or "database")
            
        Returns:
            CampsiteRepositoryInterface implementation
        """
        if repo_type == "memory":
            return InMemoryCampsiteRepository()
        elif repo_type == "database":
            # In production, this would use real database connection string
            return DatabaseCampsiteRepository("postgresql://user:pass@localhost/campsites")
        else:
            raise ValueError(f"Unknown repository type: {repo_type}")