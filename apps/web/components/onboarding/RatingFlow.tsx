"use client"

import { Loader2 } from "lucide-react"
import { useState } from "react"

import { SeedCard } from "@/components/onboarding/SeedCard"
import type { Movie, RatingStore, UserRating } from "@/lib/types"

type RatingFlowProps = {
  seedMovies: Movie[]
  onComplete: (ratings: RatingStore) => Promise<void>
}

export function RatingFlow({ seedMovies, onComplete }: RatingFlowProps) {
  const [ratings, setRatings] = useState<RatingStore>({})
  const [submitting, setSubmitting] = useState(false)
  const ratedCount = Object.keys(ratings).length
  const progress = Math.min(ratedCount, 10)

  const rate = (movieId: number, rating: UserRating) => {
    setRatings((prev) => ({ ...prev, [movieId]: rating }))
  }

  return (
    <main className="min-h-screen bg-[var(--bg)] px-5 py-24 md:px-14">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 text-center">
          <div className="mb-3 text-4xl font-black text-[var(--accent)]">Kino</div>
          <p className="text-kino-muted">Rate 10 movies so Kino can tune your recommendations.</p>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-10">
          {seedMovies.slice(0, 20).map((movie) => (
            <SeedCard key={movie.id} movie={movie} rating={ratings[movie.id] ?? null} onRate={rate} />
          ))}
        </div>
        <div className="sticky bottom-0 mt-10 bg-[var(--bg)]/95 py-5">
          <div className="mb-4 h-1 overflow-hidden rounded bg-white/15">
            <div className="h-full bg-kino-red transition-[width]" style={{ width: `${(progress / 10) * 100}%` }} />
          </div>
          <button
            className="mx-auto flex min-h-11 items-center justify-center rounded bg-white px-6 font-bold text-black disabled:bg-white/25 disabled:text-white/50"
            disabled={ratedCount < 10 || submitting}
            onClick={async () => {
              setSubmitting(true)
              await onComplete(ratings)
              setSubmitting(false)
            }}
          >
            {submitting ? (
              <span className="flex items-center gap-2">
                <Loader2 className="animate-spin" size={18} /> Building your recommendations...
              </span>
            ) : (
              "Continue"
            )}
          </button>
        </div>
      </div>
    </main>
  )
}
