"use client"

import { useEffect, useRef, useState } from "react"
import Link from "next/link"
import { Search, X } from "lucide-react"
import { api } from "@/lib/api-client"
import type { Movie } from "@/lib/types"
import { MovieCard } from "@/components/home/MovieCard"

const CATEGORY_PILLS = ["All", "Action", "Drama", "Comedy", "Sci-Fi", "Thriller", "Animation", "Documentary", "Romance", "Crime"]

export default function SearchPage() {
  const [query, setQuery] = useState("")
  const [activeCategory, setActiveCategory] = useState("All")
  const [results, setResults] = useState<Movie[]>([])
  const [browseMovies, setBrowseMovies] = useState<Movie[]>([])
  const [searching, setSearching] = useState(false)
  const [browseLoaded, setBrowseLoaded] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Auto-focus
  useEffect(() => { inputRef.current?.focus() }, [])

  // Load default popular titles for the "top searches" state
  useEffect(() => {
    api.movies.list(1, 18, undefined)
      .then((d) => { setBrowseMovies(d.items); setBrowseLoaded(true) })
      .catch(() => setBrowseLoaded(true))
  }, [])

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (query.length < 2) {
      setResults([])
      setSearching(false)
      return
    }
    setSearching(true)
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await api.movies.search(query)
        setResults(data.items)
      } catch {
        setResults([])
      } finally {
        setSearching(false)
      }
    }, 280)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query])

  // Category filter on browse grid
  const filteredBrowse = activeCategory === "All"
    ? browseMovies
    : browseMovies.filter((m) => m.genres.includes(activeCategory))

  const isSearching = query.length >= 2

  return (
    <main className="min-h-screen pt-20 pb-20 px-6 md:px-12" style={{ background: "var(--bg)" }}>
      {/* Search input */}
      <div
        className="mb-8 flex items-center gap-3 rounded-lg px-4"
        style={{ background: "var(--surface)", border: "1px solid var(--border)", height: "52px" }}
      >
        <Search size={20} style={{ color: "var(--text3)", flexShrink: 0 }} />
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 bg-transparent text-[15px] outline-none placeholder-[#565650]"
          style={{ color: "var(--text)" }}
          placeholder="Search titles, genres, overview..."
        />
        {query && (
          <button
            onClick={() => setQuery("")}
            className="grid h-6 w-6 shrink-0 place-items-center rounded-full"
            style={{ background: "var(--surface2)", color: "var(--text2)" }}
            aria-label="Clear"
          >
            <X size={13} />
          </button>
        )}
      </div>

      {isSearching ? (
        /* Search results */
        <>
          <div className="mb-6 flex items-center gap-3">
            {searching ? (
              <div
                className="h-5 w-5 animate-spin rounded-full border-2 border-transparent"
                style={{ borderTopColor: "var(--accent)" }}
              />
            ) : (
              <p className="text-[13px]" style={{ color: "var(--text3)" }}>
                {results.length} result{results.length !== 1 ? "s" : ""} for &ldquo;{query}&rdquo;
              </p>
            )}
          </div>
          {results.length === 0 && !searching ? (
            <div className="flex flex-col items-center justify-center py-32 gap-3">
              <p className="font-serif text-2xl italic" style={{ color: "var(--text3)" }}>No results</p>
              <p className="text-sm" style={{ color: "var(--text3)" }}>Try a different title or keyword</p>
            </div>
          ) : (
            <div
              className="grid gap-3"
              style={{ gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))" }}
            >
              {results.map((movie, i) => (
                <Link key={`${movie.id}-${i}`} href={`/movie/${movie.id}`} className="block">
                  <MovieCard movie={movie} expandDirection="center" />
                </Link>
              ))}
            </div>
          )}
        </>
      ) : (
        /* Default browse state */
        <>
          {/* Category pills */}
          <div className="mb-6 flex flex-wrap gap-2">
            {CATEGORY_PILLS.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className="rounded-full px-4 py-1.5 text-[13px] font-medium transition-all duration-200"
                style={
                  activeCategory === cat
                    ? { background: "var(--text)", color: "#0B0B0B" }
                    : { background: "var(--surface)", border: "1px solid var(--border)", color: "var(--text2)" }
                }
              >
                {cat}
              </button>
            ))}
          </div>

          <p className="mb-5 text-[11px] font-bold uppercase tracking-[0.08em]" style={{ color: "var(--text3)" }}>
            Top Titles
          </p>

          {!browseLoaded ? (
            <div
              className="grid gap-3"
              style={{ gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))" }}
            >
              {Array.from({ length: 18 }).map((_, i) => (
                <div
                  key={i}
                  className="animate-pulse rounded"
                  style={{ aspectRatio: "2/3", background: "var(--surface)" }}
                />
              ))}
            </div>
          ) : (
            <div
              className="grid gap-3"
              style={{ gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))" }}
            >
              {filteredBrowse.map((movie, i) => (
                <Link key={`${movie.id}-${i}`} href={`/movie/${movie.id}`} className="block">
                  <MovieCard movie={movie} expandDirection="center" />
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </main>
  )
}
