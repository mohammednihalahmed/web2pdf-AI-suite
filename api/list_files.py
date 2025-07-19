import select
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from services.database import get_db_session, UserFile
from services.auth_utils import get_current_user_id

router = APIRouter()

@router.get("/list_my_files/")
async def list_user_files(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        result = await db.execute(
            select(UserFile).where(UserFile.user_id == user_id)
        )
        files = result.scalars().all()

        if not files:
            return JSONResponse(
                status_code=200,
                content={"files": []}
            )

        file_list = [
            {
                "filename": f.filename,
                "file_path": f.file_path,
                "uploaded_at": f.uploaded_at.isoformat()
            }
            for f in files
        ]

        return JSONResponse(
            status_code=200,
            content={"files": file_list}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {e}")


