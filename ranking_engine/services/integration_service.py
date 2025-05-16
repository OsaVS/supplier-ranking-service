"""
Integration Service - Handles integration with other system components

This service manages communications with the other subsystems in the
Intelligent and Smart Supply Chain Management System (Groups 29, 30, and 32).
"""

import json
import logging
import requests
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

# Import our internal models - we don't directly import external models
from api.models import (
    SupplierRanking,
    SupplierPerformanceCache,
    RankingEvent
)

from ranking_engine.utils.kafka_utils import KafkaProducer, KafkaConsumer

logger = logging.getLogger(__name__)


class IntegrationService:
    """
    Service for integrating with other subsystems in the
    Intelligent and Smart Supply Chain Management System
    """
    
    # API endpoints for external services
    USER_SERVICE_API = getattr(settings, 'USER_SERVICE_API', 'http://localhost:8000/api/users/')
    ORDER_SERVICE_API = getattr(settings, 'ORDER_SERVICE_API', 'http://localhost:8001/api/orders/')
    WAREHOUSE_SERVICE_API = getattr(settings, 'WAREHOUSE_SERVICE_API', 'http://localhost:8002/api/warehouse/')
    
    # API endpoints for other subsystems
    GROUP29_FORECAST_API = getattr(settings, 'GROUP29_FORECAST_API', 'http://localhost:8003/api/forecasts/')
    GROUP30_BLOCKCHAIN_API = getattr(settings, 'GROUP30_BLOCKCHAIN_API', 'http://localhost:8004/api/blockchain/')
    GROUP32_LOGISTICS_API = getattr(settings, 'GROUP32_LOGISTICS_API', 'http://localhost:8005/api/logistics/')
    
    # Kafka topics
    KAFKA_TOPIC_RANKINGS = 'supplier_rankings'
    KAFKA_TOPIC_FORECASTS = 'demand_forecasts'
    KAFKA_TOPIC_BLOCKCHAIN = 'blockchain_transactions'
    KAFKA_TOPIC_LOGISTICS = 'logistics_data'
    
    @staticmethod
    def get_supplier_info(supplier_id):
        """
        Fetches supplier information from User Service
        
        Args:
            supplier_id: ID of the supplier
            
        Returns:
            dict: Supplier information
        """
        try:
            response = requests.get(
                f"{IntegrationService.USER_SERVICE_API}suppliers/{supplier_id}/",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch supplier info: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching supplier info: {str(e)}")
            return None
    
    @staticmethod
    def get_supplier_order_metrics(supplier_id, start_date, end_date):
        """
        Fetches supplier order metrics from Order Management Service
        
        Args:
            supplier_id: ID of the supplier
            start_date: Start date for metrics (YYYY-MM-DD)
            end_date: End date for metrics (YYYY-MM-DD)
            
        Returns:
            dict: Order metrics data
        """
        try:
            params = {
                'start_date': start_date,
                'end_date': end_date
            }
            
            response = requests.get(
                f"{IntegrationService.ORDER_SERVICE_API}suppliers/{supplier_id}/metrics/",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch order metrics: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching order metrics: {str(e)}")
            return None
    
    @staticmethod
    def get_supplier_price_metrics(supplier_id):
        """
        Fetches supplier price metrics from Warehouse Management Service
        
        Args:
            supplier_id: ID of the supplier
            
        Returns:
            dict: Price metrics data
        """
        try:
            response = requests.get(
                f"{IntegrationService.WAREHOUSE_SERVICE_API}suppliers/{supplier_id}/price-metrics/",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch price metrics: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching price metrics: {str(e)}")
            return None
    
    @staticmethod
    def get_supplier_service_metrics(supplier_id):
        """
        Fetches supplier service metrics from User Service
        
        Args:
            supplier_id: ID of the supplier
            
        Returns:
            dict: Service metrics data
        """
        try:
            response = requests.get(
                f"{IntegrationService.USER_SERVICE_API}suppliers/{supplier_id}/service-metrics/",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch service metrics: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching service metrics: {str(e)}")
            return None
    
    @staticmethod
    def fetch_demand_forecasts(product_category=None, days_ahead=30):
        """
        Fetches demand forecasts from Group 29's Intelligent Demand Forecasting
        
        Args:
            product_category: Optional category to filter forecasts
            days_ahead: Number of days ahead to forecast
            
        Returns:
            dict: Demand forecast data
        """
        try:
            params = {
                'days_ahead': days_ahead
            }
            
            if product_category:
                params['category'] = product_category
                
            response = requests.get(
                IntegrationService.GROUP29_FORECAST_API,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch forecasts: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching demand forecasts: {str(e)}")
            
            # Fallback to sample forecast data
            return {
                'status': 'fallback',
                'message': 'Using fallback data due to connection issue',
                'forecasts': []
            }
    
    @staticmethod
    def get_blockchain_order_data(transaction_id=None, supplier_id=None, days=30):
        """
        Fetches blockchain-verified order data from Group 30
        
        Args:
            transaction_id: Optional specific transaction ID
            supplier_id: Optional supplier ID to filter
            days: Number of days of history to retrieve
            
        Returns:
            dict: Blockchain order data
        """
        try:
            params = {
                'days': days
            }
            
            if transaction_id:
                params['transaction_id'] = transaction_id
                
            if supplier_id:
                params['supplier_id'] = supplier_id
                
            response = requests.get(
                IntegrationService.GROUP30_BLOCKCHAIN_API + 'orders/',
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch blockchain data: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching blockchain data: {str(e)}")
            return None
    
    @staticmethod
    def verify_transaction_on_blockchain(transaction_id):
        """
        Verifies a transaction on the blockchain
        
        Args:
            transaction_id: Transaction ID to verify
            
        Returns:
            dict: Verification result
        """
        try:
            response = requests.get(
                f"{IntegrationService.GROUP30_BLOCKCHAIN_API}verify/{transaction_id}/",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to verify transaction: {response.status_code}")
                return {'verified': False, 'error': 'Verification failed'}
                
        except requests.RequestException as e:
            logger.error(f"Error verifying transaction: {str(e)}")
            return {'verified': False, 'error': str(e)}
    
    @staticmethod
    def get_logistics_data(supplier_id=None, days=30):
        """
        Fetches logistics data from Group 32's Logistics & Route Optimization
        
        Args:
            supplier_id: Optional supplier ID to filter
            days: Number of days of history to retrieve
            
        Returns:
            dict: Logistics performance data
        """
        try:
            params = {
                'days': days
            }
            
            if supplier_id:
                params['supplier_id'] = supplier_id
                
            response = requests.get(
                IntegrationService.GROUP32_LOGISTICS_API + 'performance/',
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch logistics data: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching logistics data: {str(e)}")
            return None
    
    @staticmethod
    def update_performance_from_external_data():
        """
        Updates supplier performance records using data from external systems
        
        Returns:
            dict: Summary of updates
        """
        updates = {
            'blockchain_updates': 0,
            'logistics_updates': 0,
            'forecast_updates': 0,
            'errors': []
        }
        
        # Get active suppliers from User Service
        try:
            # Try active endpoint first
            response = requests.get(
                f"{IntegrationService.USER_SERVICE_API}suppliers/active/",
                timeout=10
            )
            
            # If 404, try fallback to main suppliers with query param
            if response.status_code == 404:
                response = requests.get(
                    f"{IntegrationService.USER_SERVICE_API}suppliers/",
                    params={"active": "true"},
                    timeout=10
                )
            
            if response.status_code != 200:
                updates['errors'].append(f"Failed to fetch active suppliers: {response.status_code}")
                return updates
                
            # Handle different response formats
            suppliers_data = response.json()
            if isinstance(suppliers_data, dict) and 'suppliers' in suppliers_data:
                suppliers = suppliers_data['suppliers']
            elif isinstance(suppliers_data, list):
                suppliers = suppliers_data
            else:
                suppliers = suppliers_data.get('suppliers', [])
                
            today = timezone.now().date()
            
            for supplier in suppliers:
                supplier_id = supplier.get('id')
                supplier_name = supplier.get('name')
                
                try:
                    # Get blockchain data for supplier
                    blockchain_data = IntegrationService.get_blockchain_order_data(
                        supplier_id=supplier_id,
                        days=30
                    )
                    
                    if blockchain_data and 'orders' in blockchain_data:
                        # Process blockchain order data for the supplier
                        # We don't update Transaction directly since it's in another service
                        # Instead, we'll store this information in our local cache
                        updates['blockchain_updates'] += 1
                    
                    # Get logistics data for supplier
                    logistics_data = IntegrationService.get_logistics_data(
                        supplier_id=supplier_id,
                        days=30
                    )
                    
                    if logistics_data and 'performance' in logistics_data:
                        perf_data = logistics_data['performance']
                        
                        # Update or create performance cache with logistics data
                        performance_cache, created = SupplierPerformanceCache.objects.update_or_create(
                            supplier_id=supplier_id,
                            date=today,
                            defaults={
                                'supplier_name': supplier_name,
                                'on_time_delivery_rate': perf_data.get('on_time_rate', 90),
                                'average_delay_days': perf_data.get('average_delay', 0),
                                'fill_rate': perf_data.get('fill_rate', 95),
                                'order_accuracy': perf_data.get('order_accuracy', 98)
                            }
                        )
                        
                        updates['logistics_updates'] += 1
                        
                    # Get demand forecasts (general, not supplier-specific)
                    forecast_data = IntegrationService.fetch_demand_forecasts(days_ahead=90)
                    
                    if forecast_data and 'forecasts' in forecast_data:
                        # Process forecasts
                        # This could involve updating internal metrics or preparing
                        # for the Q-Learning algorithm
                        updates['forecast_updates'] += 1
                        
                except Exception as e:
                    logger.error(f"Error updating supplier {supplier_id}: {str(e)}")
                    updates['errors'].append(f"Supplier {supplier_id}: {str(e)}")
                    
        except requests.RequestException as e:
            logger.error(f"Error fetching active suppliers: {str(e)}")
            updates['errors'].append(f"Failed to fetch active suppliers: {str(e)}")
            
        return updates
    
    @staticmethod
    def publish_rankings_to_kafka():
        """
        Publishes the latest supplier rankings to Kafka
        for consumption by other subsystems
        
        Returns:
            bool: Success status
        """
        try:
            # Get today's rankings
            today = timezone.now().date()
            rankings = SupplierRanking.objects.filter(date=today)
            
            if not rankings:
                logger.warning("No rankings available to publish")
                return False
                
            # Prepare message payload
            payload = {
                'timestamp': timezone.now().isoformat(),
                'ranking_date': today.isoformat(),
                'rankings': []
            }
            
            for ranking in rankings:
                payload['rankings'].append({
                    'supplier_id': ranking.supplier_id,
                    'supplier_name': ranking.supplier_name,
                    'rank': ranking.rank,
                    'overall_score': float(ranking.overall_score),
                    'quality_score': float(ranking.quality_score),
                    'delivery_score': float(ranking.delivery_score),
                    'price_score': float(ranking.price_score),
                    'service_score': float(ranking.service_score)
                })
                
            # Publish to Kafka
            producer = KafkaProducer()
            producer.produce(
                IntegrationService.KAFKA_TOPIC_RANKINGS,
                json.dumps(payload)
            )
            
            logger.info(f"Published {len(rankings)} rankings to Kafka")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing rankings to Kafka: {str(e)}")
            return False
    
    @staticmethod
    def consume_external_data_from_kafka(timeout_seconds=30):
        """
        Consumes data from Kafka topics and processes it
        
        Args:
            timeout_seconds: Time to listen for messages
            
        Returns:
            dict: Summary of processed messages
        """
        summary = {
            'forecasts_processed': 0,
            'blockchain_processed': 0,
            'logistics_processed': 0,
            'errors': []
        }
        
        try:
            # Initialize consumer for multiple topics
            consumer = KafkaConsumer(
                [
                    IntegrationService.KAFKA_TOPIC_FORECASTS,
                    IntegrationService.KAFKA_TOPIC_BLOCKCHAIN,
                    IntegrationService.KAFKA_TOPIC_LOGISTICS
                ]
            )
            
            # Process messages for the specified duration
            end_time = datetime.now() + timedelta(seconds=timeout_seconds)
            today = timezone.now().date()
            
            while datetime.now() < end_time:
                message = consumer.poll(timeout=1.0)
                
                if not message:
                    continue
                    
                try:
                    # Process based on topic
                    topic = message.topic()
                    data = json.loads(message.value())
                    
                    if topic == IntegrationService.KAFKA_TOPIC_FORECASTS:
                        # Process forecast data
                        # Example: Update internal demand forecasts
                        summary['forecasts_processed'] += 1
                        
                    elif topic == IntegrationService.KAFKA_TOPIC_BLOCKCHAIN:
                        # Process blockchain transaction data
                        if 'transaction_id' in data and 'blockchain_hash' in data:
                            # We don't directly update Transaction model anymore
                            # Instead, we could store this reference in a local cache or log
                            RankingEvent.objects.create(
                                event_type='DATA_FETCHED',
                                description=f"Received blockchain verification for transaction {data['transaction_id']}",
                                metadata={
                                    'transaction_id': data['transaction_id'],
                                    'blockchain_hash': data['blockchain_hash']
                                }
                            )
                            summary['blockchain_processed'] += 1
                                
                    elif topic == IntegrationService.KAFKA_TOPIC_LOGISTICS:
                        # Process logistics data
                        if 'supplier_id' in data and 'delivery_metrics' in data:
                            metrics = data['delivery_metrics']
                            supplier_id = data['supplier_id']
                            
                            # Get supplier name from User Service
                            supplier_info = IntegrationService.get_supplier_info(supplier_id)
                            supplier_name = supplier_info.get('name', f"Supplier {supplier_id}") if supplier_info else f"Supplier {supplier_id}"
                            
                            # Update or create performance cache
                            SupplierPerformanceCache.objects.update_or_create(
                                supplier_id=supplier_id,
                                date=today,
                                defaults={
                                    'supplier_name': supplier_name,
                                    'on_time_delivery_rate': metrics.get('on_time_rate', 90),
                                    'average_delay_days': metrics.get('average_delay', 0)
                                }
                            )
                            summary['logistics_processed'] += 1
                                
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {str(e)}")
                    summary['errors'].append(str(e))
                    
            # Close the consumer
            consumer.close()
            
        except Exception as e:
            logger.error(f"Error consuming from Kafka: {str(e)}")
            summary['errors'].append(f"Kafka consumer error: {str(e)}")
            
        return summary
    
    @staticmethod
    def notify_systems_of_rankings():
        """
        Notifies other systems about new supplier rankings
        via direct API calls (backup to Kafka)
        
        Returns:
            dict: Notification results
        """
        results = {
            'demand_forecasting': False,
            'blockchain_tracking': False,
            'logistics': False,
            'errors': []
        }
        
        try:
            # Get today's rankings for top suppliers
            today = timezone.now().date()
            top_rankings = SupplierRanking.objects.filter(
                date=today, 
                rank__lte=10
            )
            
            if not top_rankings:
                logger.warning("No rankings available to notify")
                return results
                
            # Prepare payload
            payload = {
                'ranking_date': today.isoformat(),
                'top_suppliers': [
                    {
                        'supplier_id': r.supplier_id,
                        'supplier_name': r.supplier_name,
                        'rank': r.rank,
                        'overall_score': float(r.overall_score)
                    }
                    for r in top_rankings
                ]
            }
            
            # Notify Group 29 - Demand Forecasting
            try:
                response = requests.post(
                    f"{IntegrationService.GROUP29_FORECAST_API}notify-rankings/",
                    json=payload,
                    timeout=5
                )
                results['demand_forecasting'] = response.status_code == 200
            except requests.RequestException as e:
                results['errors'].append(f"Group 29 notification error: {str(e)}")
                
            # Notify Group 30 - Blockchain
            try:
                response = requests.post(
                    f"{IntegrationService.GROUP30_BLOCKCHAIN_API}supplier-rankings/",
                    json=payload,
                    timeout=5
                )
                results['blockchain_tracking'] = response.status_code == 200
            except requests.RequestException as e:
                results['errors'].append(f"Group 30 notification error: {str(e)}")
                
            # Notify Group 32 - Logistics
            try:
                response = requests.post(
                    f"{IntegrationService.GROUP32_LOGISTICS_API}update-supplier-rankings/",
                    json=payload,
                    timeout=5
                )
                results['logistics'] = response.status_code == 200
            except requests.RequestException as e:
                results['errors'].append(f"Group 32 notification error: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error notifying systems of rankings: {str(e)}")
            results['errors'].append(str(e))
            
        return results