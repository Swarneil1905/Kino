"use client"

import { HeroBanner } from "@/components/home/HeroBanner"
import { ContentRow } from "@/components/home/ContentRow"
import { SkeletonRow } from "@/components/ui/SkeletonRow"
import { useRecommendations } from "@/hooks/useRecommendations"
import { useRatings } from "@/hooks/useRatings"
import type { ContentRowData, Movie, RatingStore } from "@/lib/types"

type HomeClientProps = {
  featured: Movie
  fallbackRows: ContentRowData[]
  initialRatings?: RatingStore
}

export function HomeClient({ featured, fallbackRows, initialRatings = {} }: HomeClientProps) {
  const { rows, status, softRefresh } = useRecommendations(fallbackRows)
  const { ratings, rate, pending } = useRatings(initialRatings, softRefresh)

  return (
    <main className="min-h-screen bg-netflix-black">
      <HeroBanner movie={featured} />
      <div className="relative z-10 -mt-24 space-y-2 pb-20">
        {status === "loading"
          ? Array.from({ length: 3 }).map((_, i) => <SkeletonRow key={i} />)
          : rows.map((row) => (
              <ContentRow key={row.id} row={row} ratings={ratings} pending={pending} onRate={rate} />
            ))}
      </div>
    </main>
  )
}

