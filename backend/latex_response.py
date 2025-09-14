#!/usr/bin/env python3
"""
LaTeX Resume Tailoring Pipeline with LLaMA API
Automatically tailors resumes to job descriptions using AI and LaTeX formatting.
Supports TXT, PDF, DOCX inputs. Outputs both .tex and .pdf.
Removes blank first page in PDF if present.
"""

import os
import sys
import subprocess
from pathlib import Path

from groq import Groq

# Extra imports for file handling
from PyPDF2 import PdfReader, PdfWriter
from docx import Document
from pdfminer.high_level import extract_text
import asposewordscloud
from asposewordscloud.rest import ApiException
from dotenv import load_dotenv


load_dotenv()





def call_llama(system_prompt: str, user_prompt: str) -> str:
    """Helper function to call LLaMA API via Groq SDK."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    client = Groq(api_key=api_key)
    
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=0.3,
            max_tokens=4000,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"LLaMA API call failed: {e}")


def load_file(file_path: str) -> str:
    """Load text content from txt, tex, pdf, or docx file."""
    ext = Path(file_path).suffix.lower()
    try:
        if ext in [".txt", ".tex"]:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        elif ext == ".pdf":
            return extract_text(file_path).strip()
        elif ext == ".docx":
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()]).strip()
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Required file not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading {file_path}: {e}")


def save_file(content: str, file_path: str) -> None:
    """Save content to file, creating directories if needed."""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        raise RuntimeError(f"Error writing {file_path}: {e}")
    
import asposewordscloud
from asposewordscloud.apis.words_api import WordsApi
from asposewordscloud.models.requests import ConvertDocumentRequest
from asposewordscloud.rest import ApiException

def get_aspose_client():
    client_id = os.getenv("ASPOSE_CLIENT_ID")
    client_secret = os.getenv("ASPOSE_CLIENT_SECRET")
    return WordsApi(client_id, client_secret)

def pdf_to_word_aspose(pdf_path: str, output_path: str) -> str:
    """
    Convert PDF to Word (DOCX) using Aspose Cloud API.
    Preserves styles such as headings, underlines, fonts, etc.
    """
    api = get_aspose_client()

    try:
        with open(pdf_path, "rb") as f:
            # Create request object
            request = ConvertDocumentRequest(
                document=f,
                format="docx"
            )
            result = api.convert_document(request)

        # Save result
        with open(output_path, "wb") as f:
            f.write(result)
        
        print(f"✅ PDF converted to DOCX at {output_path}")
        return output_path

    except ApiException as e:
        raise RuntimeError(f"Aspose API conversion failed: {e}")




def print_status(message: str, success: bool = True) -> None:
    """Print status message with checkmark or X."""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")


def compile_latex_to_pdf(tex_file: str, output_dir: str) -> str:
    """Compile LaTeX file to PDF using pdflatex."""
    try:
        # Run pdflatex in nonstopmode (auto-continue without user input)
        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",  # Ignore prompts
            "-output-directory=" + output_dir,
            tex_file,
        ]
        
        # Run the LaTeX command
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # If compilation fails, print detailed error
        if result.returncode != 0:
            print("LaTeX compilation failed. Here are the details:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        
        # Return the path to the generated PDF
        pdf_path = str(Path(output_dir) / (Path(tex_file).stem + ".pdf"))
        return pdf_path

    except subprocess.CalledProcessError as e:
        print(f"LaTeX compilation failed: {e.stderr}")
        raise RuntimeError("LaTeX compilation failed.")


def remove_blank_first_page(pdf_path: str, output_path: str) -> None:
    """Always remove the first page and save the remaining PDF."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    if len(reader.pages) == 0:
        raise RuntimeError("Generated PDF is empty.")

    # Always remove the first page, if there are multiple pages
    if len(reader.pages) > 1:
        print("Removing the first page...")
        for i in range(1, len(reader.pages)):  # Start from the second page
            writer.add_page(reader.pages[i])
    else:
        # If there is only one page, we do nothing
        print("No additional pages to keep. Only one page present.")
    
    # Write the result to the output PDF
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"First page removed, and final PDF saved to {output_path}")


