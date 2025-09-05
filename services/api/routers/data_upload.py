from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import pandas as pd
import io
import sys
from pathlib import Path
from datetime import datetime

from auth.dependencies import get_current_user, require_permission
from auth.models import User

router = APIRouter(prefix="/data", tags=["data_upload"])

# Add repo root to path for ML imports
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

from data.validation.data_quality import validate_demand_data, validate_brand_data, validate_geo_data  # type: ignore


class DataUploadResponse:
    def __init__(self, success: bool, message: str, records_processed: int = 0, errors: List[str] = None):
        self.success = success
        self.message = message
        self.records_processed = records_processed
        self.errors = errors or []


@router.post("/upload/demand")
async def upload_demand_data(
    file: UploadFile = File(...),
    brand_id: str = Form(...),
    current_user: User = Depends(require_permission("data", "write"))
):
    """Upload demand data from CSV/Excel file."""
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="File must be CSV or Excel format")
        
        # Read file content
        content = await file.read()
        
        # Parse based on file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        else:  # Excel
            df = pd.read_excel(io.BytesIO(content))
        
        # Validate data structure
        validation_result = validate_demand_data(df)
        if not validation_result.is_valid:
            return DataUploadResponse(
                success=False,
                message="Data validation failed",
                errors=validation_result.errors
            )
        
        # Process and store data (in production, this would save to database)
        records_processed = len(df)
        
        # Log the upload
        print(f"User {current_user.username} uploaded {records_processed} demand records for brand {brand_id}")
        
        return DataUploadResponse(
            success=True,
            message=f"Successfully uploaded {records_processed} demand records",
            records_processed=records_processed
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload/brands")
async def upload_brand_data(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("data", "write"))
):
    """Upload brand dimension data from CSV/Excel file."""
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="File must be CSV or Excel format")
        
        # Read file content
        content = await file.read()
        
        # Parse based on file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        else:  # Excel
            df = pd.read_excel(io.BytesIO(content))
        
        # Validate data structure
        validation_result = validate_brand_data(df)
        if not validation_result.is_valid:
            return DataUploadResponse(
                success=False,
                message="Data validation failed",
                errors=validation_result.errors
            )
        
        # Process and store data
        records_processed = len(df)
        
        return DataUploadResponse(
            success=True,
            message=f"Successfully uploaded {records_processed} brand records",
            records_processed=records_processed
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload/geographies")
async def upload_geo_data(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("data", "write"))
):
    """Upload geography dimension data from CSV/Excel file."""
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="File must be CSV or Excel format")
        
        # Read file content
        content = await file.read()
        
        # Parse based on file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        else:  # Excel
            df = pd.read_excel(io.BytesIO(content))
        
        # Validate data structure
        validation_result = validate_geo_data(df)
        if not validation_result.is_valid:
            return DataUploadResponse(
                success=False,
                message="Data validation failed",
                errors=validation_result.errors
            )
        
        # Process and store data
        records_processed = len(df)
        
        return DataUploadResponse(
            success=True,
            message=f"Successfully uploaded {records_processed} geography records",
            records_processed=records_processed
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload/pricing")
async def upload_pricing_data(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("data", "write"))
):
    """Upload pricing and promotional data from CSV/Excel file."""
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="File must be CSV or Excel format")
        
        # Read file content
        content = await file.read()
        
        # Parse based on file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        else:  # Excel
            df = pd.read_excel(io.BytesIO(content))
        
        # Basic validation
        required_columns = ['brand_id', 'geo_id', 'date', 'price', 'promotion_type']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return DataUploadResponse(
                success=False,
                message="Missing required columns",
                errors=[f"Missing columns: {', '.join(missing_columns)}"]
            )
        
        # Process and store data
        records_processed = len(df)
        
        return DataUploadResponse(
            success=True,
            message=f"Successfully uploaded {records_processed} pricing records",
            records_processed=records_processed
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/upload/templates")
def get_upload_templates(current_user: User = Depends(require_permission("data", "read"))):
    """Get CSV templates for data upload."""
    templates = {
        "demand_data": {
            "filename": "demand_data_template.csv",
            "description": "Demand data template",
            "required_columns": ["brand_id", "geo_id", "date", "demand", "units"],
            "sample_data": [
                ["BRAND_A", "US", "2023-01-01", 1000, 5000],
                ["BRAND_A", "US", "2023-01-08", 1200, 6000],
                ["BRAND_A", "US", "2023-01-15", 1100, 5500]
            ]
        },
        "brand_data": {
            "filename": "brand_data_template.csv",
            "description": "Brand dimension template",
            "required_columns": ["brand_id", "brand_name", "molecule", "therapeutic_area", "launch_date"],
            "sample_data": [
                ["BRAND_A", "Brand A", "Molecule A", "Oncology", "2020-01-01"],
                ["BRAND_B", "Brand B", "Molecule B", "Cardiology", "2019-06-15"]
            ]
        },
        "geo_data": {
            "filename": "geo_data_template.csv",
            "description": "Geography dimension template",
            "required_columns": ["geo_id", "geo_name", "region", "country", "market_size"],
            "sample_data": [
                ["US", "United States", "North America", "USA", 1000000],
                ["CA", "Canada", "North America", "Canada", 500000]
            ]
        },
        "pricing_data": {
            "filename": "pricing_data_template.csv",
            "description": "Pricing and promotional data template",
            "required_columns": ["brand_id", "geo_id", "date", "price", "promotion_type", "discount_pct"],
            "sample_data": [
                ["BRAND_A", "US", "2023-01-01", 100.00, "none", 0],
                ["BRAND_A", "US", "2023-01-15", 90.00, "promotion", 10]
            ]
        }
    }
    
    return {"templates": templates}


@router.post("/upload/validate")
async def validate_upload_file(
    file: UploadFile = File(...),
    data_type: str = Form(...),
    current_user: User = Depends(require_permission("data", "read"))
):
    """Validate uploaded file before processing."""
    try:
        # Read file content
        content = await file.read()
        
        # Parse based on file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        else:  # Excel
            df = pd.read_excel(io.BytesIO(content))
        
        # Validate based on data type
        if data_type == "demand":
            validation_result = validate_demand_data(df)
        elif data_type == "brand":
            validation_result = validate_brand_data(df)
        elif data_type == "geo":
            validation_result = validate_geo_data(df)
        else:
            raise HTTPException(status_code=400, detail="Invalid data type")
        
        return {
            "valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "record_count": len(df),
            "columns": list(df.columns)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/upload/history")
def get_upload_history(
    limit: int = 50,
    current_user: User = Depends(require_permission("data", "read"))
):
    """Get upload history for the current user."""
    # In production, this would query the database
    # For now, return mock data
    history = [
        {
            "id": "upload_001",
            "filename": "demand_data_2023.csv",
            "data_type": "demand",
            "records_processed": 1000,
            "uploaded_at": "2024-01-15T10:30:00Z",
            "status": "success"
        },
        {
            "id": "upload_002",
            "filename": "brand_data_2023.xlsx",
            "data_type": "brand",
            "records_processed": 50,
            "uploaded_at": "2024-01-14T15:45:00Z",
            "status": "success"
        }
    ]
    
    return {"uploads": history[:limit]}
