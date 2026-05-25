"use client"

import { useEffect, useState } from "react"

import { api } from "@/lib/api-client"
import type { ContentRowData } from "@/lib/types"

/**
 * Fetches static curated rows (Trending Now + Top 10) that show
 * for all users — logged in or not — based purely on popularity
 * and vote average. No personalisation needed, no auth required.
 */
export function useCuratedRows() {
  const [curatedRows, setCuratedRows] = useState<ContentRowData[]>([])

  useEffect(() => {
    const load = async () => {
      const rows: ContentRowData[] = []

      try {
        const { movies } = await api.movies.trending(30)
        if (movies.length > 0) {
          rows.push({
            id:      "trending",
            title:   "Trending Now",
            movies,
            variant: "standard",
          })
        }
      } catch { /* silently skip */ }

      try {
        const { movies } = await api.movies.topRated(10)
        if (movies.length > 0) {
          rows.push({
            id:      "top10",
            title:   "Top 10 in Your Country Today",
            movies,
            variant: "ranked",
          })
        }
      } catch { /* silently skip */ }

      setCuratedRows(rows)
    }

    load()
  }, [])

  return { curatedRows }
}
