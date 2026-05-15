"use client"

import { AnimatePresence, motion } from "framer-motion"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { useState } from "react"

import { useItemsPerPage } from "@/hooks/useItemsPerPage"
import type { ContentRowData, Movie, RatingStore, UserRating } from "@/lib/types"

import { MovieCard } from "./MovieCard"

function pageVariants(direction: 1 | -1) {
  return {
    enter: { x: direction * 40, opacity: 0 },
    center: {
      x: 0,
      opacity: 1,
      transition: { duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] },
    },
    exit: {
      x: direction * -40,
      opacity: 0,
      transition: { duration: 0.2, ease: "easeIn" },
    },
  }
}

type ContentRowProps = {
  row: ContentRowData
  ratings?: RatingStore
  pending?: Set<number>
  onRate?: (movieId: number, rating: UserRating | null) => void
  onMoreInfo?: (movie: Movie) => void
}

export function ContentRow({ row, ratings = {}, pending, onRate, onMoreInfo }: ContentRowProps) {
  const [page, setPage] = useState(0)
  const [direction, setDirection] = useState<1 | -1>(1)
  const [hovering, setHovering] = useState(false)
  const itemsPerPage = useItemsPerPage()
  const totalPages = Math.max(1, Math.ceil(row.movies.length / itemsPerPage))
  const visibleMovies = row.movies.slice(page * itemsPerPage, (page + 1) * itemsPerPage)

  const go = (nextDirection: 1 | -1) => {
    setDirection(nextDirection)
    setPage((current) => (current + nextDirection + totalPages) % totalPages)
  }

  return (
    <section className="relative -my-[72px] py-[72px]" onMouseEnter={() => setHovering(true)} onMouseLeave={() => setHovering(false)}>
      <div className="mb-3 flex items-center gap-4 px-5 md:px-14">
        <h2 className="text-xl font-bold">{row.title}</h2>
        <div className={`flex gap-1 transition-opacity ${hovering ? "opacity-100" : "opacity-0"}`}>
          {Array.from({ length: totalPages }).map((_, index) => (
            <span key={index} className={index === page ? "h-0.5 w-4 bg-white" : "h-0.5 w-3 bg-white/40"} />
          ))}
        </div>
      </div>
      <div className="relative overflow-visible px-5 md:px-14">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div key={page} custom={direction} variants={pageVariants(direction)} initial="enter" animate="center" exit="exit" className="flex gap-2 md:gap-3">
            {visibleMovies.map((movie, index) => (
              <MovieCard
                key={`${row.id}-${movie.id}`}
                movie={movie}
                expandDirection={index === 0 ? "right" : index === visibleMovies.length - 1 ? "left" : "center"}
                userRating={ratings[movie.id] ?? null}
                pending={pending?.has(movie.id)}
                onRate={onRate}
                onMoreInfo={onMoreInfo}
              />
            ))}
          </motion.div>
        </AnimatePresence>
        {totalPages > 1 && (
          <>
            <button className={`absolute left-0 top-0 grid h-full w-12 place-items-center bg-black/50 transition-opacity hover:bg-black/70 ${hovering ? "opacity-100" : "opacity-0"}`} onClick={() => go(-1)} aria-label="Previous">
              <ChevronLeft size={28} />
            </button>
            <button className={`absolute right-0 top-0 grid h-full w-12 place-items-center bg-black/50 transition-opacity hover:bg-black/70 ${hovering ? "opacity-100" : "opacity-0"}`} onClick={() => go(1)} aria-label="Next">
              <ChevronRight size={28} />
            </button>
          </>
        )}
      </div>
    </section>
  )
}
