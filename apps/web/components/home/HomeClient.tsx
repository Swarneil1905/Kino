"use client"

import { useState } from "react"

import { ContentRow } from "@/components/home/ContentRow"
import { ContinueWatchingRow } from "@/components/home/ContinueWatchingRow"
import { HeroBanner } from "@/components/home/HeroBanner"
import { Top10Row } from "@/components/home/Top10Row"
import { SkeletonRow } from "@/components/ui/SkeletonRow"
import { useLikedMovies } from "@/hooks/useLikedMovies"
import { useRatings } from "@/hooks/useRatings"
import { useRecommendations } from "@/hooks/useRecommendations"
import type { ContentRowData, Movie, RatingStore, UserRating } from "@/lib/types"

type HomeClientProps = {
  featured: Movie
  fallbackRows: ContentRowData[]
  initialRatings?: RatingStore
}

type RenderRowProps = {
  row: ContentRowData
  ratings: RatingStore
  pending: Set<number>
  onRate: (movieId: number, value: UserRating | null) => void
}

function RenderRow({ row, ratings, pending, onRate }: RenderRowProps) {
  switch (row.variant) {
    case "top10":
      return <Top10Row row={row} />
    case "continue-watching":
      return <ContinueWatchingRow row={row} />
    case "standard":
    default:
      return (
        <ContentRow
          row={row}
          ratings={ratings}
          pending={pending}
          onRate={onRate}
        />
      )
  }
}

export function HomeClient({ featured, fallbackRows, initialRatings = {} }: HomeClientProps) {
  const [refreshKey, setRefreshKey] = useState(0)

  const handleRatingCommit = () => setRefreshKey((k) => k + 1)

  const { rows, status } = useRecommendations(fallbackRows, refreshKey)
  const { likedMovies } = useLikedMovies(refreshKey)
  const { ratings, rate, pending } = useRatings(initialRatings, handleRatingCommit)

  const likedRow: ContentRowData | null =
    likedMovies.length > 0
      ? { id: "liked", title: "Movies You Liked", movies: likedMovies, variant: "standard" }
      : null

  return (
    <main className="min-h-screen bg-netflix-black">
      <HeroBanner movie={featured} />
      <div className="relative z-10 -mt-24 space-y-2 pb-20">
        {status === "loading"
          ? Array.from({ length: 3 }).map((_, i) => <SkeletonRow key={i} />)
          : rows.map((row) => (
              <RenderRow
                key={row.id}
                row={row}
                ratings={ratings}
                pending={pending}
                onRate={rate}
              />
            ))}
        {likedRow && (
          <RenderRow
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

