import type { ModelMetrics, Movie, RecommendationResponse, UserRating } from "@/lib/types"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

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

async function request<T>(path: string, options: RequestInit = {}, auth = true): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }
  if (auth && typeof window !== "undefined") {
    const token = localStorage.getItem("kino_token")
    if (token) headers.Authorization = `Bearer ${token}`
  }
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  if (!res.ok) {
    // Stale or invalid token — clear session silently, let UI re-render
    if (res.status === 401 && auth && typeof window !== "undefined") {
      localStorage.removeItem("kino_token")
      localStorage.removeItem("kino_user_id")
      localStorage.removeItem("kino_email")
      // Dispatch event so Navbar and hooks can react without a hard redirect
      window.dispatchEvent(new Event("kino:signout"))
    }
    const body = await res.json().catch(() => ({}))
    const detail = typeof body.detail === "string" ? body.detail : "Request failed"
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export const api = {
  auth: {
    register: (email: string, password: string) =>
      request<{ access_token: string; user_id: string }>(
        "/auth/register",
        { method: "POST", body: JSON.stringify({ email, password }) },
        false,
      ),
    login: (email: string, password: string) =>
      request<{ access_token: string; user_id: string }>(
        "/auth/login",
        { method: "POST", body: JSON.stringify({ email, password }) },
        false,
      ),
    me: () => request<{ id: string; email: string; rating_count: number }>("/auth/me"),
  },
  movies: {
    list: (page = 1, limit = 20, genre?: string) => {
      const params = new URLSearchParams({ page: String(page), limit: String(limit) })
      if (genre) params.set("genre", genre)
      return request<{ items: ApiMovie[]; total: number; page: number }>(`/movies?${params}`).then((d) => ({
        ...d,
        items: d.items.map(mapMovie),
      }))
    },
    get: (id: number) => request<ApiMovie>(`/movies/${id}`).then(mapMovie),
    search: (q: string) =>
      request<{ items: ApiMovie[] }>(`/movies/search?q=${encodeURIComponent(q)}`).then((d) => ({
        items: d.items.map(mapMovie),
      })),
  },
  ratings: {
    submit: (movieId: number, value: UserRating | null) =>
      request<{ movie_id: number; value: UserRating | null; updated_at: string }>("/ratings", {
        method: "POST",
        body: JSON.stringify({ movie_id: movieId, value }),
      }),
    mine: () =>
      request<{ ratings: { movie_id: number; value: UserRating }[] }>("/ratings/me").then((d) => ({
        ratings: d.ratings,
      })),
  },
  recommendations: {
    get: (limit = 20) =>
      request<{ movies: ApiMovie[]; cache_hit: boolean; computed_at: string }>(`/recommendations?limit=${limit}`).then(
        (d) => ({ ...d, movies: d.movies.map(mapMovie) }),
      ),
    similar: (movieId: number, limit = 10) =>
      request<{ movies: ApiMovie[] }>(`/recommendations/similar/${movieId}?limit=${limit}`).then((d) => ({
        movies: d.movies.map(mapMovie),
      })),
    refresh: () =>
      request<{ status?: string; computed_at: string; movies?: ApiMovie[] }>("/recommendations/refresh", {
        method: "POST",
      }),
  },
  metrics: {
    get: () => request<ModelMetrics>("/metrics"),
  },
}
