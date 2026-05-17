"use client"

import { useEffect, useState } from "react"

import { api } from "@/lib/api-client"
import type { ContentRowData, Movie } from "@/lib/types"

type Status = "idle" | "loading" | "success" | "error"

// Build a Netflix-style mix of rows from the ranked recommendation list.
// Higher-ranked items power the personalised rows; the long tail feeds the
// "Trending", "Top 10", and "Continue Watching" surfaces.
function buildRows(movies: Movie[]): ContentRowData[] {
  if (movies.length === 0) return []

  const rows: ContentRowData[] = []

  // 1. Trending Now — uses the global top of the list.
  rows.push({
    id: "trending",
    title: "Trending Now",
    movies: movies.slice(0, Math.min(18, movies.length)),
    variant: "standard",
  })

  // 2. Top 10 — ranked, shown with large stroked numerals.
  if (movies.length >= 10) {
    rows.push({
      id: "top10",
      title: "Top 10 Movies in Your Region Today",
      movies: movies.slice(0, 10),
      variant: "top10",
    })
  }

  // 3. Top Picks for You — personalised recs.
  if (movies.length > 18) {
    rows.push({
      id: "picks",
      title: "Top Picks for You",
      movies: movies.slice(18, Math.min(48, movies.length)),
      variant: "standard",
    })
  }

  // 4. Continue Watching — synthetic for now; real progress data is a future
  //    backend feature. Pulled from mid-list so the user sees familiar titles.
  if (movies.length > 48) {
    rows.push({
      id: "continue",
      title: "Continue Watching",
      movies: movies.slice(48, Math.min(60, movies.length)),
      variant: "continue-watching",
    })
  }

  // 5. Based on Your Ratings — driven by the same recs model.
  if (movies.length > 60) {
    rows.push({
      id: "based-on",
      title: "Based on Your Ratings",
      movies: movies.slice(60, Math.min(80, movies.length)),
      variant: "standard",
    })
  }

  // 6. New Releases / Discover — the remainder.
  if (movies.length > 80) {
    rows.push({
      id: "new-releases",
      title: "New Releases",
      movies: movies.slice(80),
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
