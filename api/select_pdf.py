from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from services.database import get_db_session, UserFile
from pathlib import Path
from services.auth_utils import get_current_user_id

router = APIRouter(tags=["PDF Selection"])

@router.post("/select_pdf")
async def select_pdf(
    file_id: int = Query(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(
        select(UserFile).where(
            UserFile.user_id == user_id,
            UserFile.id == file_id
        )
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(404, "File not found")

    stem = Path(file.file_path).stem  # e.g. "sample"
    chunk_filename = f"{stem}_text_chunks.pkl"

    return {"chunk_filename": chunk_filename}