"use client"

import Link from "next/link"

import type { Movie } from "@/lib/types"
import { imageUrl } from "@/lib/utils"

type Top10CardProps = {
  rank: number
  movie: Movie
}

export function Top10Card({ rank, movie }: Top10CardProps) {
  const poster = imageUrl(movie.posterPath, "w500")

  return (
    <Link
      href={`/movie/${movie.id}`}
      className="group flex items-center"
      aria-label={`Rank ${rank}: ${movie.title}`}
    >
      {/* Large stroked rank — outline only against the background */}
      <span
        className="-mr-5 select-none text-[120px] font-black leading-none transition-transform duration-300 group-hover:scale-105 md:text-[160px]"
        style={{
          color: "#141414",
          WebkitTextStroke: "3px #595959",
          textShadow: "0 4px 16px rgba(0,0,0,0.6)",
        }}
      >
        {rank}
      </span>

      {/* Poster (2:3) */}
      <div
        className="aspect-[2/3] w-[110px] flex-shrink-0 rounded bg-zinc-800 bg-cover bg-center shadow-lg transition-transform duration-300 group-hover:scale-105 md:w-[140px]"
        style={{ backgroundImage: poster ? `url(${poster})` : undefined }}
      >
        {!poster && (
          <div className="grid h-full place-items-center p-3 text-center text-xs font-semibold leading-snug text-white/50">
            {movie.title}
          </div>
        )}
      </div>
    </Link>
  )
}
