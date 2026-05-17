import type { ContentRowData, Movie } from "@/lib/types"
import { mockMovies, mockRows } from "@/lib/mock-data"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

type ApiMovie = {
  id: number
  title: string
  overview: string
  poster_path: string | null
  backdrop_path: string | null
  release_year: number | null
  genres: string[]
  match_percent: number
  duration: string
  maturity_rating: string
  vote_average: number
}

function mapMovie(movie: ApiMovie): Movie {
  return {
    id: movie.id,
    title: movie.title,
    overview: movie.overview,
    posterPath: movie.poster_path,
    backdropPath: movie.backdrop_path,
    releaseYear: movie.release_year ?? 0,
    genres: movie.genres,
    matchPercent: movie.match_percent,
    duration: movie.duration,
    maturityRating: movie.maturity_rating,
    voteAverage: movie.vote_average,
  }
}

async function fetchMoviesFromApi(limit: number): Promise<Movie[]> {
  const res = await fetch(`${API_URL}/movies?page=1&limit=${limit}`, { next: { revalidate: 300 } })
  if (!res.ok) throw new Error("API unavailable")
  const data = await res.json()
  return data.items.map(mapMovie)
}

export async function fetchHomeData(): Promise<{ featured: Movie; fallbackRows: ContentRowData[] }> {
  try {
    const items = await fetchMoviesFromApi(60)
    if (items.length === 0) throw new Error("empty")
    return {
      featured: items[0],
      fallbackRows: [
        { id: "trending", title: "Trending Now", movies: items.slice(0, 18), variant: "standard" },
        { id: "top10", title: "Top 10 Movies in Your Region Today", movies: items.slice(0, 10), variant: "top10" },
        { id: "picks", title: "Top Picks for You", movies: items.slice(18, 36), variant: "standard" },
        { id: "continue", title: "Continue Watching", movies: items.slice(24, 36), variant: "continue-watching" },
        { id: "discover", title: "Discover Something New", movies: items.slice(36), variant: "standard" },
      ],
    }
  } catch {
    return { featured: mockMovies[0], fallbackRows: mockRows }
  }
}

export async function fetchSeedMovies(): Promise<Movie[]> {
  try {
    const items = await fetchMoviesFromApi(20)
    return items.length >= 10 ? items : mockMovies.slice(0, 20)
  } catch {
    return mockMovies.slice(0, 20)
  }
}

export async function fetchMovie(id: number): Promise<Movie | null> {
  try {
    const res = await fetch(`${API_URL}/movies/${id}`, { next: { revalidate: 300 } })
    if (!res.ok) return null
    return mapMovie(await res.json())
  } catch {
    return mockMovies.find((m) => m.id === id) ?? null
  }
}
