from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime


class BaseConnector(ABC):
    """Base class for all data connectors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to data source."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close connection to data source."""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if connection is working."""
        pass
    
    @abstractmethod
    def get_schema(self, table_name: str) -> Dict[str, str]:
        """Get schema for a table."""
        pass
    
    @abstractmethod
    def extract_data(
        self,
        table_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """Extract data from source."""
        pass
    
    def validate_data(self, df: pd.DataFrame, expected_columns: list) -> bool:
        """Validate extracted data has required columns."""
        return all(col in df.columns for col in expected_columns)
