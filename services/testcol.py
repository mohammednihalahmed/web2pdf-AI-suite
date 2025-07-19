from api.upload_pdf import router as upload_pdf_router
from api.generate_convo_pdf import router as generate_convo_pdf_router
from api.web2pdf import router as web2pdf_router
app.include_router(upload_pdf_router)
app.include_router(generate_convo_pdf_router)
app.include_router(web2pdf_router)