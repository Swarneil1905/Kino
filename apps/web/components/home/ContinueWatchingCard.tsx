"use client"

import { Play } from "lucide-react"
import Link from "next/link"

import type { Movie } from "@/lib/types"
import { imageUrl } from "@/lib/utils"

type ContinueWatchingCardProps = {
  movie: Movie
  progress: number
}

export function ContinueWatchingCard({ movie, progress }: ContinueWatchingCardProps) {
  const backdrop = imageUrl(movie.backdropPath, "w780")
  const clamped = Math.min(100, Math.max(0, progress))

  return (
    <Link
      href={`/movie/${movie.id}`}
      className="group relative block w-full"
      aria-label={`Resume ${movie.title}, ${Math.round(clamped)}% watched`}
    >
      <div
        className="aspect-video w-full overflow-hidden rounded bg-zinc-800 bg-cover bg-center"
        style={{ backgroundImage: backdrop ? `url(${backdrop})` : undefined }}
      >
        {!backdrop && (
          <div className="grid h-full place-items-center p-3 text-center text-xs font-semibold leading-snug text-white/50">
            {movie.title}
          </div>
        )}

        {/* Hover Play overlay */}
        <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
          <Play size={40} className="text-white" fill="currentColor" />
        </div>
      </div>

      {/* Progress bar */}
      <div className="absolute inset-x-0 bottom-0 h-1 bg-[#4d4d4d]">
        <div
          className="h-full bg-kino-red"
          style={{ width: `${clamped}%` }}
        />
      </div>

      {/* Title under thumbnail */}
      <div className="mt-2 line-clamp-1 text-[13px] font-semibold text-white/85">
        {movie.title}
      </div>
    </Link>
  )
}
