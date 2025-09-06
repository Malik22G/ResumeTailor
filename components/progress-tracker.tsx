"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { CheckCircle, Clock, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

export type ProcessStep = "idle" | "uploading" | "analyzing" | "tailoring" | "compiling" | "complete" | "error"

interface ProgressTrackerProps {
  currentStep: ProcessStep
  className?: string
}

const steps = [
  { id: "uploading", label: "Uploading Files", description: "Processing your resume and job description" },
  { id: "analyzing", label: "Analyzing Content", description: "Understanding job requirements and your experience" },
  { id: "tailoring", label: "Tailoring Resume", description: "Customizing your resume for this position" },
  { id: "compiling", label: "Compiling PDF", description: "Generating your tailored resume" },
  { id: "complete", label: "Complete", description: "Your resume is ready for download" },
]

export function ProgressTracker({ currentStep, className }: ProgressTrackerProps) {
  const getStepIndex = (step: ProcessStep) => {
    if (step === "idle") return -1
    if (step === "error") return -1
    return steps.findIndex((s) => s.id === step)
  }

  const currentIndex = getStepIndex(currentStep)
  const progress =
    currentStep === "idle"
      ? 0
      : currentStep === "error"
        ? 0
        : currentStep === "complete"
          ? 100
          : ((currentIndex + 1) / steps.length) * 100

  const getStepStatus = (stepIndex: number) => {
    if (currentStep === "error") return "error"
    if (stepIndex < currentIndex) return "complete"
    if (stepIndex === currentIndex) return "active"
    return "pending"
  }

  if (currentStep === "idle") return null

  return (
    <Card className={cn("w-full", className)}>
      <CardContent className="p-6">
        <div className="space-y-6">
          <div>
            <h3 className="font-heading font-semibold text-lg mb-2">Processing Your Resume</h3>
            <Progress value={progress} className="h-2" />
            <p className="text-sm text-muted-foreground mt-2">
              {currentStep === "error"
                ? "An error occurred during processing"
                : currentStep === "complete"
                  ? "Processing complete!"
                  : `${Math.round(progress)}% complete`}
            </p>
          </div>

          <div className="space-y-4">
            {steps.map((step, index) => {
              const status = getStepStatus(index)
              return (
                <div key={step.id} className="flex items-start gap-3">
                  <div
                    className={cn(
                      "flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center mt-0.5",
                      status === "complete" && "bg-primary text-primary-foreground",
                      status === "active" && "bg-primary text-primary-foreground animate-pulse",
                      status === "pending" && "bg-muted text-muted-foreground",
                      status === "error" && "bg-destructive text-destructive-foreground",
                    )}
                  >
                    {status === "complete" ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : status === "active" ? (
                      <Clock className="h-4 w-4" />
                    ) : status === "error" ? (
                      <AlertCircle className="h-4 w-4" />
                    ) : (
                      <div className="w-2 h-2 rounded-full bg-current" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p
                      className={cn(
                        "text-sm font-medium",
                        status === "active" && "text-primary",
                        status === "complete" && "text-foreground",
                        status === "pending" && "text-muted-foreground",
                      )}
                    >
                      {step.label}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">{step.description}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
