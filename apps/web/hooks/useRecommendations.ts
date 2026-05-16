"use client"

import { useEffect, useState } from "react"

import { api } from "@/lib/api-client"
import type { ContentRowData } from "@/lib/types"

type Status = "idle" | "loading" | "success" | "error"

export function useRecommendations(fallback: ContentRowData[]) {
  const [rows, setRows] = useState<ContentRowData[]>(fallback)
  const [status, setStatus] = useState<Status>("idle")

  useEffect(() => {
    const token = localStorage.getItem("kino_token")
    if (!token) return

    setStatus("loading")
    api.recommendations
      .get(60)
      .then((data) => {
        setRows([
          { id: "picks", title: "Top Picks for You", movies: data.movies.slice(0, 18) },
          { id: "genre", title: "Based on Your Ratings", movies: data.movies.slice(18, 36) },
          { id: "discover", title: "Discover Something New", movies: data.movies.slice(36) },
        ])
        setStatus("success")
      })
      .catch(() => setStatus("error"))
  }, [])

  return { rows, status }
}
