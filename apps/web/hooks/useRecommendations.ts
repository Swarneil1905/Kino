"use client"

import { useCallback, useEffect, useState } from "react"

import { api } from "@/lib/api-client"
import type { ContentRowData, Movie } from "@/lib/types"

type Status = "idle" | "loading" | "success" | "error"

function buildRows(movies: Movie[]): ContentRowData[] {
  const rows: ContentRowData[] = []
  if (movies.length === 0) return rows

  // Always show Top Picks with up to 18 movies
  rows.push({ id: "picks", title: "Top Picks for You", movies: movies.slice(0, 18) })

  // Only add remaining rows if there are enough movies
  if (movies.length > 18) {
    rows.push({ id: "genre", title: "Based on Your Ratings", movies: movies.slice(18, 36) })
  }
  if (movies.length > 36) {
    rows.push({ id: "discover", title: "Discover Something New", movies: movies.slice(36) })
  }

  return rows
}

export function useRecommendations(fallback: ContentRowData[], refreshKey: number = 0) {
  const [rows, setRows] = useState<ContentRowData[]>(fallback)
  const [status, setStatus] = useState<Status>("idle")

  useEffect(() => {
    const token = localStorage.getItem("kino_token")
    if (!token) return

    // First load: show spinner. Subsequent refreshes: silent background update
    if (refreshKey === 0) setStatus("loading")

    const fetchFresh = () => api.recommendations.get(100)
      .then((data) => { setRows(buildRows(data.movies)); setStatus("success") })
      .catch(() => { if (refreshKey === 0) setStatus("error") })

    if (refreshKey === 0) {
      fetchFresh()
    } else {
      api.recommendations.refresh().then(fetchFresh).catch(() => {})
    }
  }, [refreshKey])

  return { rows, status }
}
