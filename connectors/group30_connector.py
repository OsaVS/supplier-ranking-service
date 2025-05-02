"""
Integration connector with Group 30's Blockchain-Based Order Tracking system.
This module handles data exchange between our Supplier Ranking system and
the Blockchain-Based Order Tracking system using Hyperledger Fabric and IPFS.
"""

import json
import logging
import requests
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class Group30Connector:
    """
    Connector class for integrating with Group 30's Blockchain-Based Order Tracking system.
    Responsible for retrieving blockchain data that can be used to evaluate supplier performance.
    """
    
    def __init__(self, base_url: str = "http://blockchain-tracking-service:8000/api/v1/",
                 api_key: Optional[str] = None,
                 timeout: int = 15):
        """
        Initialize the connector with configuration options.
        
        Args:
            base_url: Base URL for the blockchain tracking API
            api_key: API key for authentication if required
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.headers["Content-Type"] = "application/json"
    
    def get_supplier_history(self, supplier_id: int, 
                           from_date: Optional[str] = None,
                           to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve transaction history for a specific supplier from the blockchain.
        
        Args:
            supplier_id: ID of the supplier
            from_date: Optional start date in ISO format (YYYY-MM-DD)
            to_date: Optional end date in ISO format (YYYY-MM-DD)
            
        Returns:
            List of transaction history records
            
        Raises:
            ConnectionError: If unable to connect to the blockchain service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"blockchain/suppliers/{supplier_id}/history/"
            params = {}
            if from_date:
                params["from_date"] = from_date
            if to_date:
                params["to_date"] = to_date
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get supplier history: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 30's blockchain service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from blockchain service")
            raise ValueError("Invalid response from Group 30's blockchain service")
    
    def get_transaction_details(self, transaction_hash: str) -> Dict[str, Any]:
        """
        Retrieve detailed information about a specific transaction.
        
        Args:
            transaction_hash: Blockchain hash of the transaction
            
        Returns:
            Dictionary containing transaction details
            
        Raises:
            ConnectionError: If unable to connect to the blockchain service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"blockchain/transactions/{transaction_hash}/"
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get transaction details: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 30's blockchain service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from blockchain service")
            raise ValueError("Invalid response from Group 30's blockchain service")
    
    def get_supplier_performance_metrics(self, supplier_id: int) -> Dict[str, Any]:
        """
        Retrieve blockchain-verified performance metrics for a supplier.
        
        Args:
            supplier_id: ID of the supplier
            
        Returns:
            Dictionary containing performance metrics
            
        Raises:
            ConnectionError: If unable to connect to the blockchain service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"blockchain/suppliers/{supplier_id}/metrics/"
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get supplier performance metrics: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 30's blockchain service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from blockchain service")
            raise ValueError("Invalid response from Group 30's blockchain service")
    
    def verify_transaction(self, transaction_id: int) -> Dict[str, Any]:
        """
        Verify a transaction against the blockchain to confirm its authenticity.
        
        Args:
            transaction_id: ID of the transaction from our system
            
        Returns:
            Dictionary containing verification result
            
        Raises:
            ConnectionError: If unable to connect to the blockchain service
            ValueError: If the response is invalid
        """
        try:
            endpoint = "blockchain/verify/"
            data = {"transaction_id": transaction_id}
            
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to verify transaction: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 30's blockchain service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from blockchain service")
            raise ValueError("Invalid response from Group 30's blockchain service")
    
    def get_document_hash(self, document_ipfs_hash: str) -> Dict[str, Any]:
        """
        Retrieve document information from IPFS using the hash.
        
        Args:
            document_ipfs_hash: IPFS hash of the document
            
        Returns:
            Dictionary containing document information
            
        Raises:
            ConnectionError: If unable to connect to the IPFS service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"ipfs/documents/{document_ipfs_hash}/"
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get document from IPFS: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 30's IPFS service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from IPFS service")
            raise ValueError("Invalid response from Group 30's IPFS service")
    
    def get_supplier_compliance_documents(self, supplier_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve compliance documents for a supplier stored on IPFS.
        
        Args:
            supplier_id: ID of the supplier
            
        Returns:
            List of documents with their IPFS hashes
            
        Raises:
            ConnectionError: If unable to connect to the blockchain service
            ValueError: If the response is invalid
        """
        try:
            endpoint = f"blockchain/suppliers/{supplier_id}/documents/"
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get supplier compliance documents: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 30's blockchain service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from blockchain service")
            raise ValueError("Invalid response from Group 30's blockchain service")
    
    def record_supplier_ranking(self, supplier_id: int, ranking_data: Dict[str, Any]) -> str:
        """
        Record supplier ranking information on the blockchain for immutability.
        
        Args:
            supplier_id: ID of the supplier
            ranking_data: Data about the supplier ranking
            
        Returns:
            Transaction hash for the recorded data
            
        Raises:
            ConnectionError: If unable to connect to the blockchain service
            ValueError: If the response is invalid
        """
        try:
            endpoint = "blockchain/records/"
            data = {
                "supplier_id": supplier_id,
                "ranking_data": ranking_data,
                "recorded_at": datetime.now().isoformat(),
                "record_type": "supplier_ranking"
            }
            
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            return result["transaction_hash"]
            
        except requests.RequestException as e:
            logger.error(f"Failed to record supplier ranking: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 30's blockchain service: {str(e)}")
        except (json.JSONDecodeError, KeyError):
            logger.error("Invalid JSON response from blockchain service")
            raise ValueError("Invalid response from Group 30's blockchain service")
    
    def get_blockchain_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the blockchain network.
        
        Returns:
            Dictionary containing blockchain statistics
            
        Raises:
            ConnectionError: If unable to connect to the blockchain service
            ValueError: If the response is invalid
        """
        try:
            endpoint = "blockchain/stats/"
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get blockchain stats: {str(e)}")
            raise ConnectionError(f"Could not connect to Group 30's blockchain service: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from blockchain service")
            raise ValueError("Invalid response from Group 30's blockchain service")