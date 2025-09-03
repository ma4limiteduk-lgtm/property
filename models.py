from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class PropertyQueryRequest(BaseModel):
    query_type: str  # "property_details", "available_listings", "search", "budget_filter"
    user_message: str
    address: Optional[str] = None
    property_id: Optional[int] = None
    min_rent: Optional[float] = None
    max_rent: Optional[float] = None
    beds: Optional[int] = None
    city: Optional[str] = None
    extracted_info: Optional[Dict[str, Any]] = None

class PropertyResponse(BaseModel):
    success: bool
    property_found: Optional[bool] = None
    data: Optional[Dict[str, Any]] = None
    response_text: str
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None