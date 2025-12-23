from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import uuid
from pathlib import Path
from typing import Optional
from backend.models.database import get_db
from backend.models.models import Tenant
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Create upload directory if it doesn't exist
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    tenant_id: Optional[int] = Query(None),
    file_type: str = Query("agreement", description="Type of file: 'agreement' or 'aadhar'"),
    db: Session = Depends(get_db)
):
    """Upload a PDF file"""
    # Log received parameters
    logger.info(f"Upload request - tenant_id: {tenant_id}, file_type: '{file_type}', filename: {file.filename}")

    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file_type parameter
    file_type = file_type.strip().lower()  # Normalize the file_type
    if file_type not in ["agreement", "aadhar"]:
        logger.error(f"Invalid file_type received: '{file_type}'")
        raise HTTPException(status_code=400, detail=f"file_type must be 'agreement' or 'aadhar', got '{file_type}'")

    # Read file content to check size
    file_content = file.file.read()
    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / 1024 / 1024}MB")

    # Generate meaningful filename based on tenant_id and file_type
    file_extension = Path(file.filename).suffix.lower()
    if tenant_id:
        # Use tenant_id and file_type for meaningful naming: tenant_1_agreement.pdf or tenant_1_aadhar.pdf
        unique_filename = f"tenant_{tenant_id}_{file_type}{file_extension}"
    else:
        # Fallback to UUID if no tenant_id provided
        unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    logger.info(f"Saving file to: {file_path}")

    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Update tenant record if tenant_id provided
    if tenant_id:
        tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if tenant:
            logger.info(f"Updating tenant {tenant_id} with file_type '{file_type}'")
            if file_type == "agreement":
                # Delete old agreement file if exists and different
                if tenant.agreement_pdf_path and tenant.agreement_pdf_path != file_path and os.path.exists(tenant.agreement_pdf_path):
                    try:
                        os.remove(tenant.agreement_pdf_path)
                    except:
                        pass
                tenant.agreement_pdf_path = file_path
                logger.info(f"Set agreement_pdf_path to: {file_path}")
            elif file_type == "aadhar":
                # Delete old aadhar file if exists and different
                if tenant.aadhar_pdf_path and tenant.aadhar_pdf_path != file_path and os.path.exists(tenant.aadhar_pdf_path):
                    try:
                        os.remove(tenant.aadhar_pdf_path)
                    except:
                        pass
                tenant.aadhar_pdf_path = file_path
                logger.info(f"Set aadhar_pdf_path to: {file_path}")
            db.commit()
            db.refresh(tenant)
            logger.info(f"Tenant updated - agreement_pdf_path: {tenant.agreement_pdf_path}, aadhar_pdf_path: {tenant.aadhar_pdf_path}")
        else:
            logger.warning(f"Tenant {tenant_id} not found")

    return {
        "filename": file.filename,
        "file_path": file_path,
        "file_size": file_size,
        "file_type": file_type,
        "message": "File uploaded successfully"
    }


# IMPORTANT: This route MUST come BEFORE the /{file_path:path} route
# Otherwise FastAPI will match /tenant/2 as a file path
@router.get("/tenant/{tenant_id}")
def get_tenant_file(
    tenant_id: int,
    file_type: str = Query("agreement", description="Type of file: 'agreement' or 'aadhar'"),
    db: Session = Depends(get_db)
):
    """Get PDF file for a specific tenant"""
    logger.info(f"Get file request - tenant_id: {tenant_id}, file_type: '{file_type}'")

    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    file_type = file_type.strip().lower()

    if file_type == "agreement":
        logger.info(f"Looking for agreement at: {tenant.agreement_pdf_path}")
        if not tenant.agreement_pdf_path:
            raise HTTPException(status_code=404, detail="Agreement PDF not found - no path stored")
        if not os.path.exists(tenant.agreement_pdf_path):
            raise HTTPException(status_code=404, detail=f"Agreement PDF file not found on disk: {tenant.agreement_pdf_path}")
        return FileResponse(tenant.agreement_pdf_path, media_type="application/pdf", filename=f"tenant_{tenant_id}_agreement.pdf")
    elif file_type == "aadhar":
        logger.info(f"Looking for aadhar at: {tenant.aadhar_pdf_path}")
        if not tenant.aadhar_pdf_path:
            raise HTTPException(status_code=404, detail="Aadhar PDF not found - no path stored")
        if not os.path.exists(tenant.aadhar_pdf_path):
            raise HTTPException(status_code=404, detail=f"Aadhar PDF file not found on disk: {tenant.aadhar_pdf_path}")
        return FileResponse(tenant.aadhar_pdf_path, media_type="application/pdf", filename=f"tenant_{tenant_id}_aadhar.pdf")
    else:
        raise HTTPException(status_code=400, detail="file_type must be 'agreement' or 'aadhar'")


# This catch-all route MUST come LAST
@router.get("/download/{file_path:path}")
def get_file(file_path: str):
    """Get a file by path"""
    # Security: Ensure file is within upload directory
    full_path = os.path.abspath(os.path.join(UPLOAD_DIR, file_path))
    upload_dir_abs = os.path.abspath(UPLOAD_DIR)

    if not full_path.startswith(upload_dir_abs):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(full_path, media_type="application/pdf")
