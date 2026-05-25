"use client"

import { useEffect, useState } from "react"

import { api } from "@/lib/api-client"
import type { ContentRowData } from "@/lib/types"

const STORAGE_KEY  = "kino_genre_picks"
const MIN_RATINGS  = 5          // show picker if user has fewer ratings than this
const COLD_LIMIT   = 30         // movies to fetch from cold-start endpoint

/**
 * Controls the onboarding genre picker.
 *
 * Shows the picker when:
 *   - The user is logged in
 *   - They have fewer than MIN_RATINGS ratings
 *   - They haven't already completed onboarding (no localStorage key)
 *
 * Once genres are chosen the picker is hidden, cold-start recs are fetched,
 * and the selection is persisted so the picker never shows again.
 */
export function useOnboarding(ratingCount: number | null) {
  const [showPicker, setShowPicker]     = useState(false)
  const [coldRows,   setColdRows]       = useState<ContentRowData[]>([])
  const [loading,    setLoading]        = useState(false)

  // Decide whether to show the picker on mount / when ratingCount changes
  useEffect(() => {
    if (ratingCount === null) return                         // not loaded yet
    const token       = localStorage.getItem("kino_token")
    if (!token) return                                       // not logged in
    const alreadyDone = localStorage.getItem(STORAGE_KEY)
    if (alreadyDone) {
      // User already picked genres — reload those recs silently
      const genres = JSON.parse(alreadyDone) as string[]
      fetchColdRecs(genres)
      return
    }
    if (ratingCount < MIN_RATINGS) setShowPicker(true)
  }, [ratingCount])

  // Clear on sign-out
  useEffect(() => {
    const handler = () => { setShowPicker(false); setColdRows([]) }
    window.addEventListener("kino:signout", handler)
    return () => window.removeEventListener("kino:signout", handler)
  }, [])

  const fetchColdRecs = async (genres: string[]) => {
    setLoading(true)
    try {
      const { movies } = await api.recommendations.coldStart(genres, COLD_LIMIT)
      if (movies.length > 0) {
        setColdRows([{
          id:      "cold-start",
          title:   "Picked for Your Taste",
          movies,
          variant: "standard",
        }])
      }
    } catch {
      // silently skip — main recs still work
    } finally {
      setLoading(false)
    }
  }

  const completePicker = (genres: string[]) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(genres))
    setShowPicker(false)
    fetchColdRecs(genres)
  }

  return { showPicker, coldRows, coldLoading: loading, completePicker }
}
