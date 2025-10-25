"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { FileText, Sparkles, Briefcase } from "lucide-react"

interface TemplateSelectorProps {
  selectedTemplate: string
  onTemplateChange: (template: string) => void
}

export function TemplateSelector({ selectedTemplate, onTemplateChange }: TemplateSelectorProps) {
  const templates = [
    {
      id: "template1",
      name: "Classic Professional",
      description: "Clean, ATS-friendly layout ideal for corporate roles.",
      icon: FileText,
    },
    {
      id: "template2",
      name: "Modern Minimalist",
      description: "Stylish layout suitable for startups and creative roles.",
      icon: Sparkles,
    },
    {
      id: "template3",
      name: "Executive Bold",
      description: "Sophisticated design perfect for senior leadership positions.",
      icon: Briefcase,
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-heading">Choose Resume Template</CardTitle>
        <CardDescription>Select a template that best fits your target role</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <RadioGroup value={selectedTemplate} onValueChange={onTemplateChange} className="gap-4">
          {templates.map((template) => {
            const Icon = template.icon
            return (
              <div key={template.id} className="relative">
                <RadioGroupItem value={template.id} id={template.id} className="peer sr-only" />
                <Label
                  htmlFor={template.id}
                  className="flex items-start gap-4 rounded-lg border-2 border-muted bg-card p-4 hover:bg-accent cursor-pointer transition-colors peer-data-[state=checked]:border-primary peer-data-[state=checked]:bg-primary/5"
                >
                  <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="font-semibold leading-none">{template.name}</p>
                    <p className="text-sm text-muted-foreground">{template.description}</p>
                  </div>
                </Label>
              </div>
            )
          })}
        </RadioGroup>
        <p className="text-xs text-muted-foreground text-center pt-2">More templates coming soon!</p>
      </CardContent>
    </Card>
  )
}
