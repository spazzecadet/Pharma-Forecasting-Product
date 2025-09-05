from __future__ import annotations

import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import datetime
import numpy as np


class DataQualityValidator:
    """Data quality validation for pharma forecasting data."""
    
    def __init__(self):
        self.rules = {
            "fact_demand": {
                "required_columns": ["date", "brand_id", "geo_id", "channel_id", "trx", "nrx", "units", "net_sales"],
                "date_columns": ["date"],
                "numeric_columns": ["trx", "nrx", "units", "net_sales"],
                "non_negative_columns": ["trx", "nrx", "units", "net_sales"],
                "id_columns": ["brand_id", "geo_id", "channel_id"]
            },
            "dim_brand": {
                "required_columns": ["brand_id", "molecule", "form", "strength", "indication"],
                "unique_columns": ["brand_id"],
                "date_columns": ["launch_date", "loe_date"]
            },
            "dim_geo": {
                "required_columns": ["geo_id", "country"],
                "unique_columns": ["geo_id"]
            }
        }
    
    def validate_table(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Validate a data table against quality rules."""
        if table_name not in self.rules:
            return {"error": f"No validation rules for table {table_name}"}
        
        rules = self.rules[table_name]
        results = {
            "table_name": table_name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "issues": [],
            "warnings": [],
            "passed": True
        }
        
        # Check required columns
        missing_cols = set(rules.get("required_columns", [])) - set(df.columns)
        if missing_cols:
            results["issues"].append(f"Missing required columns: {list(missing_cols)}")
            results["passed"] = False
        
        # Check unique constraints
        for col in rules.get("unique_columns", []):
            if col in df.columns and df[col].duplicated().any():
                results["issues"].append(f"Duplicate values in unique column: {col}")
                results["passed"] = False
        
        # Check date columns
        for col in rules.get("date_columns", []):
            if col in df.columns:
                try:
                    pd.to_datetime(df[col])
                except:
                    results["issues"].append(f"Invalid date format in column: {col}")
                    results["passed"] = False
        
        # Check numeric columns
        for col in rules.get("numeric_columns", []):
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    results["issues"].append(f"Non-numeric values in numeric column: {col}")
                    results["passed"] = False
        
        # Check non-negative constraints
        for col in rules.get("non_negative_columns", []):
            if col in df.columns and (df[col] < 0).any():
                results["issues"].append(f"Negative values in non-negative column: {col}")
                results["passed"] = False
        
        # Check for missing values
        missing_pct = df.isnull().sum() / len(df) * 100
        for col, pct in missing_pct.items():
            if pct > 0:
                if pct > 50:
                    results["issues"].append(f"High missing value percentage in {col}: {pct:.1f}%")
                    results["passed"] = False
                else:
                    results["warnings"].append(f"Missing values in {col}: {pct:.1f}%")
        
        # Check for outliers (using IQR method)
        for col in rules.get("numeric_columns", []):
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                if len(outliers) > 0:
                    outlier_pct = len(outliers) / len(df) * 100
                    if outlier_pct > 5:
                        results["warnings"].append(f"High outlier percentage in {col}: {outlier_pct:.1f}%")
        
        return results
    
    def validate_forecast_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate forecast-specific data quality."""
        results = {
            "table_name": "forecast_data",
            "row_count": len(df),
            "issues": [],
            "warnings": [],
            "passed": True
        }
        
        # Check for required columns
        required_cols = ["step", "yhat"]
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            results["issues"].append(f"Missing required forecast columns: {list(missing_cols)}")
            results["passed"] = False
        
        # Check for valid forecast values
        if "yhat" in df.columns:
            if (df["yhat"] < 0).any():
                results["issues"].append("Negative forecast values found")
                results["passed"] = False
            
            if df["yhat"].isnull().any():
                results["issues"].append("Missing forecast values found")
                results["passed"] = False
        
        # Check step sequence
        if "step" in df.columns:
            if not df["step"].is_monotonic_increasing:
                results["warnings"].append("Forecast steps are not in ascending order")
        
        return results
    
    def validate_time_series_continuity(self, df: pd.DataFrame, date_col: str = "date") -> Dict[str, Any]:
        """Validate time series continuity and detect gaps."""
        results = {
            "table_name": "time_series_continuity",
            "issues": [],
            "warnings": [],
            "passed": True
        }
        
        if date_col not in df.columns:
            results["issues"].append(f"Date column {date_col} not found")
            results["passed"] = False
            return results
        
        # Convert to datetime and sort
        df_sorted = df.copy()
        df_sorted[date_col] = pd.to_datetime(df_sorted[date_col])
        df_sorted = df_sorted.sort_values(date_col)
        
        # Check for gaps
        date_diff = df_sorted[date_col].diff()
        expected_freq = date_diff.mode().iloc[0] if not date_diff.empty else None
        
        if expected_freq is not None:
            gaps = date_diff[date_diff > expected_freq * 1.5]
            if len(gaps) > 0:
                results["warnings"].append(f"Found {len(gaps)} potential gaps in time series")
        
        # Check for duplicates
        duplicates = df_sorted[date_col].duplicated()
        if duplicates.any():
            results["issues"].append(f"Found {duplicates.sum()} duplicate dates")
            results["passed"] = False
        
        return results


def validate_sample_data():
    """Validate all sample data files."""
    import os
    from pathlib import Path
    
    validator = DataQualityValidator()
    data_dir = Path(__file__).parent.parent / "sample"
    
    results = {}
    
    # Validate each CSV file
    for csv_file in data_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            table_name = csv_file.stem
            results[table_name] = validator.validate_table(df, table_name)
        except Exception as e:
            results[csv_file.stem] = {"error": str(e), "passed": False}
    
    return results


if __name__ == "__main__":
    # Run validation on sample data
    results = validate_sample_data()
    for table, result in results.items():
        print(f"\n{table}:")
        if result.get("passed", False):
            print("  ✓ PASSED")
        else:
            print("  ✗ FAILED")
            for issue in result.get("issues", []):
                print(f"    - {issue}")
        for warning in result.get("warnings", []):
            print(f"    ! {warning}")
