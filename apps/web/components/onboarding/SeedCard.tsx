"use client"

import { ThumbsDown, ThumbsUp } from "lucide-react"

import type { Movie, UserRating } from "@/lib/types"
import { cn, imageUrl } from "@/lib/utils"

type SeedCardProps = {
  movie: Movie
  rating: UserRating | null
  onRate: (movieId: number, rating: UserRating) => void
}

export function SeedCard({ movie, rating, onRate }: SeedCardProps) {
  const poster = imageUrl(movie.posterPath, "w342")

  return (
    <div className={cn("group relative aspect-[2/3] overflow-hidden rounded bg-kino-surface bg-cover bg-center transition", rating === 1 && "ring-2 ring-kino-green", rating === -1 && "opacity-40")} style={{ backgroundImage: poster ? `url(${poster})` : undefined }}>
      {!poster && <div className="grid h-full place-items-center p-3 text-center text-sm font-bold">{movie.title}</div>}
      <div className="absolute inset-0 flex items-center justify-center gap-3 bg-black/55 opacity-0 transition-opacity group-hover:opacity-100">
        <button className="grid h-10 w-10 place-items-center rounded-full bg-white text-black" onClick={() => onRate(movie.id, 1)} aria-label="Like">
          <ThumbsUp size={18} />
        </button>
        <button className="grid h-10 w-10 place-items-center rounded-full border border-white/70 bg-black/40" onClick={() => onRate(movie.id, -1)} aria-label="Dislike">
          <ThumbsDown size={18} />
        </button>
      </div>
    </div>
  )
}
