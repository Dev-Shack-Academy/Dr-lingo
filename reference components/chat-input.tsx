"use client"

import type React from "react"

import { useState } from "react"
import { Mic, Send, Square } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

interface ChatInputProps {
  onSendMessage: (text: string, isVoice: boolean) => void
  isRecording: boolean
  onToggleRecording: () => void
}

export function ChatInput({ onSendMessage, isRecording, onToggleRecording }: ChatInputProps) {
  const [message, setMessage] = useState("")

  const handleSend = () => {
    if (message.trim()) {
      onSendMessage(message, false)
      setMessage("")
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t border-border bg-card px-4 py-4 md:px-6">
      <div className="mx-auto max-w-3xl">
        {isRecording ? (
          <div className="flex items-center gap-4 rounded-2xl bg-primary/10 px-6 py-4">
            <div className="flex flex-1 items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary">
                <Mic className="h-5 w-5 animate-pulse text-primary-foreground" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Recording...</p>
                <p className="text-xs text-muted-foreground">Listening in English</p>
              </div>
            </div>
            <Button
              onClick={onToggleRecording}
              size="icon"
              className="h-12 w-12 rounded-full bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              <Square className="h-5 w-5 fill-current" />
              <span className="sr-only">Stop recording</span>
            </Button>
          </div>
        ) : (
          <div className="flex items-end gap-2">
            <Button
              onClick={onToggleRecording}
              size="icon"
              variant="outline"
              className={cn(
                "h-12 w-12 shrink-0 rounded-full transition-colors",
                "hover:bg-primary hover:text-primary-foreground",
              )}
            >
              <Mic className="h-5 w-5" />
              <span className="sr-only">Start voice recording</span>
            </Button>

            <div className="relative flex-1">
              <Textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Type a message..."
                className="min-h-[48px] max-h-32 resize-none rounded-2xl bg-input pr-12 text-sm leading-relaxed"
                rows={1}
              />
              <Button
                onClick={handleSend}
                size="icon"
                disabled={!message.trim()}
                className="absolute bottom-1.5 right-1.5 h-9 w-9 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
                <span className="sr-only">Send message</span>
              </Button>
            </div>
          </div>
        )}

        <div className="mt-3 flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-primary" />
            <span>Real-time translation active</span>
          </div>
        </div>
      </div>
    </div>
  )
}
