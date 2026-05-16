"use client"

import { useCallback, useState } from "react"

import { api } from "@/lib/api-client"
import type { RatingStore, UserRating } from "@/lib/types"

export function useRatings(initial: RatingStore = {}) {
  const [ratings, setRatings] = useState<RatingStore>(initial)
  const [pending, setPending] = useState<Set<number>>(new Set())

  const rate = useCallback(
    async (movieId: number, value: UserRating | null) => {
      const previous = ratings[movieId] ?? null

      setRatings((prev) => {
        const next = { ...prev }
        if (value === null) delete next[movieId]
        else next[movieId] = value
        return next
      })
      setPending((prev) => new Set(prev).add(movieId))

      try {
        await api.ratings.submit(movieId, value)
      } catch {
        setRatings((prev) => {
          const next = { ...prev }
          if (previous === null) delete next[movieId]
          else next[movieId] = previous
          return next
        })
      } finally {
        setPending((prev) => {
          const next = new Set(prev)
          next.delete(movieId)
          return next
        })
      }
    },
    [ratings],
  )

  return { ratings, rate, pending }
}
