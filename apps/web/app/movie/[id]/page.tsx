import Image from "next/image"
import Link from "next/link"
import { notFound } from "next/navigation"

import { ContentRow } from "@/components/home/ContentRow"
import { fetchMovie } from "@/lib/tmdb"
import type { Movie } from "@/lib/types"
import { imageUrl } from "@/lib/utils"

type PageProps = { params: Promise<{ id: string }> }

export default async function MoviePage({ params }: PageProps) {
  const { id } = await params
  const movie = await fetchMovie(Number(id))
  if (!movie) notFound()

  const backdrop = imageUrl(movie.backdropPath, "original")
  let similarMovies: Movie[] = []
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
    const res = await fetch(`${apiUrl}/recommendations/similar/${movie.id}?limit=12`, { next: { revalidate: 300 } })
    if (res.ok) {
      const data = await res.json()
      similarMovies = data.movies.map((m: Record<string, unknown>) => ({
        id: m.id as number,
        title: m.title as string,
        overview: (m.overview as string) ?? "",
        posterPath: (m.poster_path as string) ?? null,
        backdropPath: (m.backdrop_path as string) ?? null,
        releaseYear: (m.release_year as number) ?? 0,
        genres: (m.genres as string[]) ?? [],
        matchPercent: (m.match_percent as number) ?? 80,
        duration: (m.duration as string) ?? "2h",
        maturityRating: (m.maturity_rating as string) ?? "PG-13",
        voteAverage: (m.vote_average as number) ?? 0,
      }))
    }
  } catch {
    // Similar row optional when API is offline
  }

  return (
    <main className="min-h-screen bg-netflix-black pb-20">
      <section className="relative min-h-[70vh]">
        {backdrop && <Image src={backdrop} alt="" fill className="object-cover" priority unoptimized />}
        <span className="pointer-events-none absolute inset-0 bg-gradient-to-r from-netflix-black via-netflix-black/80 to-transparent" />
        <span className="pointer-events-none absolute inset-0 bg-gradient-to-t from-netflix-black via-transparent to-transparent" />
        <section className="relative z-10 flex min-h-[70vh] items-end px-5 pb-16 md:px-14">
          <article className="max-w-2xl">
            <h1 className="mb-4 text-4xl font-black md:text-6xl">{movie.title}</h1>
            <p className="mb-2 font-semibold text-netflix-match-green">{movie.matchPercent}% Match</p>
            <p className="mb-4 text-sm text-white/70">
              {movie.releaseYear} · {movie.maturityRating} · {movie.duration}
            </p>
            <p className="text-white/80">{movie.overview}</p>
            <Link href="/" className="mt-6 inline-block text-sm text-white/60 hover:text-white">
              ← Back to browse
            </Link>
          </article>
        </section>
      </section>
      {similarMovies.length > 0 && (
        <ContentRow row={{ id: "similar", title: "More Like This", movies: similarMovies }} />
      )}
    </main>
  )
}
