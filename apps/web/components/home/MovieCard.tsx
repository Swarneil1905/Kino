"use client"

import { AnimatePresence, motion } from "framer-motion"
import { ChevronDown, Play, Plus, ThumbsDown, ThumbsUp } from "lucide-react"
import Link from "next/link"
import { useEffect, useRef, useState } from "react"

import type { Movie, UserRating } from "@/lib/types"
import { cn, imageUrl } from "@/lib/utils"

const expandedPanelVariants = {
  hidden: { opacity: 0, scale: 0.85, y: 8 },
  visible: {
    opacity: 1,
    scale: 1,
    y: -36,
    transition: { duration: 0.22, ease: [0.25, 0.46, 0.45, 0.94] },
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    y: 0,
    transition: { duration: 0.15, ease: "easeIn" },
  },
}

type MovieCardProps = {
  movie: Movie
  expandDirection?: "left" | "center" | "right"
  userRating?: UserRating | null
  pending?: boolean
  onRate?: (movieId: number, rating: UserRating | null) => void
  onMoreInfo?: (movie: Movie) => void
}

export function MovieCard({ movie, expandDirection = "center", userRating = null, pending = false, onRate, onMoreInfo }: MovieCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [localRating, setLocalRating] = useState<UserRating | null>(userRating)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    setLocalRating(userRating)
  }, [userRating])

  const poster = imageUrl(movie.posterPath, "w342")
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
      className="relative w-[148px] shrink-0 md:w-[180px] lg:w-[210px]"
      onMouseEnter={() => {
        clearTimer()
        timerRef.current = setTimeout(() => setExpanded(true), 420)
      }}
      onMouseLeave={() => {
        clearTimer()
        setExpanded(false)
      }}
    >
      <div className={cn("aspect-[2/3] rounded bg-kino-surface bg-cover bg-center transition-opacity", expanded && "opacity-0")} style={{ backgroundImage: poster ? `url(${poster})` : undefined }}>
        {!poster && <div className="grid h-full place-items-center p-4 text-center text-xs font-semibold text-white/60">{movie.title}</div>}
      </div>
      {!expanded && (
        <p className="mt-1 truncate text-center text-xs text-white/60">{movie.title}</p>
      )}

      <AnimatePresence>
        {expanded && (
          <motion.div
            className={cn(
              "absolute top-0 z-20 w-[280px] overflow-hidden rounded-lg border border-white/5 bg-kino-surface shadow-[0_16px_40px_rgba(0,0,0,0.7)]",
              expandDirection === "left" && "right-0 origin-top-right",
              expandDirection === "right" && "left-0 origin-top-left",
              expandDirection === "center" && "left-1/2 -translate-x-1/2 origin-top",
            )}
            variants={expandedPanelVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            <div className="relative aspect-video bg-zinc-800 bg-cover bg-center" style={{ backgroundImage: backdrop ? `url(${backdrop})` : undefined }}>
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
              <div className="absolute bottom-2 left-3 text-sm font-bold">{movie.title}</div>
            </div>
            <div className="space-y-3 p-3">
              <div className="flex items-center gap-2">
                <button className="grid h-8 w-8 place-items-center rounded-full bg-white text-black" aria-label="Play">
                  <Play size={16} fill="currentColor" />
                </button>
                <button className="grid h-8 w-8 place-items-center rounded-full border border-white/40 hover:border-white" aria-label="Add to list">
                  <Plus size={16} />
                </button>
                <button disabled={pending} className={cn("grid h-8 w-8 place-items-center rounded-full border border-white/40 hover:border-white disabled:opacity-40", localRating === 1 && "bg-white/15")} onClick={() => handleRate(1)} aria-label="Thumbs up">
                  <ThumbsUp size={16} />
                </button>
                <button disabled={pending} className={cn("grid h-8 w-8 place-items-center rounded-full border border-white/40 hover:border-white disabled:opacity-40", localRating === -1 && "bg-white/15")} onClick={() => handleRate(-1)} aria-label="Thumbs down">
                  <ThumbsDown size={16} />
                </button>
                <Link href={`/movie/${movie.id}`} className="ml-auto grid h-8 w-8 place-items-center rounded-full border border-white/40 hover:border-white" aria-label="More info" onClick={() => onMoreInfo?.(movie)}>
                  <ChevronDown size={18} />
                </Link>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-white/75">
                <span className="text-kino-green">{movie.matchPercent}% Match</span>
                <span>{movie.releaseYear}</span>
                <span className="border border-white/50 px-1">{movie.maturityRating}</span>
                <span>{movie.duration}</span>
              </div>
              <div className="flex flex-wrap items-center gap-1 text-xs text-white/70">
                {movie.genres.map((genre) => (
                  <span key={genre}>{genre}</span>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
