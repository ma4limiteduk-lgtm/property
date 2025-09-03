from typing import List, Dict, Optional
from rentvine_client import RentvineClient
import re

class PropertyService:
    def __init__(self, rentvine_client: RentvineClient):
        self.client = rentvine_client
        self._properties_cache = None

    def _get_all_properties(self) -> List[Dict]:
        """Get all properties with caching"""
        if self._properties_cache is None:
            self._properties_cache = self.client.get_all_units_with_properties()
        return self._properties_cache

    def search_by_address(self, address: str) -> Optional[Dict]:
        """Search for a property by address"""
        properties = self._get_all_properties()
        
        # Clean and normalize the search address
        search_address = address.lower().strip()
        
        for prop in properties:
            # Try multiple address formats
            addresses_to_check = [
                prop["unit"]["address"].lower(),
                prop["display_address"].lower(),
                prop["full_address"].lower()
            ]
            
            for addr in addresses_to_check:
                if search_address in addr or addr in search_address:
                    return self._format_property_response(prop)
        
        return None

    def get_available_listings(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get all vacant properties with optional filters"""
        properties = self._get_all_properties()
        vacant_properties = [p for p in properties if p["is_vacant"]]
        
        if filters:
            vacant_properties = self._apply_filters(vacant_properties, filters)
        
        return [self._format_property_response(prop) for prop in vacant_properties]

    def search_properties(self, filters: Dict) -> List[Dict]:
        """Search properties with various filters"""
        properties = self._get_all_properties()
        filtered_properties = self._apply_filters(properties, filters)
        
        return [self._format_property_response(prop) for prop in filtered_properties]

    def _apply_filters(self, properties: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to property list"""
        filtered = properties
        
        if filters.get("min_rent"):
            filtered = [p for p in filtered if float(p["unit"]["rent"]) >= filters["min_rent"]]
        
        if filters.get("max_rent"):
            filtered = [p for p in filtered if float(p["unit"]["rent"]) <= filters["max_rent"]]
        
        if filters.get("beds"):
            filtered = [p for p in filtered if int(p["unit"]["beds"]) >= filters["beds"]]
        
        if filters.get("city"):
            city_filter = filters["city"].lower()
            filtered = [p for p in filtered if city_filter in p["unit"]["city"].lower()]
        
        if filters.get("pets_allowed"):
            # This would need to be implemented based on pet policy data
            pass
        
        return filtered

    def _format_property_response(self, property_data: Dict) -> Dict:
        """Format property data for response"""
        unit = property_data["unit"]
        prop = property_data["property"]
        
        return {
            "property_id": unit["propertyID"],
            "unit_id": unit["unitID"],
            "address": property_data["display_address"],
            "full_address": property_data["full_address"],
            "city": unit["city"],
            "state": unit["stateID"],
            "zip_code": unit["postalCode"],
            "rent": float(unit["rent"]),
            "deposit": float(unit["deposit"]) if unit["deposit"] else 0,
            "beds": int(unit["beds"]),
            "full_baths": int(unit["fullBaths"]),
            "half_baths": int(unit["halfBaths"]),
            "size": int(unit["size"]) if unit["size"] else None,
            "year_built": prop.get("yearBuilt"),
            "is_available": property_data["is_vacant"],
            "property_type": self._get_property_type(prop["propertyTypeID"])
        }

    def _get_property_type(self, type_id: str) -> str:
        """Convert property type ID to readable string"""
        type_map = {
            "1": "Single Family Home",
            "2": "Duplex", 
            "3": "Condo/Apartment",
            "4": "Townhouse",
            "5": "Multi-Family"
        }
        return type_map.get(str(type_id), "Unknown")