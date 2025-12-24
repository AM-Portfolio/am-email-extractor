import os
import json
import logging
from datetime import datetime
from kafka import KafkaProducer

class NotificationProducer:
    def __init__(self):
        self.bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.topic = os.environ.get('KAFKA_TOPIC', 'portfolio_updates')
        self.producer = None
        self._setup_producer()

    def _setup_producer(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                retries=3
            )
            logging.info(f"Connected to Kafka at {self.bootstrap_servers}")
        except Exception as e:
            logging.error(f"Failed to connect to Kafka: {e}")
            self.producer = None

    def send_update_event(self, user_id, status, db_id, broker, error=None):
        """
        Send a notification event to Kafka
        """
        if not self.producer:
            logging.warning("Kafka producer not available, attempting to reconnect...")
            self._setup_producer()
            
        if not self.producer:
            logging.error("Could not send event: Kafka unavailable")
            return False

        event = {
            "event": "PORTFOLIO_UPDATED",
            "user_id": user_id,
            "broker": broker,
            "status": status,
            "db_id": db_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error": error
        }

        try:
            future = self.producer.send(self.topic, event)
            # Block for result to ensure delivery (optional, can be async)
            record_metadata = future.get(timeout=10)
            logging.info(f"Event sent to {record_metadata.topic}:{record_metadata.partition}")
            return True
        except Exception as e:
            logging.error(f"Failed to send Kafka event: {e}")
            return False

# Global instance
producer_instance = NotificationProducer()

def get_producer():
    return producer_instance
