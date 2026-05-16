"use client"

import { Bell, Search } from "lucide-react"
import Link from "next/link"
import { useState } from "react"

import { useScrollPosition } from "@/hooks/useScrollPosition"
import { cn } from "@/lib/utils"

export function Navbar() {
  const scrollY = useScrollPosition()
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 flex h-16 items-center justify-between px-5 transition-colors duration-500 md:px-14",
        scrollY > 60 ? "bg-kino-background" : "bg-gradient-to-b from-black/80 to-transparent",
      )}
    >
      <div className="flex items-center gap-8">
        <Link href="/" className="text-2xl font-black tracking-normal text-kino-red">
          Kino
        </Link>
        <nav className="hidden items-center gap-5 text-sm text-white/70 md:flex">
          <Link href="/" className="transition-colors hover:text-white">
            Home
          </Link>
          <Link href="/" className="transition-colors hover:text-white">
            Movies
          </Link>
          <Link href="/metrics" className="transition-colors hover:text-white">
            Metrics
          </Link>
          <Link href="/login" className="transition-colors hover:text-white">
            Sign In
          </Link>
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center border border-white/70 bg-black/30">
          <button className="grid h-8 w-8 place-items-center" onClick={() => setSearchOpen((value) => !value)} aria-label="Search">
            <Search size={18} />
          </button>
          <input
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            className={cn("h-8 bg-transparent text-sm outline-none transition-[width] duration-300", searchOpen ? "w-44 px-2" : "w-0 px-0")}
            placeholder="Titles, genres"
          />
        </div>
        <Bell size={20} />
        <div className="grid h-8 w-8 place-items-center rounded bg-kino-red text-xs font-bold">K</div>
      </div>
    </header>
  )
}
