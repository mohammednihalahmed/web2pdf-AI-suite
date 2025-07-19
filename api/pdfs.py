from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from services.database import get_db_session, UserFile
from services.auth_utils import get_current_user_id

router = APIRouter()

@router.get("/pdfs")
async def get_user_pdfs(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        result = await db.execute(
            select(UserFile)
            .where(UserFile.user_id == user_id)
            .order_by(UserFile.uploaded_at.desc())
        )
        files = result.scalars().all()
        
        return {"pdfs": [
            {"id": f.id, "filename": f.filename, "uploaded_at": f.uploaded_at}
            for f in files
        ]}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching PDFs: {str(e)}"
        )

