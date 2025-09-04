from fastapi import FastAPI, HTTPException
from models import PropertyQueryRequest, PropertyResponse
from property_service import PropertyService
from rentvine_client import RentvineClient
from config import RENTVINE_SUBDOMAIN, RENTVINE_API_KEY, RENTVINE_API_SECRET
from typing import Dict, List
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Property API for Alison",
    description="FastAPI service for property management and Rentvine integration",
    version="1.0.0"
)

# Global variables for services
rentvine_client = None
property_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global rentvine_client, property_service
    
    try:
        logger.info("Starting up Property API...")
        
        # Check if we have required environment variables
        if not all([RENTVINE_SUBDOMAIN, RENTVINE_API_KEY, RENTVINE_API_SECRET]):
            logger.error("Missing required environment variables")
            raise ValueError("Missing Rentvine configuration")
        
        # Initialize services
        rentvine_client = RentvineClient(
            subdomain=RENTVINE_SUBDOMAIN,
            api_key=RENTVINE_API_KEY,
            api_secret=RENTVINE_API_SECRET
        )
        
        property_service = PropertyService(rentvine_client)
        
        # Test connection
        connection_test = rentvine_client.test_connection()
        if connection_test["success"]:
            logger.info("Rentvine connection test successful")
        else:
            logger.error(f"Rentvine connection test failed: {connection_test['message']}")
        
        logger.info("Property API startup complete")
        
    except Exception as e:
        logger.error(f"Failed to start Property API: {e}")
        # Don't raise here - let the app start even if Rentvine is down

@app.post("/api/property-query", response_model=PropertyResponse)
async def handle_property_query(request: PropertyQueryRequest):
    """Main endpoint for handling all property queries from Alison"""
    
    if not property_service:
        return PropertyResponse(
            success=False,
            response_text="Property service is not initialized. Please check server logs.",
            error="Service initialization error"
        )
    
    try:
        logger.info(f"Processing query: {request.query_type} - {request.user_message}")
        
        if request.query_type == "property_details":
            return handle_property_details(request)
        elif request.query_type == "available_listings":
            return handle_available_listings(request)
        elif request.query_type == "search":
            return handle_property_search(request)
        elif request.query_type == "budget_filter":
            return handle_budget_filter(request)
        else:
            return PropertyResponse(
                success=False,
                response_text="I'm not sure how to handle that type of query.",
                error="Unknown query type"
            )
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return PropertyResponse(
            success=False,
            response_text="I'm having trouble accessing property information right now. Please try again.",
            error=str(e)
        )

def handle_property_details(request: PropertyQueryRequest) -> PropertyResponse:
    """Handle specific property detail requests"""
    if not request.address:
        return PropertyResponse(
            success=False,
            response_text="I need an address to look up property details."
        )
    
    try:
        property_data = property_service.search_by_address(request.address)
        
        if not property_data:
            return PropertyResponse(
                success=False,
                property_found=False,
                response_text=f"I couldn't find a property at {request.address}. Could you double-check the address?"
            )
        
        # Generate response text based on what was asked
        if "bed" in request.user_message.lower() or "bath" in request.user_message.lower():
            response_text = f"{property_data['address']} has {property_data['beds']} bedrooms and {property_data['full_baths']} full bathrooms"
            if property_data['half_baths'] > 0:
                response_text += f" plus {property_data['half_baths']} half bath"
            response_text += "."
        else:
            response_text = f"Here are the details for {property_data['address']}: {property_data['beds']} bed/{property_data['full_baths']} bath, {property_data['size']} sq ft, ${property_data['rent']}/month."
        
        return PropertyResponse(
            success=True,
            property_found=True,
            data=property_data,
            response_text=response_text
        )
        
    except Exception as e:
        logger.error(f"Error in handle_property_details: {e}")
        return PropertyResponse(
            success=False,
            response_text="Sorry, I'm having trouble looking up that property right now.",
            error=str(e)
        )

