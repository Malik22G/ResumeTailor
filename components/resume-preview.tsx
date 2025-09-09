"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, FileText } from "lucide-react"
import { cn } from "@/lib/utils"

interface ResumePreviewProps {
  latexContent?: string
  pdfUrl?: string
  onDownloadTex?: () => void
  onDownloadPdf?: () => void
  onDownloadDoc?: () => void
  className?: string
}

export function ResumePreview({
  latexContent,
  pdfUrl,
  onDownloadTex,
  onDownloadPdf,
  onDownloadDoc,
  className,
}: ResumePreviewProps) {
  if (!latexContent && !pdfUrl) {
    return (
      <Card className={cn("w-full", className)}>
        <CardContent className="p-8 text-center">
          <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="font-heading font-semibold text-lg mb-2">No Preview Available</h3>
          <p className="text-muted-foreground">
            Upload your resume and job description to see the tailored result here.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="font-heading text-lg">Resume Preview</CardTitle>
          <div className="flex gap-2">
            {onDownloadTex && (
              <Button variant="outline" size="sm" onClick={onDownloadTex}>
                <Download className="h-4 w-4 mr-2" />
                .tex
              </Button>
            )}
            {onDownloadDoc && (
              <Button variant="outline" size="sm" onClick={onDownloadDoc}>
                <Download className="h-4 w-4 mr-2" />
                .docx
              </Button>
            )}
            {onDownloadPdf && (
              <Button size="sm" onClick={onDownloadPdf}>
                <Download className="h-4 w-4 mr-2" />
                PDF
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {pdfUrl ? (
          <div className="aspect-[8.5/11] bg-muted rounded-b-lg overflow-hidden">
            <iframe src={pdfUrl} className="w-full h-full" title="Resume Preview" />
          </div>
        ) : latexContent ? (
          <div className="max-h-96 overflow-auto p-6 bg-muted/50 rounded-b-lg">
            <pre className="text-xs font-mono whitespace-pre-wrap break-words">{latexContent}</pre>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
