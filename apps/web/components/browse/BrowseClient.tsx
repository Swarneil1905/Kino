"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import Link from "next/link"
import { api } from "@/lib/api-client"
import type { Movie } from "@/lib/types"
import { MovieCard } from "@/components/home/MovieCard"
import { cn } from "@/lib/utils"

const ALL_PILL = "All"

type Props = {
  category: string
  label: string
  genres: string[]
}

export function BrowseClient({ label, genres }: Props) {
  const [activeGenre, setActiveGenre] = useState<string>(ALL_PILL)
  const [movies, setMovies] = useState<Movie[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [initialDone, setInitialDone] = useState(false)
  const sentinelRef = useRef<HTMLDivElement>(null)

  const fetchPage = useCallback(async (genre: string, pg: number, replace: boolean) => {
    setLoading(true)
    try {
      const g = genre === ALL_PILL ? undefined : genre
      const data = await api.movies.list(pg, 24, g)
      setTotal(data.total)
      setMovies((prev) => replace ? data.items : [...prev, ...data.items])
      setPage(pg)
    } finally {
      setLoading(false)
      if (!initialDone) setInitialDone(true)
    }
  }, [initialDone])

  // Initial load
  useEffect(() => {
    fetchPage(activeGenre, 1, true)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeGenre])

  // Infinite scroll sentinel
  useEffect(() => {
    if (!sentinelRef.current) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loading && movies.length < total) {
          fetchPage(activeGenre, page + 1, false)
        }
      },
      { rootMargin: "300px" },
    )
    observer.observe(sentinelRef.current)
    return () => observer.disconnect()
  }, [activeGenre, fetchPage, loading, movies.length, page, total])

  const pills = [ALL_PILL, ...genres]

  return (
    <main className="min-h-screen pt-24 pb-20 px-6 md:px-12" style={{ background: "var(--bg)" }}>
      {/* Page header */}
      <div className="mb-8">
        <h1
          className="font-serif font-bold text-balance"
          style={{ fontSize: "clamp(32px, 5vw, 56px)", letterSpacing: "-0.025em", color: "var(--text)" }}
        >
          {label}
        </h1>
      </div>

      {/* Genre pills */}
      <div className="mb-8 flex flex-wrap gap-2">
        {pills.map((g) => (
          <button
            key={g}
            onClick={() => { if (g !== activeGenre) setActiveGenre(g) }}
            className={cn(
              "rounded-full px-4 py-1.5 text-[13px] font-medium transition-all duration-200",
              activeGenre === g
                ? "text-black"
                : "border text-[#9E9C96] hover:text-[#F0EEE8]",
            )}
            style={
              activeGenre === g
                ? { background: "var(--text)" }
                : { borderColor: "var(--border)", background: "transparent" }
            }
          >
            {g}
          </button>
        ))}
      </div>

      {/* Results count */}
      {initialDone && (
        <p className="mb-6 text-[13px]" style={{ color: "var(--text3)" }}>
          {total.toLocaleString()} titles
        </p>
      )}

      {/* Grid */}
      {!initialDone ? (
        <div
          className="grid gap-3"
          style={{ gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))" }}
        >
          {Array.from({ length: 24 }).map((_, i) => (
            <div
              key={i}
              className="animate-pulse rounded"
              style={{ aspectRatio: "2/3", background: "var(--surface)" }}
            />
          ))}
        </div>
      ) : movies.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-32 gap-3">
          <p className="font-serif text-2xl italic" style={{ color: "var(--text3)" }}>No titles found</p>
          <p className="text-sm" style={{ color: "var(--text3)" }}>Try a different genre</p>
        </div>
      ) : (
        <div
          className="grid gap-3"
          style={{ gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))" }}
        >
          {movies.map((movie, index) => (
            <Link key={`${movie.id}-${index}`} href={`/movie/${movie.id}`} className="block">
              <MovieCard movie={movie} expandDirection="center" />
            </Link>
          ))}
        </div>
      )}

      {/* Infinite scroll sentinel + spinner */}
      <div ref={sentinelRef} className="mt-8 flex justify-center">
        {loading && initialDone && (
          <div
            className="h-6 w-6 animate-spin rounded-full border-2 border-transparent"
            style={{ borderTopColor: "var(--accent)" }}
          />
        )}
      </div>
    </main>
  )
}
