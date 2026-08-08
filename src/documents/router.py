"""
VADP Document Router
=========================

REST API endpoints for document upload and retrieval:
  - POST /api/v1/documents/upload/{case_id}
  - GET  /api/v1/documents/case/{case_id}
  - GET  /api/v1/documents/{id}/download
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.db.session import get_db_session
from app.documents.schemas import DocumentListResponseSchema, DocumentResponseSchema
from app.documents.service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload/{case_id}",
    response_model=DocumentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document to case",
    description="Upload a document (PDF, DOCX, TXT, image) to local storage. Computes SHA-256 hash.",
)
async def upload_document(
    case_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentResponseSchema:
    service = DocumentService(db)
    return await service.upload_document(case_id, file, current_user.id)


@router.get(
    "/case/{case_id}",
    response_model=DocumentListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="List case documents",
    description="Retrieve list of all uploaded document metadata for a case.",
)
async def list_documents(
    case_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> DocumentListResponseSchema:
    service = DocumentService(db)
    return await service.list_case_documents(case_id)


@router.get(
    "/{doc_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download document file",
    description="Stream document file from local storage.",
)
async def download_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> FileResponse:
    service = DocumentService(db)
    file_path, filename, media_type = await service.get_document_for_download(doc_id)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
    )
