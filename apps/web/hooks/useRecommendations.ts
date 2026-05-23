"use client"

import { useEffect, useState } from "react"

import { api } from "@/lib/api-client"
import type { ContentRowData, Movie } from "@/lib/types"

type Status = "idle" | "loading" | "success" | "error"

// Build recommendation rows from the ranked list returned by the two-tower model.
// All rows are real — populated entirely from the personalised ranking.
// No synthetic "Continue Watching" or "Top 10" rows.
function buildRows(movies: Movie[]): ContentRowData[] {
  if (movies.length === 0) return []

  const rows: ContentRowData[] = [
    {
      id: "picks",
      title: "Top Picks for You",
      movies: movies.slice(0, 30),
      variant: "standard",
    },
  ]

  if (movies.length > 30) {
    rows.push({
      id: "based-on",
      title: "Based on Your Ratings",
      movies: movies.slice(30, 60),
      variant: "standard",
    })
  }

  if (movies.length > 60) {
    rows.push({
      id: "discover",
      title: "Discover Something New",
      movies: movies.slice(60),
      variant: "standard",
    })
  }

  return rows
}

export function useRecommendations(fallback: ContentRowData[], refreshKey: number = 0) {
  const [rows, setRows] = useState<ContentRowData[]>(fallback)
  const [status, setStatus] = useState<Status>("idle")

  // Reset to fallback when session is cleared (e.g. 401 on refresh)
  useEffect(() => {
    const handler = () => { setRows(fallback); setStatus("idle") }
    window.addEventListener("kino:signout", handler)
    return () => window.removeEventListener("kino:signout", handler)
  }, [fallback])

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
