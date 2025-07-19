# api/upload_pdf.py

import os
import shutil
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from services.process_pdf import PDFProcessor
from services.chatbot_service import stop_model, start_model
from services.auth_utils import get_current_user_id
from services.database import UserFile, get_db_session
from configs.paths import UPLOADS_DIR

router = APIRouter()

@router.post("/upload_pdf/")
async def upload_pdf(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Save, process, and index the uploaded PDF. This is a blocking endpoint.
    """
    os.makedirs(UPLOADS_DIR, exist_ok=True)

    # 1️⃣ Generate a unique filename to avoid collisions
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    dest_path = os.path.join(UPLOADS_DIR, unique_name)

    # 2️⃣ Save file
    try:
        with open(dest_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    # 3️⃣ Stop the model, process the file, then restart the model
    try:
        stop_model()

        processor = PDFProcessor()
        await processor.process_and_store(dest_path)

        start_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

    # 4️⃣ Save metadata to DB
    user_file = UserFile(
        user_id=user_id,
        filename=unique_name,
        file_path=dest_path
    )
    db.add(user_file)
    await db.commit()

    # 5️⃣ Respond with success
    return JSONResponse({"message": "✅ PDF uploaded and processed successfully."})