def handle_available_listings(request: PropertyQueryRequest) -> PropertyResponse:
    """Handle requests for available properties"""
    try:
        filters = {}
        if request.min_rent:
            filters["min_rent"] = request.min_rent
        if request.max_rent:
            filters["max_rent"] = request.max_rent
        if request.beds:
            filters["beds"] = request.beds
        if request.city:
            filters["city"] = request.city
        
        available_properties = property_service.get_available_listings(filters)
        
        if not available_properties:
            return PropertyResponse(
                success=True,
                response_text="I don't have any available properties that match your criteria right now."
            )
        
        # Format response
        if len(available_properties) == 1:
            prop = available_properties[0]
            response_text = f"I found 1 available property: {prop['address']} - {prop['beds']} bed/{prop['full_baths']} bath for ${prop['rent']}/month."
        else:
            response_text = f"I found {len(available_properties)} available properties. Here are your options:\n"
            for prop in available_properties[:5]:  # Limit to first 5
                response_text += f"• {prop['address']} - {prop['beds']} bed/{prop['full_baths']} bath, ${prop['rent']}/month\n"
        
        return PropertyResponse(
            success=True,
            data={"properties": available_properties},
            response_text=response_text
        )
        
    except Exception as e:
        logger.error(f"Error in handle_available_listings: {e}")
        return PropertyResponse(
            success=False,
            response_text="Sorry, I'm having trouble finding available properties right now.",
            error=str(e)
        )

def handle_property_search(request: PropertyQueryRequest) -> PropertyResponse:
    """Handle general property search requests"""
    try:
        filters = {}
        if request.min_rent:
            filters["min_rent"] = request.min_rent
        if request.max_rent:
            filters["max_rent"] = request.max_rent
        if request.beds:
            filters["beds"] = request.beds
        if request.city:
            filters["city"] = request.city
        
        properties = property_service.search_properties(filters)
        
        if not properties:
            return PropertyResponse(
                success=True,
                response_text="I couldn't find any properties matching your search criteria."
            )
        
        response_text = f"I found {len(properties)} properties matching your search:\n"
        for prop in properties[:5]:  # Limit to first 5
            availability = "Available" if prop["is_available"] else "Occupied"
            response_text += f"• {prop['address']} - {prop['beds']} bed/{prop['full_baths']} bath, ${prop['rent']}/month ({availability})\n"
        
        return PropertyResponse(
            success=True,
            data={"properties": properties},
            response_text=response_text
        )
        
    except Exception as e:
        logger.error(f"Error in handle_property_search: {e}")
        return PropertyResponse(
            success=False,
            response_text="Sorry, I'm having trouble searching properties right now.",
            error=str(e)
        )

def handle_budget_filter(request: PropertyQueryRequest) -> PropertyResponse:
    """Handle budget-based filtering"""
    try:
        filters = {
            "min_rent": request.min_rent,
            "max_rent": request.max_rent
        }
        
        # Include available properties only for budget searches
        available_properties = property_service.get_available_listings(filters)
        
        if not available_properties:
            return PropertyResponse(
                success=True,
                response_text=f"I don't have any available properties in the ${request.min_rent}-${request.max_rent} range right now."
            )
        
        response_text = f"I found {len(available_properties)} available properties in your budget range:\n"
        for prop in available_properties:
            response_text += f"• {prop['address']} - ${prop['rent']}/month ({prop['beds']} bed/{prop['full_baths']} bath)\n"
        
        return PropertyResponse(
            success=True,
            data={"properties": available_properties},
            response_text=response_text
        )
        
    except Exception as e:
        logger.error(f"Error in handle_budget_filter: {e}")
        return PropertyResponse(
            success=False,
            response_text="Sorry, I'm having trouble filtering properties by budget right now.",
            error=str(e)
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "api_version": "1.0.0"
    }
    
    if property_service:
        health_status["property_service"] = "initialized"
        if rentvine_client:
            connection_test = rentvine_client.test_connection()
            health_status["rentvine_connection"] = connection_test["success"]
    else:
        health_status["property_service"] = "not_initialized"
        health_status["rentvine_connection"] = False
    
    return health_status

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check configuration"""
    return {
        "status": "running",
        "environment": {
            "rentvine_subdomain": RENTVINE_SUBDOMAIN,
            "has_api_key": bool(RENTVINE_API_KEY),
            "has_api_secret": bool(RENTVINE_API_SECRET),
        },
        "services": {
            "rentvine_client_initialized": rentvine_client is not None,
            "property_service_initialized": property_service is not None,
        }
    }

@app.get("/test-rentvine")
async def test_rentvine():
    """Test Rentvine connection"""
    if not rentvine_client:
        return {
            "success": False,
            "error": "Rentvine client not initialized"
        }
    
    try:
        connection_test = rentvine_client.test_connection()
        
        if connection_test["success"]:
            # Try to get a small sample of data
            properties = rentvine_client.get_properties()
            return {
                "success": True,
                "connection_test": connection_test,
                "property_count": len(properties),
                "sample_property": properties[0] if properties else None
            }
        else:
            return {
                "success": False,
                "connection_test": connection_test
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
