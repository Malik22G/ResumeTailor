"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { CheckCircle, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface JobDescriptionInputProps {
  title: string
  description: string
  onJobDescriptionSubmit: (text: string) => void
  jobDescription?: string | null
  className?: string
}

export function JobDescriptionInput({
  title,
  description,
  onJobDescriptionSubmit,
  jobDescription,
  className,
}: JobDescriptionInputProps) {
  const [text, setText] = useState(jobDescription || "")
  const [isSubmitted, setIsSubmitted] = useState(!!jobDescription)

  const handleSubmit = () => {
    if (text.trim()) {
      onJobDescriptionSubmit(text.trim())
      setIsSubmitted(true)
    }
  }

  const handleClear = () => {
    setText("")
    setIsSubmitted(false)
    onJobDescriptionSubmit("")
  }

  return (
    <Card className={cn("transition-all duration-200", className)}>
      <CardContent className="p-6">
        <h3 className="font-heading font-semibold text-lg mb-2">{title}</h3>
        <p className="text-muted-foreground text-sm mb-4">{description}</p>

        {isSubmitted && jobDescription ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium text-sm">Job description added</p>
                  <p className="text-xs text-muted-foreground">{jobDescription.length} characters</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={handleClear} className="h-8 w-8 p-0">
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="p-4 bg-background border rounded-lg max-h-32 overflow-y-auto">
              <p className="text-sm text-muted-foreground line-clamp-4">{jobDescription}</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <Textarea
              placeholder="Paste the job description here..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="min-h-[120px] resize-none"
            />
            <Button onClick={handleSubmit} disabled={!text.trim()} className="w-full">
              Add Job Description
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
