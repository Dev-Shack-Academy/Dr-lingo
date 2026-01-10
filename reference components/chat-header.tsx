"use client"

import { Activity, Globe, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

export function ChatHeader() {
  return (
    <header className="flex items-center justify-between border-b border-border bg-card px-4 py-3 md:px-6 md:py-4">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
          <Activity className="h-5 w-5 text-primary-foreground" />
        </div>
        <div>
          <h1 className="text-balance text-base font-semibold tracking-tight md:text-lg">Medical Translation</h1>
          <p className="text-xs text-muted-foreground md:text-sm">Real-time voice & text</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-9 w-9">
              <Globe className="h-4 w-4" />
              <span className="sr-only">Language settings</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>English ⇄ Afrikaans</DropdownMenuItem>
            <DropdownMenuItem>English ⇄ isiZulu</DropdownMenuItem>
            <DropdownMenuItem>English ⇄ isiXhosa</DropdownMenuItem>
            <DropdownMenuItem>English ⇄ Sesotho</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <Button variant="ghost" size="icon" className="h-9 w-9">
          <Settings className="h-4 w-4" />
          <span className="sr-only">Settings</span>
        </Button>
      </div>
    </header>
  )
}
