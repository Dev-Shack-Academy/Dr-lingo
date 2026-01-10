"use client"

import { useEffect, useRef } from "react"
import { Volume2, Mic } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { Message } from "./medical-translation-chat"

interface ChatMessagesProps {
  messages: Message[]
}

export function ChatMessages({ messages }: ChatMessagesProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 md:px-6">
      <div className="mx-auto max-w-3xl space-y-6">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const isDoctor = message.type === "doctor"

  return (
    <div className={cn("flex gap-3", isDoctor ? "justify-start" : "justify-end")}>
      <div
        className={cn(
          "flex max-w-[85%] flex-col gap-2 rounded-2xl px-4 py-3 md:max-w-[75%]",
          isDoctor
            ? "bg-[var(--doctor-bubble)] text-[var(--doctor-text)]"
            : "bg-[var(--patient-bubble)] text-[var(--patient-text)]",
        )}
      >
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium opacity-70">{message.originalLanguage}</span>
          {message.isVoice && <Mic className="h-3 w-3 opacity-70" />}
        </div>

        <p className="text-pretty text-sm leading-relaxed md:text-base">{message.originalText}</p>

        <div className="mt-1 flex items-center gap-2 border-t border-white/10 pt-2">
          <span className="text-xs opacity-60">{message.translatedLanguage}</span>
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "ml-auto h-6 w-6",
              isDoctor ? "text-[var(--doctor-text)] hover:bg-white/10" : "text-[var(--patient-text)] hover:bg-black/10",
            )}
          >
            <Volume2 className="h-3 w-3" />
            <span className="sr-only">Play translation</span>
          </Button>
        </div>

        <p className="text-pretty text-xs leading-relaxed opacity-80 md:text-sm">{message.translatedText}</p>

        <span className="mt-1 text-xs opacity-50">
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>
    </div>
  )
}
