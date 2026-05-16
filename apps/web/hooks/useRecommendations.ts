"use client"

import { useCallback, useEffect, useState } from "react"

import { api } from "@/lib/api-client"
import type { ContentRowData } from "@/lib/types"

type Status = "idle" | "loading" | "success" | "error"

function buildRows(movies: ReturnType<typeof Array.prototype.slice>): ContentRowData[] {
  return [
    { id: "picks",    title: "Top Picks for You",       movies: movies.slice(0, 18) },
    { id: "genre",    title: "Based on Your Ratings",   movies: movies.slice(18, 36) },
    { id: "discover", title: "Discover Something New",  movies: movies.slice(36) },
  ]
}

export function useRecommendations(fallback: ContentRowData[]) {
  const [rows, setRows] = useState<ContentRowData[]>(fallback)
  const [status, setStatus] = useState<Status>("idle")

  // Initial load — read from cache (fast)
  useEffect(() => {
    const token = localStorage.getItem("kino_token")
    if (!token) return
    setStatus("loading")
    api.recommendations
      .get(60)
      .then((data) => { setRows(buildRows(data.movies)); setStatus("success") })
      .catch(() => setStatus("error"))
  }, [])

  // Silent background refresh — called after user rates, no loading flash
  const softRefresh = useCallback(() => {
    const token = localStorage.getItem("kino_token")
    if (!token) return
    // POST /refresh forces recompute, then GET picks up the fresh cache
    api.recommendations
      .refresh()
      .then(() => api.recommendations.get(60))
      .then((data) => { setRows(buildRows(data.movies)) })
      .catch(() => {/* swallow — stale rows are fine */})
  }, [])

  return { rows, status, softRefresh }
}
