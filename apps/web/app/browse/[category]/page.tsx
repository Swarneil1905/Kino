import { notFound } from "next/navigation"
import { BrowseClient } from "@/components/browse/BrowseClient"

// Maps URL slug → { label, genres[] }
// Multiple genres = OR logic across pills; empty = all movies
export const CATEGORY_CONFIG: Record<string, { label: string; genres: string[] }> = {
  movies:         { label: "Movies",        genres: ["Action", "Drama", "Comedy", "Thriller", "Romance", "Crime", "Mystery", "Adventure", "Fantasy", "Horror", "Western", "War", "Musical"] },
  series:         { label: "Series",        genres: ["Drama", "Crime", "Mystery", "Thriller", "Adventure"] },
  documentaries:  { label: "Documentaries", genres: ["Documentary"] },
  anime:          { label: "Anime",         genres: ["Animation"] },
  sports:         { label: "Sports",        genres: ["Action", "Adventure"] },
}

type PageProps = { params: Promise<{ category: string }> }

export function generateStaticParams() {
  return Object.keys(CATEGORY_CONFIG).map((category) => ({ category }))
}

export default async function BrowsePage({ params }: PageProps) {
  const { category } = await params
  const config = CATEGORY_CONFIG[category]
  if (!config) notFound()

  return <BrowseClient category={category} label={config.label} genres={config.genres} />
}
