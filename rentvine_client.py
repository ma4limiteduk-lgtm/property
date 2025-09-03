import requests
from typing import List, Dict, Optional
import logging

class RentvineClient:
    def __init__(self, subdomain: str, api_key: str, api_secret: str):
        self.base_url = f"https://{subdomain}.rentvine.com/api/manager"
        self.auth = (api_key, api_secret)
        self.headers = {"Content-Type": "application/json"}

    def get_properties(self) -> List[Dict]:
        """Fetch all properties"""
        try:
            response = requests.get(
                f"{self.base_url}/properties",
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return [item["property"] for item in response.json()]
        except Exception as e:
            logging.error(f"Error fetching properties: {e}")
            return []

    def get_units_for_property(self, property_id: int) -> List[Dict]:
        """Fetch units for a specific property"""
        try:
            response = requests.get(
                f"{self.base_url}/properties/{property_id}/units",
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return [item["unit"] for item in response.json()]
        except Exception as e:
            logging.error(f"Error fetching units for property {property_id}: {e}")
            return []

    def get_all_units_with_properties(self) -> List[Dict]:
        """Get all units with their property information"""
        properties = self.get_properties()
        all_units = []
        
        for prop in properties:
            units = self.get_units_for_property(prop["propertyID"])
            for unit in units:
                # Combine property and unit data
                combined = {
                    "property": prop,
                    "unit": unit,
                    "full_address": f"{unit['address']}, {unit['city']}, {unit['stateID']} {unit['postalCode']}",
                    "is_vacant": unit.get("leaseID") is None or unit.get("leaseID") == "",
                    "display_address": unit["address"] + (f" {unit['address2']}" if unit.get("address2") else "")
                }
                all_units.append(combined)
        
        return all_units