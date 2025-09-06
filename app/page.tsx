"use client"

import { useState } from "react"
import axios from "axios"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { FileUpload } from "@/components/file-upload"
import { JobDescriptionInput } from "@/components/job-description-input"
import { ProgressTracker, type ProcessStep } from "@/components/progress-tracker"
import { ResumePreview } from "@/components/resume-preview"
import { ModeToggle } from "@/components/mode-toggle"
import { Sparkles, FileText, Target, Zap } from "lucide-react"

export default function HomePage() {
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [jobDescription, setJobDescription] = useState<string>("")
  const [currentStep, setCurrentStep] = useState<ProcessStep>("idle")
  const [latexContent, setLatexContent] = useState<string>("")
  const [pdfUrl, setPdfUrl] = useState<string>("")
  const [texUrl, setTexUrl] = useState<string>("")

  const canStartProcess = resumeFile && jobDescription.trim() && currentStep === "idle"

  const handleTailorResume = async () => {
    if (!canStartProcess) return;

    const validMimeTypes = [
      "application/msword", 
      "application/pdf", 
      "text/plain", 
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ];

    // Check if the file has a valid MIME type
    if (resumeFile && !validMimeTypes.includes(resumeFile.type)) {
      alert("Invalid file type. Please upload a valid .txt, .pdf, or .docx file.");
      return;
    }

    setCurrentStep("uploading");
    await new Promise((resolve) => setTimeout(resolve, 1500));

    setCurrentStep("analyzing");
    await new Promise((resolve) => setTimeout(resolve, 2000));

    setCurrentStep("tailoring");
    await new Promise((resolve) => setTimeout(resolve, 2500));

    setCurrentStep("compiling");
    await new Promise((resolve) => setTimeout(resolve, 1500));

    try {
      const formData = new FormData();
      formData.append("resume", resumeFile);
      formData.append("job_desc", jobDescription);

      const response = await axios.post("http://127.0.0.1:8000/tailor_resume/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      // Handle the JSON response containing file URLs or paths
      if (response.data.tex_url && response.data.pdf_url) {
        setTexUrl(response.data.tex_url);
        setPdfUrl(response.data.pdf_url);
        setLatexContent("LaTeX file generated successfully!");
      } else if (response.data.error) {
        throw new Error(response.data.error);
      }
      
      setCurrentStep("complete");
    } catch (error) {
      console.error("Error tailoring the resume:", error);
      setLatexContent("Error generating tailored resume.");
      setCurrentStep("idle");
      alert("Error generating tailored resume. Please try again.");
    }
  };

  const handleDownloadTex = () => {
    if (texUrl) {
      const a = document.createElement("a")
      a.href = texUrl
      a.download = "tailored_resume.tex"
      a.click()
    }
  }

  const handleDownloadPdf = () => {
    if (pdfUrl) {
      const a = document.createElement("a")
      a.href = pdfUrl
      a.download = "tailored_resume.pdf"
      a.click()
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Sparkles className="h-5 w-5 text-primary-foreground" />
              </div>
              <h1 className="font-heading font-bold text-xl">Resume Tailor</h1>
            </div>
            <ModeToggle />
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-12 bg-gradient-to-b from-background to-muted/20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="font-heading font-bold text-4xl md:text-5xl mb-4 text-balance">
            Tailor Your Resume with <span className="text-primary">AI Precision</span>
          </h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto text-pretty">
            Upload your resume and job description to get a perfectly tailored resume in LaTeX format, optimized for ATS
            systems and hiring managers.
          </p>

          <div className="flex flex-wrap justify-center gap-6 mb-8">
            <div className="flex items-center gap-2 text-sm">
              <FileText className="h-4 w-4 text-primary" />
              <span>LaTeX Formatting</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Target className="h-4 w-4 text-primary" />
              <span>ATS Optimized</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Zap className="h-4 w-4 text-primary" />
              <span>Instant Results</span>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Upload & Process */}
          <div className="space-y-6">
            <FileUpload
              title="Upload Your Resume"
              description="Upload your current resume in TXT, PDF, or DOCX format"
              acceptedTypes={["text/plain", "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]}
              onFileUpload={setResumeFile}
              uploadedFile={resumeFile}
            />

            <JobDescriptionInput
              title="Job Description"
              description="Paste the job description you're applying for"
              onJobDescriptionSubmit={setJobDescription}
              jobDescription={jobDescription}
            />

            <Card>
              <CardContent className="p-6">
                <Button
                  onClick={handleTailorResume}
                  disabled={!canStartProcess}
                  size="lg"
                  className="w-full font-semibold"
                >
                  <Sparkles className="h-5 w-5 mr-2" />
                  Tailor My Resume!
                </Button>
                {!canStartProcess && (resumeFile || jobDescription) && (
                  <p className="text-sm text-muted-foreground mt-2 text-center">
                    Please upload your resume and add job description to continue
                  </p>
                )}
              </CardContent>
            </Card>

            <ProgressTracker currentStep={currentStep} />
          </div>

          {/* Right Column - Preview */}
          <div>
            <ResumePreview
              latexContent={latexContent}
              pdfUrl={pdfUrl}
              onDownloadTex={handleDownloadTex}
              onDownloadPdf={handleDownloadPdf}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t mt-16 py-8 bg-muted/20">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm text-muted-foreground">Built with AI-powered resume tailoring technology</p>
        </div>
      </footer>
    </div>
  )
}