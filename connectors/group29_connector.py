"""
Integration connector with Group 29's Intelligent Demand Forecasting system.
This module handles data exchange between our Supplier Ranking system and
the Demand Forecasting system using Time Series Analysis, Prophet, and LSTMs.
"""

import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

# Set up logging
logger = logging.getLogger(__name__)

class Group29Connector:
    """
    Connector class for integrating with Group 29's Demand Forecasting system.
    Responsible for retrieving forecasts that can influence supplier rankings.
    """
    
    def __init__(self, base_url: str = "http://demand-forecasting-service:8000/api/v1/",
                 api_key: Optional[str] = None,
                 timeout: int = 10):
        """
        Initialize the connector with configuration options.
        
        Args:
            base_url: Base URL for the demand forecasting API
            api_key: API key for authentication if required
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.headers["Content-Type"] = "application/json"
    
    def get_product_demand_forecast(self, product_id: int, 
                                    horizon_days: int = 90) -> Dict[str, Any]:
        """
        Retrieve demand forecast for a specific product.
        
        Args:
            product_id: ID of the product
            horizon_days: Number of days to forecast ahead
            
        Returns:
            Dictionary containing forecast data
            
        Raises:
            ConnectionError: If unable to connect to the forecasting service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"forecasts/products/{product_id}/"
            params = {"horizon_days": horizon_days}
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get product demand forecast: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 29's forecasting service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from forecasting service")
            raise ValueError("Invalid response from Group 29's forecasting service")
    
    def get_supplier_demand_forecast(self, supplier_id: int,
                                    horizon_days: int = 90) -> Dict[str, Any]:
        """
        Retrieve aggregated demand forecast for all products from a specific supplier.
        
        Args:
            supplier_id: ID of the supplier
            horizon_days: Number of days to forecast ahead
            
        Returns:
            Dictionary containing forecast data
            
        Raises:
            ConnectionError: If unable to connect to the forecasting service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"forecasts/suppliers/{supplier_id}/"
            params = {"horizon_days": horizon_days}
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get supplier demand forecast: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 29's forecasting service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from forecasting service")
            raise ValueError("Invalid response from Group 29's forecasting service")
    
    def get_forecast_confidence(self, forecast_id: int) -> Dict[str, Any]:
        """
        Get confidence metrics for a specific forecast.
        
        Args:
            forecast_id: ID of the forecast
            
        Returns:
            Dictionary containing confidence metrics
        """
        try:
            endpoint = f"forecasts/{forecast_id}/confidence/"
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get forecast confidence metrics: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 29's forecasting service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from forecasting service")
            raise ValueError("Invalid response from Group 29's forecasting service")
    
    def get_seasonal_factors(self, product_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get seasonal demand factors that might influence supplier requirements.
        
        Args:
            product_id: Optional filter by product ID
            
        Returns:
            Dictionary containing seasonal factors
        """
        try:
            endpoint = "forecasts/seasonal-factors/"
            params = {}
            if product_id:
                params["product_id"] = product_id
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get seasonal factors: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 29's forecasting service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from forecasting service")
            raise ValueError("Invalid response from Group 29's forecasting service")
    
    def calculate_supply_risk(self, supplier_id: int) -> Dict[str, Any]:
        """
        Calculate supply risk based on demand forecasts and supplier capacity.
        
        Args:
            supplier_id: ID of the supplier
            
        Returns:
            Dictionary containing risk assessment
        """
        try:
            endpoint = "analysis/supply-risk/"
            data = {"supplier_id": supplier_id}
            
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to calculate supply risk: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 29's forecasting service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from forecasting service")
            raise ValueError("Invalid response from Group 29's forecasting service")
    
    def get_forecast_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current forecasts to help with supplier ranking.
        
        Returns:
            Dictionary containing forecast summaries
        """
        try:
            endpoint = "forecasts/summary/"
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get forecast summary: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 29's forecasting service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from forecasting service")
            raise ValueError("Invalid response from Group 29's forecasting service")
    
    def notify_critical_supplier(self, supplier_id: int, 
                               forecast_data: Dict[str, Any]) -> bool:
        """
        Notify the forecasting system about a critical supplier based on our ranking.
        
        Args:
            supplier_id: ID of the critical supplier
            forecast_data: Data about why this supplier is critical
            
        Returns:
            True if notification was successful
        """
        try:
            endpoint = "notifications/critical-supplier/"
            data = {
                "supplier_id": supplier_id,
                "forecast_data": forecast_data,
                "notified_at": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to notify critical supplier: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 29's forecasting service: {str(e)}")
        
        return False