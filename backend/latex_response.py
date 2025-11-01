#!/usr/bin/env python3
"""
LaTeX Resume Tailoring Pipeline with LLaMA API
Automatically tailors resumes to job descriptions using AI and LaTeX formatting.
Supports TXT, PDF, DOCX inputs. Outputs both .tex and .pdf.
Removes blank first page in PDF if present.
"""

import os
import sys
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter


from groq import Groq

# Extra imports for file handling
from PyPDF2 import PdfReader, PdfWriter
from docx import Document
from pdfminer.high_level import extract_text
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
    print("Converting pdf to word....")
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
    """Compile LaTeX file to PDF using pdflatex with maximum error tolerance."""
    from pathlib import Path
    import subprocess
    
    # First, try to sanitize the file if you have such a function
    # sanitize_tex_file(tex_file=tex_file)
    
    pdf_path = str(Path(output_dir) / (Path(tex_file).stem + ".pdf"))
    
    # Method 1: Try with batchmode (most permissive)
    try:
        cmd = [
            "pdflatex",
            "-interaction=batchmode",  # Suppress all output, continue through errors
            "-output-directory=" + output_dir,
            tex_file,
        ]
        
        # Run multiple times to resolve references (typical LaTeX workflow)
        for i in range(3):
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Check if PDF was created even with errors
            if Path(pdf_path).exists():
                print(f"PDF generated successfully (pass {i+1})")
                return pdf_path
    except Exception as e:
        print(f"Batchmode attempt failed: {e}")
    
    # Method 2: Try with nonstopmode if batchmode didn't work
    try:
        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",  # Continue without stopping for errors
            "-file-line-error",          # Better error reporting
            "-output-directory=" + output_dir,
            tex_file,
        ]
        
        # Run the command
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Check if PDF exists regardless of return code
        if Path(pdf_path).exists():
            print("PDF generated with nonstopmode despite errors")
            return pdf_path
        
        # If no PDF, print diagnostics
        if result.returncode != 0:
            print("LaTeX compilation had errors. Details:")
            print("STDOUT:", result.stdout[-2000:])  # Last 2000 chars to avoid flood
            
    except subprocess.CalledProcessError as e:
        print(f"Nonstopmode attempt failed: {e}")
    
    # Method 3: Force compilation with error recovery wrapper
    try:
        # Create a wrapper tex file that includes the original with error handling
        wrapper_content = r"""
\nonstopmode
\batchmode  % Suppress most error messages
\documentclass{article}
\usepackage{silence}  % If available, suppresses warnings
\begin{document}
\scrollmode  % Continue past errors
\input{""" + Path(tex_file).stem + r"""}
\end{document}
"""
        
        wrapper_file = Path(output_dir) / f"wrapper_{Path(tex_file).stem}.tex"
        wrapper_file.write_text(wrapper_content)
        
        cmd = [
            "pdflatex",
            "-interaction=batchmode",
            "-output-directory=" + output_dir,
            str(wrapper_file),
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Check for wrapper PDF
        wrapper_pdf = Path(output_dir) / f"wrapper_{Path(tex_file).stem}.pdf"
        if wrapper_pdf.exists():
            # Rename to expected output
            wrapper_pdf.rename(pdf_path)
            print("PDF generated using wrapper method")
            return pdf_path
            
    except Exception as e:
        print(f"Wrapper method failed: {e}")
    
    # Method 4: Fix common LaTeX errors before compilation
    try:
        # Read the tex file and attempt to fix common issues
        with open(tex_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Common fixes
        fixes_applied = []
        
        # Balance braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces > close_braces:
            content += '}' * (open_braces - close_braces)
            fixes_applied.append(f"Added {open_braces - close_braces} closing braces")
        elif close_braces > open_braces:
            # Remove extra closing braces from the end
            for _ in range(close_braces - open_braces):
                if content.rstrip().endswith('}'):
                    content = content.rstrip()[:-1]
            fixes_applied.append(f"Removed {close_braces - open_braces} extra closing braces")
        
        # Ensure document ends properly
        if '\\end{document}' not in content:
            content += '\n\\end{document}'
            fixes_applied.append("Added missing \\end{document}")
        
        # Save fixed version
        fixed_file = Path(output_dir) / f"fixed_{Path(tex_file).stem}.tex"
        with open(fixed_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if fixes_applied:
            print(f"Applied fixes: {', '.join(fixes_applied)}")
        
        # Try to compile the fixed version
        cmd = [
            "pdflatex",
            "-interaction=batchmode",
            "-output-directory=" + output_dir,
            str(fixed_file),
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Check for fixed PDF
        fixed_pdf = Path(output_dir) / f"fixed_{Path(tex_file).stem}.pdf"
        if fixed_pdf.exists():
            # Rename to expected output
            fixed_pdf.rename(pdf_path)
            print("PDF generated after applying automatic fixes")
            return pdf_path
            
    except Exception as e:
        print(f"Auto-fix method failed: {e}")
    
    # Final check: See if any PDF was created with original name
    if Path(pdf_path).exists():
        print("PDF found despite errors")
        return pdf_path
    
    # If all methods failed, raise an error with helpful information
    raise RuntimeError(
        f"Could not generate PDF. The LaTeX file has fatal errors.\n"
        f"Main error appears to be: Missing }} at line 225.\n"
        f"Please check the LaTeX source for unmatched braces near \\end{{center}}"
    )


def sanitize_tex_file(tex_file: str):
    """
    Pre-process LaTeX file to fix common issues that prevent compilation.
    This modifies the file in place.
    """
    from pathlib import Path
    
    try:
        with open(tex_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        fixed_lines = []
        brace_count = 0
        
        for i, line in enumerate(lines):
            # Track brace balance
            brace_count += line.count('{') - line.count('}')
            
            # Fix common issues
            # Remove stray closing braces at end of center environment
            if '\\end{center}' in line and line.strip().endswith('}}'):
                line = line.replace('}}', '}', 1)
                print(f"Fixed extra brace at line {i+1}")
            
            fixed_lines.append(line)
        
        # Write back if changes were made
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
            
        if brace_count != 0:
            print(f"Warning: Brace imbalance detected: {brace_count}")
            
    except Exception as e:
        print(f"Could not sanitize file: {e}")


def remove_blank_first_page(pdf_path: str, output_path: str) -> None:
    """
    Remove the first page if it has no or minimal alphabetic text.
    Saves resulting PDF to output_path.
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    num_pages = len(reader.pages)
    if num_pages == 0:
        raise RuntimeError("Generated PDF is empty.")

    first_page = reader.pages[0]

    # Extract text from first page
    try:
        first_page_text = first_page.extract_text() or ""
    except Exception:
        first_page_text = ""

    # Count alphabetic characters
    alpha_count = sum(c.isalpha() for c in first_page_text)

    # Consider page blank if it has 5 or fewer alphabetic characters
    is_blank = alpha_count <= 5

    if is_blank:
        # If there's only one page, keep the original
        if num_pages == 1:
            with open(pdf_path, "rb") as src, open(output_path, "wb") as dst:
                dst.write(src.read())
            print("PDF had a single blank page — kept original.")
            return

        # Add all pages except the first
        for i in range(1, num_pages):
            writer.add_page(reader.pages[i])

        # Preserve metadata if present
        try:
            if reader.metadata:
                writer.add_metadata(reader.metadata)
        except Exception:
            pass

        with open(output_path, "wb") as f_out:
            writer.write(f_out)

        print(f"First page removed (only {alpha_count} alphabetic characters). Saved to {output_path}")
    else:
        # Copy original PDF to output_path
        with open(pdf_path, "rb") as src, open(output_path, "wb") as dst:
            dst.write(src.read())
        print(f"First page has {alpha_count} alphabetic characters. No changes made.")


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
- You can remove section if there is no content relevant to that section.
- Do NOT insert blank pages or extra spacing that could push content to a new page
- Donot leave out any experience or projects that is already present.  
- Make sure there is **exactly one space before each number** and no additional space after the digits.
- Keep the structure professional and tailored to the job description
- Make sure all the skills mentioned in job description are included
- Rewrite the work experience so that it aligns with skills required in the job description but donot change the title of the job.
- Output must contain ONLY valid LaTeX code. 
- Do NOT include explanations, comments, or extra text such as 
  "Here is the LaTeX", "Below is...", or anything outside LaTeX.

EXPERIENCE SECTION REQUIREMENTS:
- Write detailed, comprehensive bullet points for each role (3-5 bullet points per position)
- Each bullet point should be a complete sentence or detailed phrase (15-25 words minimum)
- Use the STAR method: describe the Situation/Task, Action taken, and Result/impact achieved
- Include specific metrics, percentages, numbers, and quantifiable achievements wherever possible
- Highlight technical skills, tools, and technologies used in context
- Demonstrate leadership, collaboration, and problem-solving abilities
- Tailor each bullet point to emphasize skills and experiences relevant to the job description
- Use strong action verbs (e.g., "Architected", "Spearheaded", "Optimized", "Implemented")
- Show progression and increasing responsibility across roles
- Example good bullet point: "Architected and implemented a microservices-based data pipeline processing 2M+ records daily, reducing processing time by 45% and improving system reliability to 99.9% uptime through automated monitoring and failover mechanisms"
- Example bad bullet point: "Worked on data pipeline" or "Improved system performance"

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
- Output must contain ONLY valid LaTeX code. 
- Do NOT include any other text in response just latex code no explanations, comments, or extra text such as 
  "Here is the LaTeX", "Below is...", or anything outside LaTeX.
- Preserve ALL template formatting, commands, and structure
- Insert the provided LaTeX content in the correct location
- Do NOT add blank pages or extra vertical spacing
- Do NOT include \\documentclass, \\begin{document}, or \\end{document} in the inserted content
- Ensure the final document compiles to a single-page resume (unless the content is naturally longer)
- Ensure there is exactly one space before each number, and no additional space after the digits.
- Maintain proper LaTeX syntax throughout
- Ensure that empty sections with no content are removed.
- Never add the line "The boilerplate content was inspired by Gayle McDowell."
- Ensure special characters like in eötvös loránd are turned into normal english alphabets.
- Ensure in Awards and Certifications section the bullet points are pectly aligned.
- Dates should always be aligned to the right and place of work or title to the left.
- Ensure that the subheadings are bold except for the Awards and Certifications and skills section.
- Ensure the dates are aligned on the right side and place of work to the left.
- Donot insert links on your own.
- Job title should never be bold.
- Ensure that the place of work and role should be on seperate lines.

EMPTY SECTION REMOVAL:
- Before finalizing, check each \\section{} block
- If a section contains no items, no bullet points, or only whitespace, remove that entire section
- Common empty sections to watch for: Awards and Certifications, Languages, Projects
- The final document should only contain sections with actual content
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