def tailor_resume_content(resume_text: str, job_desc: str) -> str:
    """
    LLaMA call: Tailor entire resume (header + body) to job description.
    Returns LaTeX body without preamble.
    """
    system_prompt = """You are an expert resume writer and LaTeX specialist.
Your task is to rewrite an entire resume (header + body) to align with a job description.

CRITICAL REQUIREMENTS:
- Output ONLY LaTeX body content (e.g., \\begin{header}, \\section{}, etc.)
- Do NOT include any LaTeX preamble (\\documentclass, \\begin{document}, \\end{document}, etc.)
- Always generate a proper LaTeX header block using \\begin{header}...\\end{header}
- After header, include sections such as Summary, Education, Experience, Projects, Skills, and Awards and certifications and Languages
- Do NOT insert blank pages or extra spacing that could push content to a new page
- Make sure there is **exactly one space before each number** and no additional space after the digits.
- Keep the structure professional and tailored to the job description
- Make sure all the skills mentioned in job description are included
- Rewrite the work experience so that it aligns with skills required in the job description but donot change the title of the job.
- Donot leave out any experience that is already present.  
"""

    user_prompt = f"""Please rewrite this resume (header + body) to align with the job description below.

ORIGINAL RESUME:
{resume_text}

JOB DESCRIPTION:
{job_desc}

Output ONLY the tailored resume body in LaTeX (including a header)."""
    
    return call_llama(system_prompt, user_prompt)

def insert_into_template(template_content: str, latex_draft: str) -> str:
    """
    Second LLaMA call: Insert tailored content into LaTeX template.
    Returns complete LaTeX document ready for compilation.
    """
    system_prompt = """You are a LaTeX expert specializing in resume templates.
Your task is to insert resume content into a LaTeX template.

CRITICAL REQUIREMENTS:
- Preserve ALL template formatting, commands, and structure
- Insert the provided LaTeX content in the correct location
- Do NOT add blank pages or extra vertical spacing
- Do NOT include \\documentclass, \\begin{document}, or \\end{document} in the inserted content
- Ensure the final document compiles to a single-page resume (unless the content is naturally longer)
- Ensure there is exactly one space before each number, and no additional space after the digits.
- Maintain proper LaTeX syntax throughout
- Never add the line "The boilerplate content was inspired by Gayle McDowell."
- Awalys keep the headings and subheadings bold.
- Keep the date aligned on the right side.
"""

    user_prompt = f"""Please insert the following LaTeX resume content into the provided template.

LATEX TEMPLATE:
{template_content}

RESUME CONTENT TO INSERT:
{latex_draft}

Output the complete LaTeX document ready for compilation."""
    
    return call_llama(system_prompt, user_prompt)



def main():
    """Main pipeline execution."""
    print("🚀 Starting LaTeX Resume Tailoring Pipeline")
    print("-" * 50)
    
    try:
        # Step 1: Load resume (txt, pdf, or docx)
        resume_path = "data/resume1.pdf"  # <-- change extension as needed
        print(f"Loading resume from {resume_path}...")
        resume_text = load_file(resume_path)
        print_status("Resume loaded successfully")
        
        # Step 2: Load job description
        job_desc_path = "data/job_desc.txt"
        print(f"Loading job description from {job_desc_path}...")
        job_desc = load_file(job_desc_path)
        print_status("Job description loaded successfully")
        
        # Step 3: First LLaMA call - Tailor full resume (header + body)
        print("Tailoring resume with LLaMA API...")
        latex_draft = tailor_resume_content(resume_text, job_desc)
        
        # Save intermediate draft
        save_file(latex_draft, "results/draft_resume.tex")
        print_status("Tailored resume draft saved to results/draft_resume.tex")
        
        # Step 4: Load LaTeX template
        template_path = "data/template.tex"
        print(f"Loading LaTeX template from {template_path}...")
        template_content = load_file(template_path)
        print_status("LaTeX template loaded successfully")
        
        # Step 5: Second LLaMA call - Insert into template
        print("Inserting tailored content into template with LLaMA API...")
        final_resume = insert_into_template(template_content, latex_draft)
        
        # Save final .tex
        final_tex_path = "results/final_resume.tex"
        save_file(final_resume, final_tex_path)
        print_status(f"Final resume generated and saved to {final_tex_path}")
        
        # Step 6: Compile LaTeX to PDF
        print("Compiling LaTeX to PDF...")
        pdf_path = compile_latex_to_pdf(final_tex_path, "results")
        print_status(f"PDF compiled successfully: {pdf_path}")
        
        # Step 7: Remove blank first page if present
        final_pdf_path = "results/final_resume_fixed.pdf"
        remove_blank_first_page(pdf_path, final_pdf_path)
        print_status(f"Final PDF cleaned and saved to {final_pdf_path}")
        
        print("-" * 50)
        print("🎉 Pipeline completed successfully!")
        print(f"📄 Final resume (TeX): {final_tex_path}")
        print(f"📄 Final resume (PDF): {final_pdf_path}")
        
    except Exception as e:
        print_status(f"Pipeline failed: {e}", success=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
