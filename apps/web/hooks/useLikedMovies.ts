"use client"

import { useCallback, useEffect, useState } from "react"

import { api } from "@/lib/api-client"
import type { Movie } from "@/lib/types"

export function useLikedMovies(refreshKey: number = 0) {
  const [likedMovies, setLikedMovies] = useState<Movie[]>([])

  const fetch = useCallback(async () => {
    const token = localStorage.getItem("kino_token")
    if (!token) return

    try {
      const { ratings } = await api.ratings.mine()
      const likedIds = ratings
        .filter((r) => r.value === 1)
        .map((r) => r.movie_id)
        .slice(-18) // show up to 18 most-recent likes

      if (!likedIds.length) return

      const movies = await Promise.all(likedIds.map((id) => api.movies.get(id)))
      setLikedMovies(movies)
    } catch {
      // silently fail — this row is optional
    }
  }, [])

  useEffect(() => { fetch() }, [fetch, refreshKey])

  useEffect(() => {
    const handler = () => setLikedMovies([])
    window.addEventListener("kino:signout", handler)
    return () => window.removeEventListener("kino:signout", handler)
  }, [])

  return { likedMovies, refetch: fetch }
}
