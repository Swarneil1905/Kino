"use client"

import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

import { RatingFlow } from "@/components/onboarding/RatingFlow"
import { api } from "@/lib/api-client"
import { mockMovies } from "@/lib/mock-data"
import type { Movie, RatingStore } from "@/lib/types"

export default function OnboardingPage() {
  const router = useRouter()
  const [seedMovies, setSeedMovies] = useState<Movie[]>(mockMovies.slice(0, 20))

  useEffect(() => {
    api.movies.list(1, 20).then(({ items }) => {
      if (items.length >= 10) setSeedMovies(items)
    }).catch(() => {})
  }, [])

  async function handleComplete(ratings: RatingStore) {
    const entries = Object.entries(ratings)
    await Promise.all(entries.map(([id, value]) => api.ratings.submit(Number(id), value)))
    await api.recommendations.refresh()
    localStorage.setItem("kino_onboarded", "true")
    router.push("/")
  }

  return <RatingFlow seedMovies={seedMovies} onComplete={handleComplete} />
}
