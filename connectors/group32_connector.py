"""
Integration connector with Group 32's Logistics & Route Optimization system.
This module handles data exchange between our Supplier Ranking system and
the Logistics & Route Optimization system using Google OR-Tools and Dijkstra's Algorithm.
"""

import json
import logging
import requests
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class Group32Connector:
    """
    Connector class for integrating with Group 32's Logistics & Route Optimization system.
    Responsible for retrieving logistics data that affects supplier evaluations.
    """
    
    def __init__(self, base_url: str = "http://logistics-optimization-service:8000/api/v1/",
                 api_key: Optional[str] = None,
                 timeout: int = 10):
        """
        Initialize the connector with configuration options.
        
        Args:
            base_url: Base URL for the logistics API
            api_key: API key for authentication if required
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.headers["Content-Type"] = "application/json"
    
    def get_supplier_logistics_score(self, supplier_id: int) -> Dict[str, Any]:
        """
        Retrieve logistics optimization score for a specific supplier.
        
        Args:
            supplier_id: ID of the supplier
            
        Returns:
            Dictionary containing logistics score and metrics
            
        Raises:
            ConnectionError: If unable to connect to the logistics service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"logistics/suppliers/{supplier_id}/score/"
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get supplier logistics score: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 32's logistics service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from logistics service")
            raise ValueError("Invalid response from Group 32's logistics service")
    
    def get_route_efficiency(self, supplier_id: int, destination_id: int) -> Dict[str, Any]:
        """
        Get efficiency metrics for routes between a supplier and destination.
        
        Args:
            supplier_id: ID of the supplier
            destination_id: ID of the destination warehouse/facility
            
        Returns:
            Dictionary containing route efficiency metrics
            
        Raises:
            ConnectionError: If unable to connect to the logistics service
            ValueError: If the response is invalid
        """
        try:
            endpoint = "logistics/routes/efficiency/"
            params = {
                "supplier_id": supplier_id,
                "destination_id": destination_id
            }
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get route efficiency: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 32's logistics service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from logistics service")
            raise ValueError("Invalid response from Group 32's logistics service")
    
    def get_transportation_costs(self, supplier_id: int, product_ids: List[int] = None) -> Dict[str, Any]:
        """
        Get transportation cost estimates for products from a supplier.
        
        Args:
            supplier_id: ID of the supplier
            product_ids: Optional list of product IDs to filter by
            
        Returns:
            Dictionary containing transportation cost data
            
        Raises:
            ConnectionError: If unable to connect to the logistics service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"logistics/suppliers/{supplier_id}/transportation-costs/"
            params = {}
            if product_ids:
                params["product_ids"] = ",".join(map(str, product_ids))
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get transportation costs: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 32's logistics service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from logistics service")
            raise ValueError("Invalid response from Group 32's logistics service")
    
    def get_delivery_time_estimates(self, supplier_id: int, product_ids: List[int] = None) -> Dict[str, Any]:
        """
        Get estimated delivery times for products from a supplier.
        
        Args:
            supplier_id: ID of the supplier
            product_ids: Optional list of product IDs to filter by
            
        Returns:
            Dictionary containing delivery time estimates
            
        Raises:
            ConnectionError: If unable to connect to the logistics service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"logistics/suppliers/{supplier_id}/delivery-estimates/"
            params = {}
            if product_ids:
                params["product_ids"] = ",".join(map(str, product_ids))
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get delivery time estimates: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 32's logistics service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from logistics service")
            raise ValueError("Invalid response from Group 32's logistics service")
    
    def get_logistics_disruptions(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get current logistics disruptions that might affect supplier performance.
        
        Args:
            region: Optional region code to filter disruptions
            
        Returns:
            List of disruption events
            
        Raises:
            ConnectionError: If unable to connect to the logistics service
            ValueError: If the response is invalid
        """
        try:
            endpoint = "logistics/disruptions/"
            params = {}
            if region:
                params["region"] = region
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get logistics disruptions: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 32's logistics service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from logistics service")
            raise ValueError("Invalid response from Group 32's logistics service")
    
    def get_carbon_footprint(self, supplier_id: int) -> Dict[str, Any]:
        """
        Get carbon footprint metrics for a supplier's logistics operations.
        
        Args:
            supplier_id: ID of the supplier
            
        Returns:
            Dictionary containing carbon footprint data
            
        Raises:
            ConnectionError: If unable to connect to the logistics service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"logistics/suppliers/{supplier_id}/carbon-footprint/"
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get carbon footprint: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 32's logistics service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from logistics service")
            raise ValueError("Invalid response from Group 32's logistics service")
    
    def optimize_supplier_selection(self, product_id: int, 
                                  quantity: int,
                                  delivery_location_id: int) -> Dict[str, Any]:
        """
        Get logistics-optimized supplier recommendations for a product order.
        
        Args:
            product_id: ID of the product
            quantity: Order quantity
            delivery_location_id: ID of the delivery location
            
        Returns:
            Dictionary containing optimized supplier recommendations
            
        Raises:
            ConnectionError: If unable to connect to the logistics service
            ValueError: If the response is invalid
        """
        try:
            endpoint = "logistics/optimize/supplier-selection/"
            data = {
                "product_id": product_id,
                "quantity": quantity,
                "delivery_location_id": delivery_location_id
            }
            
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to optimize supplier selection: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 32's logistics service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from logistics service")
            raise ValueError("Invalid response from Group 32's logistics service")
    
    def get_warehouse_capacities(self) -> Dict[str, Any]:
        """
        Get current warehouse capacities to factor into supplier rankings.
        
        Returns:
            Dictionary containing warehouse capacity information
            
        Raises:
            ConnectionError: If unable to connect to the logistics service
            ValueError: If the response is invalid
        """
        try:
            endpoint = "logistics/warehouses/capacities/"
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get warehouse capacities: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 32's logistics service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from logistics service")
            raise ValueError("Invalid response from Group 32's logistics service")
    
    def update_supplier_logistics_profile(self, supplier_id: int, profile_data: Dict[str, Any]) -> bool:
        """
        Update logistics profile for a supplier based on ranking changes.
        
        Args:
            supplier_id: ID of the supplier
            profile_data: Updated logistics profile data
            
        Returns:
            True if update was successful
            
        Raises:
            ConnectionError: If unable to connect to the logistics service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"logistics/suppliers/{supplier_id}/profile/"
            
            response = requests.put(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=profile_data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to update supplier logistics profile: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 32's logistics service: {str(e)}")
        
        return False
    
    def get_route_analytics(self, supplier_id: int) -> Dict[str, Any]:
        """
        Get analytics about the supplier's logistics routes.
        
        Args:
            supplier_id: ID of the supplier
            
        Returns:
            Dictionary containing route analytics data
            
        Raises:
            ConnectionError: If unable to connect to the logistics service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"logistics/suppliers/{supplier_id}/route-analytics/"
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get route analytics: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 32's logistics service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from logistics service")
            raise ValueError("Invalid response from Group 32's logistics service")