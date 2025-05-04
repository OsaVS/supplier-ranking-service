"""
Kafka utilities for the Supplier Ranking Service

This module provides wrapper classes for Kafka producers and consumers
to facilitate message-based integration with other services in the
Intelligent and Smart Supply Chain Management System.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from confluent_kafka import Producer as ConfluentProducer
from confluent_kafka import Consumer as ConfluentConsumer
from confluent_kafka import KafkaException, KafkaError
from django.conf import settings

logger = logging.getLogger(__name__)


class KafkaProducer:
    """
    Wrapper class for Kafka producer to publish messages to topics
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Kafka producer with configuration

        Args:
            config: Optional configuration dictionary for Kafka producer
        """
        default_config = {
            'bootstrap.servers': getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            'client.id': getattr(settings, 'KAFKA_CLIENT_ID', 'supplier-ranking-service'),
            'acks': 'all',  # Wait for all replicas to acknowledge
            'retries': 3,
            'retry.backoff.ms': 500
        }
        
        # Merge provided config with defaults
        if config:
            default_config.update(config)
            
        try:
            self.producer = ConfluentProducer(default_config)
            logger.info("Kafka producer initialized")
        except KafkaException as e:
            logger.error(f"Failed to initialize Kafka producer: {str(e)}")
            self.producer = None
            
    def produce(self, topic: str, value: Union[str, Dict], key: Optional[str] = None, 
                headers: Optional[Dict[str, str]] = None, callback: Optional[Callable] = None):
        """
        Publish a message to a Kafka topic

        Args:
            topic: The Kafka topic to publish to
            value: The message value (string or dict to be JSON serialized)
            key: Optional message key
            headers: Optional message headers
            callback: Optional delivery callback function

        Returns:
            bool: True if message was sent to Kafka broker, False otherwise
        """
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
            
        try:
            # Convert dict to JSON string if necessary
            if isinstance(value, dict):
                value = json.dumps(value)
                
            # Default callback function for delivery reports
            def delivery_report(err, msg):
                if err is not None:
                    logger.error(f"Message delivery failed: {err}")
                    if callback:
                        callback(False, err)
                else:
                    logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")
                    if callback:
                        callback(True, None)
            
            # Prepare headers in the format expected by confluent-kafka
            kafka_headers = None
            if headers:
                kafka_headers = [(k, v.encode('utf-8') if isinstance(v, str) else v) 
                                for k, v in headers.items()]
            
            # Produce message to topic
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8') if key else None,
                value=value.encode('utf-8'),
                headers=kafka_headers,
                callback=delivery_report
            )
            
            # Poll producer queue to trigger callbacks
            self.producer.poll(0)
            return True
            
        except KafkaException as e:
            logger.error(f"Error producing message to Kafka: {str(e)}")
            if callback:
                callback(False, str(e))
            return False
            
    def flush(self, timeout: float = 10.0):
        """
        Wait for all messages to be delivered

        Args:
            timeout: Maximum time to block in seconds
            
        Returns:
            Number of messages still in queue
        """
        if self.producer:
            return self.producer.flush(timeout)
        return 0


class KafkaMessage:
    """
    Class representing a message received from Kafka
    """
    
    def __init__(self, kafka_msg):
        """
        Initialize with a Kafka message
        
        Args:
            kafka_msg: Original Kafka message object
        """
        self._kafka_msg = kafka_msg
        self._value = None
        self._parsed_value = None
        
    def topic(self) -> str:
        """Get the topic name"""
        return self._kafka_msg.topic()
        
    def partition(self) -> int:
        """Get the partition number"""
        return self._kafka_msg.partition()
        
    def offset(self) -> int:
        """Get the offset"""
        return self._kafka_msg.offset()
        
    def key(self) -> Optional[str]:
        """Get the message key as string if present"""
        if self._kafka_msg.key() is not None:
            return self._kafka_msg.key().decode('utf-8')
        return None
        
    def value(self) -> str:
        """Get the message value as string"""
        if self._value is None:
            self._value = self._kafka_msg.value().decode('utf-8')
        return self._value
        
    def json(self) -> Optional[Dict]:
        """Get the message value as parsed JSON"""
        if self._parsed_value is None:
            try:
                self._parsed_value = json.loads(self.value())
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse message value as JSON: {self.value()[:100]}...")
                return None
        return self._parsed_value
        
    def headers(self) -> Dict[str, str]:
        """Get the message headers as a dictionary"""
        if self._kafka_msg.headers() is None:
            return {}
            
        return {
            key: value.decode('utf-8') if isinstance(value, bytes) else value
            for key, value in self._kafka_msg.headers()
        }
        
    def timestamp(self) -> tuple:
        """Get the message timestamp information"""
        return self._kafka_msg.timestamp()


class KafkaConsumer:
    """
    Wrapper class for Kafka consumer to subscribe to topics
    """
    
    def __init__(self, topics: Union[str, List[str]], config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Kafka consumer with topics and configuration

        Args:
            topics: Topic or list of topics to subscribe to
            config: Optional configuration dictionary for Kafka consumer
        """
        # Convert single topic to list
        if isinstance(topics, str):
            topics = [topics]
            
        default_config = {
            'bootstrap.servers': getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            'group.id': getattr(settings, 'KAFKA_CONSUMER_GROUP', 'supplier-ranking-group'),
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 5000
        }
        
        # Merge provided config with defaults
        if config:
            default_config.update(config)
            
        try:
            self.consumer = ConfluentConsumer(default_config)
            self.consumer.subscribe(topics)
            logger.info(f"Kafka consumer subscribed to topics: {', '.join(topics)}")
        except KafkaException as e:
            logger.error(f"Failed to initialize Kafka consumer: {str(e)}")
            self.consumer = None
            
    def poll(self, timeout: float = 1.0) -> Optional[KafkaMessage]:
        """
        Poll for new messages
        
        Args:
            timeout: Maximum time to block waiting for a message
            
        Returns:
            KafkaMessage if a message was received, None otherwise
        """
        if not self.consumer:
            logger.error("Kafka consumer not initialized")
            return None
            
        try:
            msg = self.consumer.poll(timeout)
            
            if msg is None:
                return None
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition, not an error
                    logger.debug(f"Reached end of partition: {msg.topic()} [{msg.partition()}]")
                else:
                    logger.error(f"Error polling Kafka: {msg.error()}")
                return None
                
            return KafkaMessage(msg)
            
        except KafkaException as e:
            logger.error(f"Exception polling Kafka: {str(e)}")
            return None
            
    def consume(self, num_messages: int = 100, timeout: float = 1.0) -> List[KafkaMessage]:
        """
        Consume multiple messages at once
        
        Args:
            num_messages: Maximum number of messages to consume
            timeout: Maximum time to block waiting for messages
            
        Returns:
            List of KafkaMessage objects
        """
        if not self.consumer:
            logger.error("Kafka consumer not initialized")
            return []
            
        try:
            messages = self.consumer.consume(num_messages, timeout)
            result = []
            
            for msg in messages:
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error(f"Error consuming from Kafka: {msg.error()}")
                else:
                    result.append(KafkaMessage(msg))
                    
            return result
            
        except KafkaException as e:
            logger.error(f"Exception consuming from Kafka: {str(e)}")
            return []
            
    def commit(self, message: Optional[KafkaMessage] = None, asynchronous: bool = False):
        """
        Commit offsets to Kafka
        
        Args:
            message: Specific message to commit, or None to commit current offsets
            asynchronous: Whether to commit asynchronously
            
        Returns:
            None
        """
        if not self.consumer:
            logger.error("Kafka consumer not initialized")
            return
            
        try:
            if message:
                self.consumer.commit(message._kafka_msg, asynchronous=asynchronous)
            else:
                self.consumer.commit(asynchronous=asynchronous)
                
        except KafkaException as e:
            logger.error(f"Error committing offsets: {str(e)}")
            
    def close(self):
        """
        Close the consumer and commit final offsets
        """
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("Kafka consumer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer: {str(e)}")


class KafkaAdminUtils:
    """
    Utility class for Kafka administration tasks
    """
    
    @staticmethod
    def check_connection(bootstrap_servers: Optional[str] = None) -> bool:
        """
        Check if Kafka connection is working
        
        Args:
            bootstrap_servers: Kafka bootstrap servers, defaults to settings
            
        Returns:
            bool: True if connection is working, False otherwise
        """
        if not bootstrap_servers:
            bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
            
        config = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': 'supplier-ranking-connection-test'
        }
        
        try:
            # Create a producer to test connection
            producer = ConfluentProducer(config)
            producer.list_topics(timeout=5.0)
            logger.info("Kafka connection test successful")
            return True
        except KafkaException as e:
            logger.error(f"Kafka connection test failed: {str(e)}")
            return False


def setup_kafka_logging():
    """
    Configure logging for Kafka operations
    """
    kafka_logger = logging.getLogger('kafka')
    kafka_logger.setLevel(logging.WARNING)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    kafka_logger.addHandler(handler)