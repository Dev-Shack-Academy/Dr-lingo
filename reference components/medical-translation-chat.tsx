"use client"

import { useState } from "react"
import { ChatHeader } from "./chat-header"
import { ChatMessages } from "./chat-messages"
import { ChatInput } from "./chat-input"

export interface Message {
  id: string
  type: "doctor" | "patient"
  originalText: string
  translatedText: string
  originalLanguage: string
  translatedLanguage: string
  timestamp: Date
  isVoice?: boolean
}

export function MedicalTranslationChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "doctor",
      originalText: "Good morning. How are you feeling today?",
      translatedText: "Goeie môre. Hoe voel jy vandag?",
      originalLanguage: "English",
      translatedLanguage: "Afrikaans",
      timestamp: new Date(Date.now() - 120000),
      isVoice: false,
    },
    {
      id: "2",
      type: "patient",
      originalText: "Ek voel nie lekker nie. Ek het kopseer.",
      translatedText: "I don't feel well. I have a headache.",
      originalLanguage: "Afrikaans",
      translatedLanguage: "English",
      timestamp: new Date(Date.now() - 60000),
      isVoice: true,
    },
    {
      id: "3",
      type: "doctor",
      originalText: "When did the headache start?",
      translatedText: "Wanneer het die kopseer begin?",
      originalLanguage: "English",
      translatedLanguage: "Afrikaans",
      timestamp: new Date(Date.now() - 30000),
      isVoice: false,
    },
  ])

  const [isRecording, setIsRecording] = useState(false)

  const handleSendMessage = (text: string, isVoice: boolean) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      type: "doctor",
      originalText: text,
      translatedText: text,
      originalLanguage: "English",
      translatedLanguage: "Afrikaans",
      timestamp: new Date(),
      isVoice,
    }
    setMessages([...messages, newMessage])
  }

  return (
    <div className="flex h-full flex-col bg-background">
      <ChatHeader />
      <ChatMessages messages={messages} />
      <ChatInput
        onSendMessage={handleSendMessage}
        isRecording={isRecording}
        onToggleRecording={() => setIsRecording(!isRecording)}
      />
    </div>
  )
}
