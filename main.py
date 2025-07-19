from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.auth import router as auth_router
from api.chat import router as chat_router

from api.upload_pdf import router as upload_pdf_router
from api.list_files import router as list_files_router
from api.select_pdf import router as select_pdf_router
from api.pdfs import router as pdfs_router

from api import list_files
import os

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    print("🔴 Request body:", body.decode())
    print("🔴 Validation errors:", exc.errors())
    return PlainTextResponse(str(exc), status_code=422)

# CORS for frontend to call backend

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins during dev
    allow_credentials=True,
    allow_methods=["*"],  # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # allow Content-Type, Authorization, etc.
)

# Path to React build folder
frontend_path = os.path.join(os.getcwd(), "web2pdf-frontend", "build")

# Mount static files (CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "static")), name="static")

# API Routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(upload_pdf_router)
app.include_router(list_files_router)
app.include_router(select_pdf_router)
app.include_router(pdfs_router)

# Serve index.html on any frontend route (React handles the routing)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    index_file = os.path.join(frontend_path, "index.html")
    return FileResponse(index_file)

