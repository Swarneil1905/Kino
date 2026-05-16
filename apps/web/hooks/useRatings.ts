"use client"

import { useCallback, useEffect, useRef, useState } from "react"

import { api } from "@/lib/api-client"
import type { RatingStore, UserRating } from "@/lib/types"

export function useRatings(initial: RatingStore = {}, onRatingCommit?: () => void) {
  const [ratings, setRatings] = useState<RatingStore>(initial)
  const [pending, setPending] = useState<Set<number>>(new Set())
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Cleanup timer on unmount
  useEffect(() => () => { if (debounceRef.current) clearTimeout(debounceRef.current) }, [])

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

        // Debounced refresh: fires 2 s after the LAST rating in a burst
        if (onRatingCommit) {
          if (debounceRef.current) clearTimeout(debounceRef.current)
          debounceRef.current = setTimeout(onRatingCommit, 2000)
        }
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
    [ratings, onRatingCommit],
  )

  return { ratings, rate, pending }
}
