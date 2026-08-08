"""
VADP Document Service
==========================

Business logic for file uploading, local disk persistence (/backend/uploads/),
SHA-256 hash generation, and metadata tracking. Zero cloud dependencies.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path
from typing import Sequence

import aiofiles
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.repository import CaseRepository
from app.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.documents.models import Document
from app.documents.repository import DocumentRepository
from app.documents.schemas import DocumentListResponseSchema, DocumentResponseSchema

logger = get_logger(__name__)


class DocumentService:
    """Service managing local file uploads and integrity verification."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.case_repo = CaseRepository(db)
        self.settings = get_settings()

    async def upload_document(
        self, case_id: str, file: UploadFile, uploaded_by_id: str
    ) -> DocumentResponseSchema:
        """
        Upload file to local disk storage (/backend/uploads/), generate SHA-256 hash,
        and store record in SQLite.
        """
        # Validate case exists
        case = await self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError(message=f"Case with ID '{case_id}' not found.")

        # Validate file size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        max_bytes = self.settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise ValidationError(
                message=f"File size ({file_size / (1024*1024):.1f} MB) exceeds maximum allowed limit of {self.settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        # Ensure upload directory exists
        upload_dir = Path(self.settings.UPLOAD_DIR) / case_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique local filename
        file_ext = Path(file.filename or "file.bin").suffix
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        target_path = upload_dir / unique_filename

        # Stream file to disk while calculating SHA-256 hash
        sha256_hash = hashlib.sha256()
        async with aiofiles.open(target_path, "wb") as out_file:
            while chunk := await file.read(64 * 1024):  # 64KB chunks
                sha256_hash.update(chunk)
                await out_file.write(chunk)

        content_hash = sha256_hash.hexdigest()

        # Perform malware & virus scanning
        from app.security.virus_scanner import VirusScanner
        is_safe, threat_info = VirusScanner.scan_file(target_path)
        if not is_safe:
            if target_path.exists():
                target_path.unlink()
            logger.error("Malware file upload blocked and unlinked", extra={"case_id": case_id, "threat": threat_info})
            raise ValidationError(
                message=f"File upload rejected: Security threat detected ({threat_info})."
            )
        # Perform file encryption at rest
        from app.security.file_encryption import FileEncryption
        encrypted_path = FileEncryption.encrypt_file(target_path)

        doc = Document(
            case_id=case_id,
            uploaded_by=uploaded_by_id,
            file_name=file.filename or "uploaded_document",
            file_type=file.content_type or "application/octet-stream",
            file_size=file_size,
            storage_path=str(encrypted_path),
            content_hash=content_hash,
            is_verified=True,
        )

        created_doc = await self.doc_repo.create_document(doc)

        # Log timeline event on case
        await self.case_repo.add_case_event(
            case_id=case_id,
            event_type="document_uploaded",
            description=f"Document '{file.filename}' uploaded (SHA-256: {content_hash[:8]}...)",
            performed_by=uploaded_by_id,
            data={"document_id": created_doc.id, "hash": content_hash},
        )

        logger.info(
            "Document uploaded to encrypted storage",
            extra={"doc_id": created_doc.id, "path": str(encrypted_path), "sha256": content_hash},
        )
        return DocumentResponseSchema.model_validate(created_doc)

    async def list_case_documents(self, case_id: str) -> DocumentListResponseSchema:
        """
        List all uploaded documents for a case.
        """
        docs = await self.doc_repo.list_by_case(case_id)
        items = [DocumentResponseSchema.model_validate(d) for d in docs]
        return DocumentListResponseSchema(items=items, total=len(items))

    async def get_document_for_download(self, doc_id: str) -> tuple[str, str, str]:
        """
        Get local file path (decrypting on-the-fly if encrypted), original filename, and MIME type for downloading.
        """
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc or not os.path.exists(doc.storage_path):
            raise NotFoundError(message="Document file not found on storage.")

        from app.security.file_encryption import FileEncryption

        # If file is encrypted (.enc suffix or encrypted format), decrypt to temporary file for download response
        if doc.storage_path.endswith(".enc"):
            temp_path = FileEncryption.decrypt_to_temp_file(doc.storage_path, doc.file_name)
            return str(temp_path), doc.file_name, doc.file_type or "application/octet-stream"

        return doc.storage_path, doc.file_name, doc.file_type or "application/octet-stream"
