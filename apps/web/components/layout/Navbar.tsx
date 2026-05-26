"use client"

import { Bell, LogOut, Search } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

import { useScrollPosition } from "@/hooks/useScrollPosition"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api-client"

export function Navbar() {
  const scrollY = useScrollPosition()
  const router = useRouter()
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isAdmin, setIsAdmin] = useState(false)
  const [userInitial, setUserInitial] = useState("K")

  useEffect(() => {
    const sync = () => {
      const token = localStorage.getItem("kino_token")
      const email = localStorage.getItem("kino_email")
      setIsLoggedIn(!!token)
      if (email) setUserInitial(email[0].toUpperCase())
      if (token) {
        api.auth.me().then((u) => setIsAdmin(u.is_admin ?? false)).catch(() => setIsAdmin(false))
      } else {
        setIsAdmin(false)
      }
    }
    sync()
    window.addEventListener("kino:signout", sync)
    return () => window.removeEventListener("kino:signout", sync)
  }, [])

  const handleSignOut = () => {
    localStorage.removeItem("kino_token")
    localStorage.removeItem("kino_user_id")
    localStorage.removeItem("kino_email")
    setIsLoggedIn(false)
    router.push("/login")
  }

  const navLinks: { label: string; href: string }[] = [
    { label: "Home", href: "/" },
    { label: "TV Shows", href: "/" },
    { label: "Movies", href: "/" },
    { label: "New & Popular", href: "/" },
    { label: "My List", href: "/" },
    { label: "Browse by Languages", href: "/" },
    { label: "Metrics", href: "/metrics" },
    ...(isAdmin ? [{ label: "Admin", href: "/admin" }] : []),
  ]

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
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="transition-colors hover:text-white"
            >
              {link.label}
            </Link>
          ))}
          {!isLoggedIn && (
            <Link href="/login" className="transition-colors hover:text-white">Sign In</Link>
          )}
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center border border-white/70 bg-black/30">
          <button className="grid h-8 w-8 place-items-center" onClick={() => setSearchOpen((v) => !v)} aria-label="Search">
            <Search size={18} />
          </button>
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={cn("h-8 bg-transparent text-sm outline-none transition-[width] duration-300", searchOpen ? "w-44 px-2" : "w-0 px-0")}
            placeholder="Titles, genres"
          />
        </div>
        <Bell size={20} />
        {isLoggedIn ? (
          <div className="flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded bg-kino-red text-xs font-bold">
              {userInitial}
            </div>
            <button onClick={handleSignOut} className="grid h-8 w-8 place-items-center rounded text-white/60 hover:text-white" aria-label="Sign out" title="Sign out">
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <div className="grid h-8 w-8 place-items-center rounded bg-white/10 text-xs font-bold text-white/40">?</div>
        )}
      </div>
    </header>
  )
}
