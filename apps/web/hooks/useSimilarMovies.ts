"use client"

import { useEffect, useState } from "react"

import { api } from "@/lib/api-client"
import type { ContentRowData, Movie } from "@/lib/types"

/**
 * For each of the user's most-recently liked movies (up to 2),
 * fetches similar titles from the two-tower item embeddings and
 * returns them as ready-to-render "Because you watched X" rows.
 *
 * Fires whenever `likedMovies` changes (i.e. after every rating commit).
 */
export function useSimilarMovies(likedMovies: Movie[]) {
  const [similarRows, setSimilarRows] = useState<ContentRowData[]>([])

  useEffect(() => {
    console.log("[SimilarMovies] effect fired, likedMovies count:", likedMovies.length)

    if (!likedMovies.length) {
      setSimilarRows([])
      return
    }

    // Most-recently liked movies are at the end of the array
    // (useLikedMovies preserves insertion order via ratings.mine())
    const seeds = likedMovies.slice(-2).reverse()

    let cancelled = false

    const fetchAll = async () => {
      const rows: ContentRowData[] = []
      console.log("[SimilarMovies] seeds:", seeds.map((m) => ({ id: m.id, title: m.title })))

      for (const movie of seeds) {
        try {
          console.log("[SimilarMovies] fetching similar for:", movie.id, movie.title)
          const { movies } = await api.recommendations.similar(movie.id, 15)
          console.log("[SimilarMovies] got", movies.length, "similar movies for", movie.title)
          // Only add the row if we got a meaningful number of similar titles
          if (!cancelled && movies.length >= 3) {
            rows.push({
              id: `similar-${movie.id}`,
              title: `Because you watched ${movie.title}`,
              movies,
              variant: "standard",
            })
          }
        } catch (err) {
          console.error("[SimilarMovies] error for movie", movie.id, err)
        }
      }

      console.log("[SimilarMovies] final rows:", rows.length)
      if (!cancelled) setSimilarRows(rows)
    }

    fetchAll()

    // Cleanup: if likedMovies changes again before the fetch completes,
    // discard the stale result
    return () => { cancelled = true }
  }, [likedMovies])

  // Clear rows on sign-out
  useEffect(() => {
    const handler = () => setSimilarRows([])
    window.addEventListener("kino:signout", handler)
    return () => window.removeEventListener("kino:signout", handler)
  }, [])

  return { similarRows }
}
