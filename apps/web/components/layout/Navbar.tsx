"use client"

import { Bell, LogOut, Search } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { useSession } from "next-auth/react"

import { useScrollPosition } from "@/hooks/useScrollPosition"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api-client"

export function Navbar() {
  const scrollY = useScrollPosition()
  const router = useRouter()
  const { data: session } = useSession()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isAdmin, setIsAdmin] = useState(false)
  const [userInitial, setUserInitial] = useState("K")

  useEffect(() => {
    const localToken = localStorage.getItem("kino_token")
    const localEmail = localStorage.getItem("kino_email")
    const kinoToken = localToken || session?.kinoToken || null
    const email = localEmail || session?.user?.email || null
    const loggedIn = !!(kinoToken || session?.user)

    setIsLoggedIn(loggedIn)
    if (email) setUserInitial(email[0].toUpperCase())

    if (kinoToken) {
      api.auth.me().then((u) => setIsAdmin(u.is_admin ?? false)).catch(() => setIsAdmin(false))
    } else {
      setIsAdmin(false)
    }
  }, [session])

  const handleSignOut = () => {
    localStorage.removeItem("kino_token")
    localStorage.removeItem("kino_user_id")
    localStorage.removeItem("kino_email")
    localStorage.removeItem("kino_onboarded")
    setIsLoggedIn(false)
    setIsAdmin(false)
    window.dispatchEvent(new Event("kino:signout"))
    router.push("/login")
  }

  const navLinks: { label: string; href: string }[] = [
    { label: "Home",          href: "/" },
    { label: "Movies",        href: "/browse/movies" },
    { label: "Series",        href: "/browse/series" },
    { label: "Documentaries", href: "/browse/documentaries" },
    { label: "Anime",         href: "/browse/anime" },
    { label: "Sports",        href: "/browse/sports" },
    { label: "Metrics",       href: "/metrics" },
    ...(isAdmin ? [{ label: "Admin", href: "/admin" }] : []),
  ]

  const solid = scrollY > 60

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 flex h-16 items-center justify-between px-6 transition-all duration-300 md:px-12",
        solid
          ? "border-b border-white/5 bg-[rgba(11,11,11,0.97)] backdrop-blur-sm"
          : "bg-gradient-to-b from-black/70 to-transparent",
      )}
    >
      {/* Left: wordmark + nav */}
      <div className="flex items-center gap-8">
        <Link
          href="/"
          className="select-none font-serif text-[22px] font-bold tracking-tight text-[#C41020]"
          style={{ letterSpacing: "-0.01em" }}
        >
          KINO
        </Link>
        <nav className="hidden items-center gap-5 md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="text-[13px] font-medium text-[#9E9C96] transition-colors duration-200 hover:text-[#F0EEE8]"
            >
              {link.label}
            </Link>
          ))}
          {!isLoggedIn && (
            <Link
              href="/login"
              className="text-[13px] font-medium text-[#9E9C96] transition-colors hover:text-[#F0EEE8]"
            >
              Sign In
            </Link>
          )}
        </nav>
      </div>

      {/* Right: search icon, bell, avatar */}
      <div className="flex items-center gap-3">
        <Link
          href="/search"
          className="grid h-8 w-8 place-items-center rounded transition-colors hover:text-[#F0EEE8]"
          style={{ color: "var(--text2)" }}
          aria-label="Search"
        >
          <Search size={17} />
        </Link>

        <button
          className="grid h-8 w-8 place-items-center transition-colors hover:text-[#F0EEE8]"
          style={{ color: "var(--text2)" }}
          aria-label="Notifications"
        >
          <Bell size={17} />
        </button>

        {isLoggedIn ? (
          <div className="flex items-center gap-2">
            <div
              className="grid h-8 w-8 place-items-center rounded-[10px] text-[11px] font-bold text-white"
              style={{ background: "var(--accent)", letterSpacing: "0.04em" }}
            >
              {userInitial}
            </div>
            <button
              onClick={handleSignOut}
              className="grid h-8 w-8 place-items-center rounded transition-colors hover:text-[#F0EEE8]"
              style={{ color: "var(--text3)" }}
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut size={15} />
            </button>
          </div>
        ) : (
          <div
            className="grid h-8 w-8 place-items-center rounded-[10px] text-[11px] font-bold"
            style={{ background: "rgba(255,255,255,0.08)", color: "var(--text3)" }}
          >
            ?
          </div>
        )}
      </div>
    </header>
  )
}
