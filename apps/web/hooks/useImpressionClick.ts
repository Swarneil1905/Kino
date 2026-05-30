"use client"

import { useCallback } from "react"
import { api } from "@/lib/api-client"

/**
 * Returns a fire-and-forget click recorder.
 * Call recordClick(movieId) whenever a user navigates to a movie that was
 * shown in a recommendation row. This writes to the impressions table so
 * we can compute CTR-by-position and per-version A/B metrics.
 */
export function useImpressionClick() {
  const recordClick = useCallback((movieId: number) => {
    const token = localStorage.getItem("kino_token")
    if (!token) return
    // Fire and forget -- never block navigation
    api.recommendations.click(movieId)
  }, [])

  return recordClick
}
