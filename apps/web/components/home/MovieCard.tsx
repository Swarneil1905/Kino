"use client"

import { AnimatePresence, motion } from "framer-motion"
import { ChevronDown, Play, Plus, ThumbsDown, ThumbsUp } from "lucide-react"
import Link from "next/link"
import { useEffect, useRef, useState } from "react"

import type { Movie, UserRating } from "@/lib/types"
import { cn, imageUrl } from "@/lib/utils"

const panelVariants = {
  hidden: { opacity: 0, scale: 0.88, y: 6 },
  visible: {
    opacity: 1,
    scale: 1,
    y: -32,
    transition: { duration: 0.2, ease: [0.25, 0.46, 0.45, 0.94] },
  },
  exit: {
    opacity: 0,
    scale: 0.92,
    y: 0,
    transition: { duration: 0.14, ease: "easeIn" },
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

export function MovieCard({
  movie,
  expandDirection = "center",
  userRating = null,
  pending = false,
  onRate,
  onMoreInfo,
}: MovieCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [localRating, setLocalRating] = useState<UserRating | null>(userRating)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => { setLocalRating(userRating) }, [userRating])

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
      className="relative shrink-0 w-[160px] md:w-[196px] lg:w-[224px]"
      onMouseEnter={() => {
        clearTimer()
        timerRef.current = setTimeout(() => setExpanded(true), 420)
      }}
      onMouseLeave={() => {
        clearTimer()
        setExpanded(false)
      }}
    >
      {/* Base card — landscape 16:9 */}
      <div
        className={cn(
          "aspect-video w-full rounded bg-zinc-800 bg-cover bg-center transition-opacity duration-200",
          expanded && "opacity-0",
        )}
        style={{ backgroundImage: backdrop ? `url(${backdrop})` : undefined }}
      >
        {!backdrop && (
          <div className="grid h-full place-items-center p-3 text-center text-xs font-semibold leading-snug text-white/50">
            {movie.title}
          </div>
        )}
      </div>

      {/* Title label below card */}
      {!expanded && (
        <p className="mt-1.5 truncate text-center text-[11px] font-medium text-white/55">
          {movie.title}
        </p>
      )}

      {/* Expanded hover panel */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            className={cn(
              "absolute top-0 z-20 w-[300px] overflow-hidden rounded-md border border-white/8 bg-[#181818] shadow-[0_20px_50px_rgba(0,0,0,0.8)]",
              expandDirection === "left" && "right-0 origin-top-right",
              expandDirection === "right" && "left-0 origin-top-left",
              expandDirection === "center" && "left-1/2 -translate-x-1/2 origin-top",
            )}
            variants={panelVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            {/* Thumbnail */}
            <div
              className="relative aspect-video w-full bg-zinc-800 bg-cover bg-center"
              style={{ backgroundImage: backdrop ? `url(${backdrop})` : undefined }}
            >
              <div className="absolute inset-0 bg-gradient-to-t from-[#181818] via-transparent to-transparent" />
              <div className="absolute bottom-2.5 left-3 right-3 text-sm font-bold leading-tight">
                {movie.title}
              </div>
            </div>

            {/* Action bar */}
            <div className="space-y-2.5 px-3 py-3">
              <div className="flex items-center gap-2">
                <button
                  className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-white text-black transition-colors hover:bg-white/85"
                  aria-label="Play"
                >
                  <Play size={15} fill="currentColor" />
                </button>
                <button
                  className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-white/40 text-white transition-colors hover:border-white"
                  aria-label="Add to list"
                >
                  <Plus size={15} />
                </button>
                <button
                  disabled={pending}
                  className={cn(
                    "grid h-8 w-8 shrink-0 place-items-center rounded-full border border-white/40 text-white transition-colors hover:border-white disabled:opacity-40",
                    localRating === 1 && "border-white/70 bg-white/12",
                  )}
                  onClick={() => handleRate(1)}
                  aria-label="Like"
                >
                  <ThumbsUp size={14} />
                </button>
                <button
                  disabled={pending}
                  className={cn(
                    "grid h-8 w-8 shrink-0 place-items-center rounded-full border border-white/40 text-white transition-colors hover:border-white disabled:opacity-40",
                    localRating === -1 && "border-white/70 bg-white/12",
                  )}
                  onClick={() => handleRate(-1)}
                  aria-label="Dislike"
                >
                  <ThumbsDown size={14} />
                </button>
                <Link
                  href={`/movie/${movie.id}`}
                  className="ml-auto grid h-8 w-8 shrink-0 place-items-center rounded-full border border-white/40 text-white transition-colors hover:border-white"
                  aria-label="More info"
                  onClick={() => onMoreInfo?.(movie)}
                >
                  <ChevronDown size={17} />
                </Link>
              </div>

              {/* Metadata row */}
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs font-semibold">
                <span className="text-[#46d369]">{movie.matchPercent}% Match</span>
                <span className="text-white/70">{movie.releaseYear}</span>
                <span className="border border-white/40 px-1 text-[10px] font-normal text-white/60">
                  {movie.maturityRating}
                </span>
                <span className="text-white/55">{movie.duration}</span>
              </div>

              {/* Genre tags */}
              {movie.genres.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {movie.genres.slice(0, 3).map((genre, i) => (
                    <span key={genre} className="flex items-center gap-1.5 text-[11px] text-white/60">
                      {i > 0 && <span className="h-0.5 w-0.5 rounded-full bg-white/40" />}
                      {genre}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
