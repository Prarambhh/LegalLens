from typing import Any, Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.database import get_db
from app.api import deps
from app.models.user import User
from app.services.kb_service import KnowledgeBaseService

router = APIRouter()

@router.post("/kb/upload/act")
async def upload_act(
    file: UploadFile = File(...),
    name: str = Form(...),
    year: int = Form(...),
    type: str = Form(...), # Central or State
    short_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    # current_user: User = Depends(deps.get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Admin: Upload a new Act to the Knowledge Base.
    """
    kb_service = KnowledgeBaseService(db)
    
    metadata = {
        "name": name,
        "year": year,
        "type": type,
        "short_name": short_name,
        "description": description
    }
    
    try:
        result = await kb_service.add_act(file, metadata)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/kb/upload/caselaw")
async def upload_case_law(
    file: UploadFile = File(...),
    title: str = Form(...),
    court_name: str = Form(...),
    citation: Optional[str] = Form(None),
    # current_user: User = Depends(deps.get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Admin: Upload a Case Law judgment.
    """
    kb_service = KnowledgeBaseService(db)
    
    metadata = {
        "title": title,
        "court_name": court_name,
        "citation": citation,
        # Date handling might need parsing from string if Form sends string
        "judgment_date": None 
    }
    
    try:
        result = await kb_service.add_case_law(file, metadata)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/kb/upload/acts/batch")
async def upload_acts_batch(
    files: list[UploadFile] = File(..., description="Multiple PDF files to upload"),
    metadata_json: str = Form(..., description='JSON array: [{"filename":"BNS.pdf","name":"Bharatiya Nyaya Sanhita","year":2023,"type":"Central","short_name":"BNS"}]'),
    # current_user: User = Depends(deps.get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Admin: Batch upload multiple Acts to the Knowledge Base.
    
    Provide multiple PDF files and a JSON metadata array that maps each filename to its metadata.
    
    Example metadata_json:
    ```json
    [
        {"filename": "BNS.pdf", "name": "Bharatiya Nyaya Sanhita", "year": 2023, "type": "Central", "short_name": "BNS"},
        {"filename": "IPC.pdf", "name": "Indian Penal Code", "year": 1860, "type": "Central", "short_name": "IPC"}
    ]
    ```
    """
    import json
    
    # Parse metadata JSON
    try:
        metadata_list = json.loads(metadata_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON metadata: {e}")
    
    # Build filename -> metadata map
    metadata_map = {item["filename"]: item for item in metadata_list}
    
    kb_service = KnowledgeBaseService(db)
    results = []
    errors = []
    
    for file in files:
        filename = file.filename
        if filename not in metadata_map:
            errors.append({"filename": filename, "error": "No metadata provided for this file"})
            continue
        
        meta = metadata_map[filename]
        try:
            result = await kb_service.add_act(file, {
                "name": meta["name"],
                "year": meta["year"],
                "type": meta["type"],
                "short_name": meta.get("short_name"),
                "description": meta.get("description")
            })
            results.append({"filename": filename, "success": True, **result})
        except Exception as e:
            errors.append({"filename": filename, "error": str(e)})
    
    return {
        "uploaded": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }

