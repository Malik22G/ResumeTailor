#!/usr/bin/env python3
"""
FastAPI server that uses latex_response.py functions to tailor resumes.
Compatible with the existing latex_response.py pipeline.
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import time
from pathlib import Path
from fastapi.staticfiles import StaticFiles



# Import functions from latex_response.py
from latex_response import (
    load_file,
    save_file,
    print_status,
    compile_latex_to_pdf,
    remove_blank_first_page,
    tailor_resume_content,
    insert_into_template,
)

# Create FastAPI instance
app = FastAPI()

app.mount("/static", StaticFiles(directory="results"), name="static")


# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
os.makedirs("results", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# Define ALLOWED_MIME_TYPES
ALLOWED_MIME_TYPES = [
    "text/plain",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]

def extract_text_from_upload(file_content: bytes, mime_type: str, filename: str) -> str:
    """Extract text content from uploaded file based on MIME type."""
    # Reusing logic from latex_response.py for extracting text from various formats
    ext = filename.split('.')[-1].lower()

    if mime_type == "text/plain" or ext == "txt":
        return file_content.decode('utf-8')

    elif mime_type == "application/pdf" or ext == "pdf":
        from pdfminer.high_level import extract_text
        with open(f"uploads/{filename}", "wb") as f:
            f.write(file_content)
        return extract_text(f"uploads/{filename}")

    elif mime_type == "application/msword" or ext == "doc" or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or ext == "docx":
        from docx import Document
        with open(f"uploads/{filename}", "wb") as f:
            f.write(file_content)
        doc = Document(f"uploads/{filename}")
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()]).strip()

    else:
        raise ValueError(f"Unsupported MIME type: {mime_type}")


@app.post("/tailor_resume/")
async def tailor_resume(
    resume: UploadFile = File(...),
    job_desc: str = Form(...),
):
    """
    Endpoint to tailor a resume using the provided job description.
    Uses the exact same pipeline as latex_response.py.
    Returns URLs to download the tailored LaTeX (.tex) file and compiled PDF.
    """
    try:
        # Step 1: Validate file MIME type
        mime_type = resume.content_type
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {mime_type}. Please upload a .txt, .pdf, or .docx file."
            )
        
        # Step 2: Read uploaded file content
        file_content = await resume.read()
        
        # Step 3: Extract text content based on file type
        print_status("Extracting text from uploaded file...")
        resume_content = extract_text_from_upload(file_content, mime_type, resume.filename)
        print_status("Text extracted successfully")

        # Step 4: First LLaMA call - Tailor full resume (header + body)
        print_status("Tailoring resume with LLaMA API...")
        latex_draft = tailor_resume_content(resume_content, job_desc)
        
        # Save intermediate draft with timestamp
        timestamp = str(int(time.time()))
        draft_filename = f"draft_resume_{timestamp}.tex"
        draft_path = f"results/{draft_filename}"
        save_file(latex_draft, draft_path)
        print_status(f"Tailored resume draft saved to {draft_path}")

        # Step 5: Load LaTeX template
        template_path = "data/template.tex"
        
        # Check if template exists
        if not os.path.exists(template_path):
            raise HTTPException(status_code=500, detail="LaTeX template not found")
        
        print(f"Loading LaTeX template from {template_path}...")
        template_content = load_file(template_path)
        print_status("LaTeX template loaded successfully")

        # Step 6: Second LLaMA call - Insert into template
        print_status("Inserting tailored content into template with LLaMA API...")
        final_resume = insert_into_template(template_content, latex_draft)

        # Step 7: Save the final LaTeX file with unique filename
        final_tex_filename = f"final_resume_{timestamp}.tex"
        final_tex_path = f"results/{final_tex_filename}"
        save_file(final_resume, final_tex_path)
        print_status(f"Final resume generated and saved to {final_tex_path}")

        # Step 8: Compile LaTeX to PDF
        print_status("Compiling LaTeX to PDF...")
        pdf_path = compile_latex_to_pdf(final_tex_path, "results")
        print_status(f"PDF compiled successfully: {pdf_path}")

        # Step 9: Remove blank first page if present
        final_pdf_filename = f"final_resume_fixed_{timestamp}.pdf"
        final_pdf_path = f"results/{final_pdf_filename}"
        remove_blank_first_page(pdf_path, final_pdf_path)
        print_status(f"Final PDF cleaned and saved to {final_pdf_path}")

        # Return URLs to the generated files
        base_url = "http://127.0.0.1:8000"  # Change this to your actual domain in production
        
        return {
            "success": True,
            "tex_url": f"{base_url}/static/{final_tex_filename}",
            "pdf_url": f"{base_url}/static/{final_pdf_filename}",
            "draft_tex_url": f"{base_url}/static/{draft_filename}",
            "tex_filename": final_tex_filename,
            "pdf_filename": final_pdf_filename,
            "draft_tex_filename": draft_filename,
            "message": "Resume tailored successfully!"
        }

    except HTTPException:
        raise
    except Exception as e:
        print_status(f"Error in tailor_resume: {str(e)}", success=False)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/download/tex/{filename}")
async def download_tex(filename: str):
    """Download a specific TEX file"""
    file_path = f"results/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        file_path, 
        media_type="application/x-tex",
        filename=filename
    )


@app.get("/download/pdf/{filename}")
async def download_pdf(filename: str):
    """Download a specific PDF file"""
    file_path = f"results/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        file_path,
        media_type="application/pdf", 
        filename=filename
    )


@app.get("/")
async def root():
    return {"message": "Resume Tailor API is running!"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Resume Tailor API is operational",
        "template_exists": os.path.exists("data/template.tex"),
        "results_dir_exists": os.path.exists("results"),
        "uploads_dir_exists": os.path.exists("uploads")
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting Resume Tailor API server...")
    print("Make sure you have:")
    print("- data/template.tex file")
    uvicorn.run(app, host="127.0.0.1", port=8000)
