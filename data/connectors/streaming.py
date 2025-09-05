from __future__ import annotations

import asyncio
import json
import websockets
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
import pandas as pd
from .base import BaseConnector


class StreamingConnector(BaseConnector):
    """Real-time streaming data connector."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.websocket = None
        self.subscribers: List[Callable] = []
        self.is_connected = False
    
    async def connect(self) -> bool:
        """Connect to streaming data source."""
        try:
            self.websocket = await websockets.connect(self.config.get("ws_url"))
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to streaming source: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from streaming source."""
        if self.websocket:
            await self.websocket.close()
        self.is_connected = False
    
    async def test_connection(self) -> bool:
        """Test streaming connection."""
        return self.is_connected and not self.websocket.closed
    
    def get_schema(self, table_name: str) -> Dict[str, str]:
        """Get schema for streaming data."""
        return {
            "timestamp": "datetime",
            "brand_id": "string",
            "value": "float",
            "source": "string"
        }
    
    async def extract_data(
        self,
        table_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """Extract streaming data (returns recent data)."""
        # For streaming, we typically get real-time data
        # This is a mock implementation
        data = []
        for i in range(10):
            data.append({
                "timestamp": datetime.utcnow(),
                "brand_id": filters.get("brand_id", "BRAND_A") if filters else "BRAND_A",
                "value": 100 + i * 5,
                "source": "streaming"
            })
        
        return pd.DataFrame(data)
    
    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to real-time data updates."""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Unsubscribe from data updates."""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    async def start_streaming(self):
        """Start streaming data and notify subscribers."""
        if not self.is_connected:
            await self.connect()
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                for callback in self.subscribers:
                    try:
                        callback(data)
                    except Exception as e:
                        print(f"Error in subscriber callback: {e}")
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            print(f"Error in streaming: {e}")


class KafkaConnector(BaseConnector):
    """Kafka streaming connector for high-throughput data."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.consumer = None
        self.producer = None
    
    def connect(self) -> bool:
        """Connect to Kafka cluster."""
        try:
            from kafka import KafkaConsumer, KafkaProducer
            
            self.consumer = KafkaConsumer(
                self.config.get("topic"),
                bootstrap_servers=self.config.get("bootstrap_servers"),
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.get("bootstrap_servers"),
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            
            return True
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Kafka."""
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.close()
    
    def test_connection(self) -> bool:
        """Test Kafka connection."""
        return self.consumer is not None and self.producer is not None
    
    def get_schema(self, table_name: str) -> Dict[str, str]:
        """Get schema for Kafka data."""
        return {
            "timestamp": "datetime",
            "brand_id": "string",
            "geo_id": "string",
            "value": "float",
            "event_type": "string"
        }
    
    def extract_data(
        self,
        table_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """Extract data from Kafka topic."""
        if not self.consumer:
            return pd.DataFrame()
        
        data = []
        for message in self.consumer:
            if start_date and message.timestamp < start_date.timestamp() * 1000:
                continue
            if end_date and message.timestamp > end_date.timestamp() * 1000:
                break
            
            data.append({
                "timestamp": datetime.fromtimestamp(message.timestamp / 1000),
                **message.value
            })
            
            if len(data) >= 1000:  # Limit batch size
                break
        
        return pd.DataFrame(data)
    
    def publish_data(self, topic: str, data: Dict[str, Any]):
        """Publish data to Kafka topic."""
        if self.producer:
            self.producer.send(topic, data)


class RealTimeDataManager:
    """Manages real-time data connections and streaming."""
    
    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}
        self.data_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
    
    def add_connector(self, name: str, connector: BaseConnector):
        """Add a data connector."""
        self.connectors[name] = connector
    
    def get_connector(self, name: str) -> Optional[BaseConnector]:
        """Get a connector by name."""
        return self.connectors.get(name)
    
    async def start_streaming(self, connector_name: str):
        """Start streaming from a connector."""
        connector = self.get_connector(connector_name)
        if connector and hasattr(connector, 'start_streaming'):
            await connector.start_streaming()
    
    def subscribe_to_data(self, connector_name: str, callback: Callable):
        """Subscribe to data updates from a connector."""
        if connector_name not in self.subscribers:
            self.subscribers[connector_name] = []
        self.subscribers[connector_name].append(callback)
        
        connector = self.get_connector(connector_name)
        if connector and hasattr(connector, 'subscribe'):
            connector.subscribe(callback)
    
    def cache_data(self, source: str, data: Dict[str, Any]):
        """Cache real-time data."""
        if source not in self.data_cache:
            self.data_cache[source] = []
        
        self.data_cache[source].append(data)
        
        # Keep only last 1000 records
        if len(self.data_cache[source]) > 1000:
            self.data_cache[source] = self.data_cache[source][-1000:]
    
    def get_cached_data(self, source: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get cached data from a source."""
        return self.data_cache.get(source, [])[-limit:]
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of all data sources."""
        summary = {}
        for source, data in self.data_cache.items():
            summary[source] = {
                "record_count": len(data),
                "latest_timestamp": data[-1]["timestamp"] if data else None,
                "data_rate": len(data) / 60 if data else 0  # records per minute
            }
        return summary


# Global real-time data manager
rt_manager = RealTimeDataManager()
