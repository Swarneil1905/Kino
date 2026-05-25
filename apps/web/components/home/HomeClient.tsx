"use client"

import { useEffect, useState } from "react"

import { ContentRow } from "@/components/home/ContentRow"
import { HeroBanner } from "@/components/home/HeroBanner"
import { SkeletonRow } from "@/components/ui/SkeletonRow"
import { GenrePicker } from "@/components/onboarding/GenrePicker"
import { useLikedMovies } from "@/hooks/useLikedMovies"
import { useOnboarding } from "@/hooks/useOnboarding"
import { useRatings } from "@/hooks/useRatings"
import { useRecommendations } from "@/hooks/useRecommendations"
import { useSimilarMovies } from "@/hooks/useSimilarMovies"
import { api } from "@/lib/api-client"
import type { ContentRowData, Movie, RatingStore, UserRating } from "@/lib/types"

type HomeClientProps = {
  featured: Movie
  fallbackRows: ContentRowData[]
  initialRatings?: RatingStore
}

export function HomeClient({ featured, fallbackRows, initialRatings = {} }: HomeClientProps) {
  const [refreshKey, setRefreshKey] = useState(0)
  const [ratingCount, setRatingCount] = useState<number | null>(null)

  const handleRatingCommit = () => setRefreshKey((k) => k + 1)

  // Fetch rating count once on mount so onboarding knows if picker is needed
  useEffect(() => {
    const token = localStorage.getItem("kino_token")
    if (!token) { setRatingCount(0); return }
    api.auth.me().then((u) => setRatingCount(u.rating_count)).catch(() => setRatingCount(0))
  }, [])

  const { rows, status } = useRecommendations(fallbackRows, refreshKey)
  const { likedMovies } = useLikedMovies(refreshKey)
  const { ratings, rate, pending } = useRatings(initialRatings, handleRatingCommit)
  const { similarRows } = useSimilarMovies(likedMovies)
  const { showPicker, coldRows, completePicker } = useOnboarding(ratingCount)

  const likedRow: ContentRowData | null =
    likedMovies.length > 0
      ? { id: "liked", title: "Movies You Liked", movies: likedMovies, variant: "standard" }
      : null

  // Once real recommendations load, use the first movie as the hero so we
  // always show a real backdrop image rather than the SSR fallback.
  const featuredMovie =
    status === "success" && rows[0]?.movies[0] ? rows[0].movies[0] : featured

  return (
    <main className="min-h-screen bg-netflix-black">
      {showPicker && <GenrePicker onComplete={completePicker} />}
      <HeroBanner movie={featuredMovie} />
      <div className="relative z-10 -mt-24 space-y-2 pb-20">
        {coldRows.map((row) => (
          <ContentRow key={row.id} row={row} ratings={ratings} pending={pending} onRate={rate} />
        ))}
        {status === "loading"
          ? Array.from({ length: 3 }).map((_, i) => <SkeletonRow key={i} />)
          : rows.map((row) => (
              <ContentRow
                key={row.id}
                row={row}
                ratings={ratings}
                pending={pending}
                onRate={rate}
              />
            ))}
        {similarRows.map((row) => (
          <ContentRow
            key={row.id}
            row={row}
            ratings={ratings}
            pending={pending}
            onRate={rate}
          />
        ))}
        {likedRow && (
          <ContentRow
            row={likedRow}
            ratings={ratings}
            pending={pending}
            onRate={rate}
          />
        )}
      </div>
    </main>
  )
}

