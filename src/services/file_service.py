import os
import re
import logging
from datetime import datetime
from typing import List, Tuple, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import settings
from src.models.platform_services import Attachment, AttachmentVersion
from src.repositories.platform_services import AttachmentRepository, AttachmentVersionRepository

logger = logging.getLogger(__name__)


class AttachmentService:
    """
    Service managing validated file uploads, downloads, and version controls.
    """

    def __init__(self, db: AsyncSession, upload_dir: str = "uploads") -> None:
        self.db = db
        self.attachment_repo = AttachmentRepository(db)
        self.version_repo = AttachmentVersionRepository(db)
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        """
        Removes path traversal and unsafe characters from filenames.
        """
        # Extract base name just in case path delimiters were sent
        base = os.path.basename(filename)
        # Keep alphanumeric, dashes, underscores, and dots only
        sanitized = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", base)
        return sanitized

    def validate_file(self, filename: str, content: bytes, mime_type: str) -> None:
        """
        Verifies file size, extensions, and signature headers (magic numbers).
        """
        # 1. Check file size
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB"
            )

        # 2. Check extension & MIME
        ext = os.path.splitext(filename)[1].lower()
        allowed_types = [t.strip().lower() for t in settings.ALLOWED_MIME_TYPES.split(",")]

        # Validate by mapping typical extensions to MIME
        allowed_extensions = {".pdf", ".xlsx", ".csv", ".jpg", ".jpeg", ".png"}
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' is not permitted"
            )

        # 3. Check file signature (magic numbers) to prevent renaming executable or malicious files
        if ext in {".jpg", ".jpeg"}:
            if not content.startswith(b"\xff\xd8"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JPEG file signature")
        elif ext == ".png":
            if not content.startswith(b"\x89PNG\r\n\x1a\n"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PNG file signature")
        elif ext == ".pdf":
            if not content.startswith(b"%PDF"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PDF file signature")
        # CSV/Excel verification - basic check to make sure they are not binary executables
        elif ext == ".csv":
            try:
                content[:1024].decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSV text signature")
        elif ext == ".xlsx":
            if not content.startswith(b"PK\x03\x04"): # Zip file header used by xlsx
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Excel XLSX zip signature")

    async def upload_file(
        self,
        entity_type: str,
        entity_id: str,
        category: str,
        filename: str,
        content: bytes,
        uploaded_by: Optional[int] = None
    ) -> Attachment:
        """
        Validates, uploads, and registers a file. Handles replacement/versioning automatically.
        """
        # Validate file
        self.validate_file(filename, content, "")

        # Sanitize filename
        sanitized = self.sanitize_filename(filename)

        # Build relative and absolute save paths
        entity_folder = os.path.join(category, entity_type, entity_id)
        folder_path = os.path.join(self.upload_dir, entity_folder)
        os.makedirs(folder_path, exist_ok=True)

        # Check if attachment already exists for this entity and category to trigger versioning
        existing_attachments = await self.attachment_repo.get_by_entity(entity_type, entity_id)
        target_attachment = None
        for att in existing_attachments:
            if att.category.lower() == category.lower() and att.file_name == sanitized:
                target_attachment = att
                break

        if target_attachment:
            # We are replacing/updating: move existing details to version history
            # Find next version number
            query = select(AttachmentVersion).where(AttachmentVersion.attachment_id == target_attachment.attachment_id)
            result = await self.db.execute(query)
            versions = list(result.scalars().all())
            next_version_num = len(versions) + 1

            version_record = AttachmentVersion(
                attachment_id=target_attachment.attachment_id,
                version_number=next_version_num,
                file_name=target_attachment.file_name,
                file_path=target_attachment.file_path,
                file_size=target_attachment.file_size,
                uploaded_by=target_attachment.uploaded_by,
                created_at=target_attachment.created_at
            )
            await self.version_repo.create(version_record)

            # Define new filepath with version suffix to avoid overwriting physical files
            name_part, ext_part = os.path.splitext(sanitized)
            version_filename = f"{name_part}_v{next_version_num}{ext_part}"
            file_path = os.path.join(folder_path, version_filename)
            
            # Write to disk
            with open(file_path, "wb") as f:
                f.write(content)

            # Update the existing attachment record
            target_attachment.file_path = file_path
            target_attachment.file_size = len(content)
            target_attachment.uploaded_by = uploaded_by
            target_attachment.created_at = datetime.utcnow()
            await self.attachment_repo.update(target_attachment)
            logger.info(f"Version {next_version_num} uploaded successfully for attachment ID {target_attachment.attachment_id}")
            return target_attachment

        else:
            # First version: Save directly
            file_path = os.path.join(folder_path, sanitized)
            with open(file_path, "wb") as f:
                f.write(content)

            attachment = Attachment(
                entity_type=entity_type,
                entity_id=entity_id,
                category=category,
                file_name=sanitized,
                file_path=file_path,
                file_type=os.path.splitext(sanitized)[1].lower(),
                file_size=len(content),
                uploaded_by=uploaded_by,
                created_at=datetime.utcnow()
            )
            await self.attachment_repo.create(attachment)
            logger.info(f"New attachment uploaded and registered under ID {attachment.attachment_id}")
            return attachment

    async def get_file_content(self, attachment_id: int) -> Tuple[str, str, bytes]:
        """
        Retrieves file path, name, and raw content for download or preview.
        """
        attachment = await self.attachment_repo.get_by_id(attachment_id)
        if not attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

        if not os.path.exists(attachment.file_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical file missing from storage")

        with open(attachment.file_path, "rb") as f:
            content = f.read()

        return attachment.file_name, attachment.file_type, content

    async def delete_attachment(self, attachment_id: int) -> None:
        """
        Removes physical file and deletes database records.
        """
        attachment = await self.attachment_repo.get_by_id(attachment_id)
        if not attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

        # Delete physical versions
        for v in attachment.versions:
            try:
                if os.path.exists(v.file_path):
                    os.remove(v.file_path)
            except Exception as e:
                logger.error(f"Failed to delete physical version file {v.file_path}: {e}")

        # Delete physical file
        try:
            if os.path.exists(attachment.file_path):
                os.remove(attachment.file_path)
        except Exception as e:
            logger.error(f"Failed to delete physical file {attachment.file_path}: {e}")

        # Delete from DB
        await self.attachment_repo.delete(attachment)
        logger.info(f"Attachment ID {attachment_id} and all versions deleted from DB and disk.")
