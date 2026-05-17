export type Movie = {
  id: number
  title: string
  overview: string
  posterPath: string | null
  backdropPath: string | null
  releaseYear: number
  genres: string[]
  matchPercent: number
  duration: string
  maturityRating: string
  voteAverage: number
}

export type ContentRowVariant = "standard" | "top10" | "continue-watching"

export type ContentRowData = {
  id: string
  title: string
  movies: Movie[]
  variant?: ContentRowVariant
  // For "continue-watching" rows: progress per movie id in 0–100
  progress?: Record<number, number>
}

export type UserRating = 1 | -1
export type RatingStore = Record<number, UserRating>

export type RecommendationResponse = {
  movies: Movie[]
  cache_hit: boolean
  computed_at: string
}

export type ModelMetrics = {
  recall_at_10: number
  ndcg_at_10: number
  ips_ndcg_at_10: number
  model_version: string
}

export type UserProfile = {
  id: string
  email: string
  created_at: string
  rating_count: number
}
