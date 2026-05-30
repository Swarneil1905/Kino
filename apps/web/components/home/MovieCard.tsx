"use client"

import { AnimatePresence, motion } from "framer-motion"
import { ChevronDown, Play, Plus, ThumbsDown, ThumbsUp } from "lucide-react"
import Link from "next/link"
import { useEffect, useRef, useState } from "react"

import { useImpressionClick } from "@/hooks/useImpressionClick"
import type { Movie, UserRating } from "@/lib/types"
import { cn, imageUrl } from "@/lib/utils"

const infoVariants = {
  hidden: { opacity: 0, y: 8, scale: 0.96 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.18, ease: [0.25, 0.46, 0.45, 0.94] },
  },
  exit: {
    opacity: 0,
    scale: 0.94,
    transition: { duration: 0.12, ease: "easeIn" },
  },
}

type MovieCardProps = {
  movie: Movie
  rank?: number
  expandDirection?: "left" | "center" | "right"
  userRating?: UserRating | null
  pending?: boolean
  onRate?: (movieId: number, rating: UserRating | null) => void
  onMoreInfo?: (movie: Movie) => void
}

export function MovieCard({
  movie,
  rank,
  expandDirection = "center",
  userRating = null,
  pending = false,
  onRate,
  onMoreInfo,
}: MovieCardProps) {
  const recordClick = useImpressionClick()
  const [expanded, setExpanded] = useState(false)
  const [localRating, setLocalRating] = useState<UserRating | null>(userRating)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => { setLocalRating(userRating) }, [userRating])

  // Prefer poster for 2:3 cards, fall back to backdrop
  const poster = imageUrl(movie.posterPath ?? movie.backdropPath, "w342")
  const backdrop = imageUrl(movie.backdropPath, "w780")

  const clearTimer = () => {
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = null
  }

  const handleRate = (value: UserRating) => {
    const next = localRating === value ? null : value
    setLocalRating(next)
    onRate?.(movie.id, next)
  }

  return (
    <div
      className="relative w-full min-w-0"
      onMouseEnter={() => {
        clearTimer()
        timerRef.current = setTimeout(() => setExpanded(true), 400)
      }}
      onMouseLeave={() => {
        clearTimer()
        setExpanded(false)
      }}
    >
      {/* Ranked number — Top 10 rows */}
      {rank !== undefined && (
        <div className="flex items-end">
          <span
            className="shrink-0 select-none font-black leading-none"
            style={{
              fontSize: "clamp(64px, 9vw, 110px)",
              color: "transparent",
              WebkitTextStroke: "2px rgba(255,255,255,0.15)",
              marginRight: "-6px",
              marginBottom: "-2px",
              zIndex: 1,
            }}
          >
            {rank}
          </span>
          <div className="relative flex-1 min-w-0">
            <div
              className={cn(
                "w-full rounded bg-[var(--surface)] bg-cover bg-center transition-opacity duration-200",
                expanded && "opacity-0",
              )}
              style={{ aspectRatio: "2/3", backgroundImage: poster ? `url(${poster})` : undefined }}
            >
              {!poster && (
                <div className="grid h-full place-items-center p-3 text-center text-xs font-semibold leading-snug" style={{ color: "var(--text3)" }}>
                  {movie.title}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Standard 2:3 poster card */}
      {rank === undefined && (
        <div
          className={cn(
            "relative w-full overflow-hidden rounded bg-[var(--surface)] bg-cover bg-center transition-all duration-[280ms]",
            expanded && "opacity-0",
          )}
          style={{
            aspectRatio: "2/3",
            backgroundImage: poster ? `url(${poster})` : undefined,
            borderRadius: "var(--r)",
            boxShadow: "0 4px 14px rgba(0,0,0,0.55)",
          }}
        >
          {!poster && (
            <div className="flex h-full flex-col items-center justify-end p-3 pb-4">
              {/* Gradient bottom vignette */}
              <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/80 to-transparent" />
              <p className="relative z-10 text-center text-[11px] font-semibold leading-snug" style={{ color: "var(--text)" }}>
                {movie.title}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Hover: scale overlay + detached info card */}
      <AnimatePresence>
        {expanded && (
          <>
            {/* Scaled poster */}
            <div
              className="absolute inset-0 overflow-hidden bg-[var(--surface)] bg-cover bg-center"
              style={{
                backgroundImage: poster ? `url(${poster})` : undefined,
                aspectRatio: "2/3",
                transform: "scale(1.07)",
                borderRadius: "var(--r)",
                boxShadow: "0 18px 40px rgba(0,0,0,0.75)",
                zIndex: 10,
              }}
            >
              {/* Centered play button */}
              <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                <div className="grid h-11 w-11 place-items-center rounded-full bg-white/90">
                  <Play size={18} fill="black" className="ml-0.5" />
                </div>
              </div>
            </div>

            {/* Detached info card below */}
            <motion.div
              className={cn(
                "absolute z-20 w-[280px] overflow-hidden",
                expandDirection === "left" && "right-0 origin-top-right",
                expandDirection === "right" && "left-0 origin-top-left",
                expandDirection === "center" && "left-1/2 -translate-x-1/2 origin-top",
              )}
              style={{
                top: "calc(100% + 6px)",
                background: "var(--surface2)",
                border: "1px solid var(--border)",
                borderRadius: "var(--r)",
                boxShadow: "0 20px 50px rgba(0,0,0,0.8)",
              }}
              variants={infoVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              {/* Backdrop strip */}
              {backdrop && (
                <div
                  className="relative h-32 w-full bg-cover bg-center"
                  style={{ backgroundImage: `url(${backdrop})` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-t from-[var(--surface2)] via-transparent to-transparent" />
                  <div className="absolute bottom-2 left-3 right-3 font-serif text-[13px] font-bold leading-tight" style={{ color: "var(--text)" }}>
                    {movie.title}
                  </div>
                </div>
              )}

              {/* Actions + meta */}
              <div className="space-y-2.5 px-3 py-3">
                <div className="flex items-center gap-2">
                  <button
                    className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-white text-black transition-colors hover:bg-white/85"
                    aria-label="Play"
                  >
                    <Play size={14} fill="currentColor" />
                  </button>
                  <button
                    className="grid h-8 w-8 shrink-0 place-items-center rounded-full border text-white transition-colors hover:border-white"
                    style={{ borderColor: "rgba(255,255,255,0.3)" }}
                    aria-label="Add to list"
                  >
                    <Plus size={14} />
                  </button>
                  <button
                    disabled={pending}
                    className={cn(
                      "grid h-8 w-8 shrink-0 place-items-center rounded-full border transition-colors hover:border-white disabled:opacity-40",
                      localRating === 1 && "bg-white/12",
                    )}
                    style={{ borderColor: "rgba(255,255,255,0.3)", color: "var(--text)" }}
                    onClick={() => handleRate(1)}
                    aria-label="Like"
                  >
                    <ThumbsUp size={13} />
                  </button>
                  <button
                    disabled={pending}
                    className={cn(
                      "grid h-8 w-8 shrink-0 place-items-center rounded-full border transition-colors hover:border-white disabled:opacity-40",
                      localRating === -1 && "bg-white/12",
                    )}
                    style={{ borderColor: "rgba(255,255,255,0.3)", color: "var(--text)" }}
                    onClick={() => handleRate(-1)}
                    aria-label="Dislike"
                  >
                    <ThumbsDown size={13} />
                  </button>
                  <Link
                    href={`/movie/${movie.id}`}
                    className="ml-auto grid h-8 w-8 shrink-0 place-items-center rounded-full border transition-colors hover:border-white"
                    style={{ borderColor: "rgba(255,255,255,0.3)", color: "var(--text)" }}
                    aria-label="More info"
                    onClick={() => { onMoreInfo?.(movie); recordClick(movie.id) }}
                  >
                    <ChevronDown size={16} />
                  </Link>
                </div>

                {/* Meta */}
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] font-semibold">
                  <span style={{ color: "#4ADE80" }}>{movie.matchPercent}% Match</span>
                  <span style={{ color: "var(--text2)" }}>{movie.releaseYear}</span>
                  <span
                    className="border px-1 text-[10px] font-normal"
                    style={{ borderColor: "rgba(255,255,255,0.25)", color: "var(--text2)" }}
                  >
                    {movie.maturityRating}
                  </span>
                  {movie.duration && <span style={{ color: "var(--text3)" }}>{movie.duration}</span>}
                </div>

                {/* Genre chips */}
                {movie.genres.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {movie.genres.slice(0, 3).map((genre, i) => (
                      <span key={genre} className="flex items-center gap-1.5 text-[11px]" style={{ color: "var(--text2)" }}>
                        {i > 0 && <span className="h-0.5 w-0.5 rounded-full" style={{ background: "var(--text3)" }} />}
                        {genre}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
