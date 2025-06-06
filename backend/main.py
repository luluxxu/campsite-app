"""
FastAPI Application - Refactored to use Domain Models
Complete file with all imports and initialization
"""
from fastapi import FastAPI, HTTPException, Query, Path, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from services import CampsiteService
from repositories import RepositoryFactory
from models import (
    CampsiteFilter, UserPreferencesDomain, DomainMapper
)
from schemas import (
    CampsiteResponse, CampsiteListResponse, UserPreferences, 
    RecommendationResponse, HealthResponse, StatsResponse,
    MessageResponse, ErrorResponse
)

# Create FastAPI application
app = FastAPI(
    title="🏕️ Campsite Reservation API",
    description="A professional REST API for discovering and exploring campsites across the United States",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    responses={
        404: {"model": ErrorResponse, "description": "Resource not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection for service layer
def get_campsite_service() -> CampsiteService:
    """Dependency injection for campsite service"""
    repository = RepositoryFactory.create_campsite_repository("memory")
    return CampsiteService(repository)

@app.get("/", response_model=MessageResponse, tags=["General"])
def read_root():
    """Welcome endpoint - confirms API is running"""
    return MessageResponse(message="Welcome to Campsite Reservation API")

@app.get("/campsites", 
         response_model=CampsiteListResponse, 
         tags=["Campsites"],
         summary="Get filtered campsites",
         description="Retrieve campsites with optional filtering by state, amenities, price range, and search query")
def get_campsites(
    state: Optional[str] = Query(None, description="Filter by state (e.g., 'California')"),
    has_water: Optional[bool] = Query(None, description="Filter by water availability"),
    has_electricity: Optional[bool] = Query(None, description="Filter by electricity availability"),
    has_restrooms: Optional[bool] = Query(None, description="Filter by restroom availability"),
    search: Optional[str] = Query(None, min_length=1, description="Search by name, description, or location"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price per night"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price per night"),
    service: CampsiteService = Depends(get_campsite_service)
):
    """
    Demonstrates the two-DTO pattern:
    1. API receives raw parameters
    2. Converts to domain model (CampsiteFilter)
    3. Service returns domain models (List[Campsite])
    4. Converts back to API DTOs (CampsiteResponse)
    """
    try:
        # Validate price range at API level
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_price cannot be greater than max_price"
            )
        
        # Convert API parameters to domain filter model
        filter_criteria = DomainMapper.api_filter_to_domain(
            state=state,
            has_water=has_water,
            has_electricity=has_electricity,
            has_restrooms=has_restrooms,
            search=search,
            min_price=min_price,
            max_price=max_price
        )
        
        # Service layer works with domain models
        campsite_domains = service.filter_campsites(filter_criteria)
        total_count = service.get_campsite_count()
        
        # Convert domain models back to API DTOs
        campsite_responses = [
            CampsiteResponse(
                id=campsite.id,
                name=campsite.name,
                description=campsite.description,
                location=campsite.location,
                state=campsite.state,
                has_water=campsite.has_water,
                has_electricity=campsite.has_electricity,
                has_restrooms=campsite.has_restrooms,
                price_per_night=campsite.price_per_night,
                image_url=campsite.image_url
            )
            for campsite in campsite_domains
        ]
        
        return CampsiteListResponse(
            campsites=campsite_responses,
            total_count=total_count,
            filtered_count=len(campsite_responses)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving campsites: {str(e)}"
        )

@app.get("/campsites/{campsite_id}", 
         response_model=CampsiteResponse, 
         tags=["Campsites"],
         summary="Get campsite by ID",
         description="Retrieve detailed information for a specific campsite")
def get_campsite(
    campsite_id: int = Path(..., gt=0, description="Unique campsite identifier"),
    service: CampsiteService = Depends(get_campsite_service)
):
    """
    Shows domain model usage for single entity retrieval
    """
    try:
        # Service returns domain model
        campsite_domain = service.get_campsite_by_id(campsite_id)
        
        if not campsite_domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campsite with ID {campsite_id} not found"
            )
        
        # Convert domain model to API DTO
        return CampsiteResponse(
            id=campsite_domain.id,
            name=campsite_domain.name,
            description=campsite_domain.description,
            location=campsite_domain.location,
            state=campsite_domain.state,
            has_water=campsite_domain.has_water,
            has_electricity=campsite_domain.has_electricity,
            has_restrooms=campsite_domain.has_restrooms,
            price_per_night=campsite_domain.price_per_night,
            image_url=campsite_domain.image_url
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving campsite: {str(e)}"
        )

@app.post("/campsites/recommendations", 
          response_model=RecommendationResponse, 
          tags=["Recommendations"],
          summary="Get personalized recommendations",
          description="Get campsite recommendations based on user preferences")
def get_recommendations(
    preferences: UserPreferences,  # API DTO from client
    service: CampsiteService = Depends(get_campsite_service)
):
    """
    Complex example showing full DTO transformation:
    1. Receive API DTO (UserPreferences)
    2. Transform to domain model (UserPreferencesDomain)
    3. Service returns domain recommendations
    4. Transform back to API response
    """
    try:
        # Convert API DTO to domain model
        domain_preferences = UserPreferencesDomain(
            preferred_state=preferences.preferred_state,
            max_budget=preferences.max_budget,
            required_amenities=preferences.required_amenities,
            preferred_activities=preferences.preferred_activities
        )
        
        # Service works with domain models
        recommendations = service.get_recommended_campsites(domain_preferences)
        
        # Convert domain recommendations to API format
        recommendation_dicts = []
        for rec in recommendations:
            campsite_dict = DomainMapper.campsite_to_dict(rec.campsite)
            campsite_dict['recommendation_score'] = rec.score
            campsite_dict['matching_criteria'] = rec.matching_criteria
            recommendation_dicts.append(campsite_dict)
        
        return RecommendationResponse(
            recommendations=recommendation_dicts,
            total_count=len(recommendations),
            preferences_used=preferences
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )

@app.get("/health", 
         response_model=HealthResponse, 
         tags=["Monitoring"],
         summary="Health check",
         description="Check API health and get system statistics")
def health_check(service: CampsiteService = Depends(get_campsite_service)):
    """
    Health check endpoint for monitoring and system information
    """
    try:
        total_campsites = service.get_campsite_count()
        price_stats = service.get_price_statistics()
        
        return HealthResponse(
            status="healthy",
            total_campsites=total_campsites,
            price_range={
                "min_price": price_stats.min_price,
                "max_price": price_stats.max_price
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

@app.get("/states", 
         response_model=List[str], 
         tags=["Reference Data"],
         summary="Get available states",
         description="Get list of all states that have campsites")
def get_states(service: CampsiteService = Depends(get_campsite_service)):
    """
    Get list of all states with available campsites
    """
    try:
        states = service.get_available_states()
        return states
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving states: {str(e)}"
        )

@app.get("/stats", 
         response_model=StatsResponse, 
         tags=["Statistics"],
         summary="Get campsite statistics",
         description="Get comprehensive statistics about available campsites")
def get_statistics(service: CampsiteService = Depends(get_campsite_service)):
    """
    Shows how domain models can provide calculated values
    """
    try:
        total_count = service.get_campsite_count()
        states = service.get_available_states()
        
        # Get domain model with calculated statistics
        price_stats = service.get_price_statistics()
        
        # Convert domain statistics to API format
        return StatsResponse(
            total_campsites=total_count,
            available_states=len(states),
            states=states,
            price_range={
                "min_price": price_stats.min_price,
                "max_price": price_stats.max_price,
                "average_price": price_stats.average_price
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )

# Additional endpoint showing domain model business logic
@app.get("/campsites/{campsite_id}/calculate-cost", tags=["Campsites"])
def calculate_trip_cost(
    campsite_id: int = Path(..., gt=0),
    nights: int = Query(..., gt=0, le=30),
    service: CampsiteService = Depends(get_campsite_service)
):
    """
    New endpoint leveraging domain model methods
    """
    total_cost = service.calculate_trip_cost(campsite_id, nights)
    
    if total_cost is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campsite with ID {campsite_id} not found"
        )
    
    return {
        "campsite_id": campsite_id,
        "nights": nights,
        "total_cost": total_cost,
        "currency": "USD"
    }

# Custom exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions"""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc)
    )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors with custom response"""
    return ErrorResponse(
        detail="The requested resource was not found",
        error_code="RESOURCE_NOT_FOUND"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )