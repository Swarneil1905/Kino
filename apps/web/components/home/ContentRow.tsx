"use client"

import { AnimatePresence, motion } from "framer-motion"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { useState } from "react"

import { useItemsPerPage } from "@/hooks/useItemsPerPage"
import type { ContentRowData, Movie, RatingStore, UserRating } from "@/lib/types"
import { cn } from "@/lib/utils"

import { MovieCard } from "./MovieCard"

function pageVariants(direction: 1 | -1) {
  return {
    enter: { x: direction * 36, opacity: 0 },
    center: {
      x: 0,
      opacity: 1,
      transition: { duration: 0.28, ease: [0.25, 0.46, 0.45, 0.94] },
    },
    exit: {
      x: direction * -36,
      opacity: 0,
      transition: { duration: 0.18, ease: "easeIn" },
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
    <section
      className="relative -my-10 py-10"
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
    >
      {/* Row header */}
      <div className="mb-2 flex items-baseline gap-3 px-5 md:px-14">
        <h2 className="text-[18px] font-bold tracking-tight text-white">{row.title}</h2>

        {/* Explore All — fades in on row hover */}
        <span
          className="flex items-center text-[13px] font-semibold text-kino-cyan transition-opacity duration-300"
          style={{ opacity: hovering && totalPages > 1 ? 1 : 0 }}
        >
          Explore All
          <ChevronRight className="ml-1 inline-block" size={10} />
        </span>

        {/* Page indicator dots */}
        <div
          className="ml-auto flex gap-1 transition-opacity duration-300"
          style={{ opacity: hovering && totalPages > 1 ? 1 : 0 }}
        >
          {Array.from({ length: totalPages }).map((_, index) => (
            <span
              key={index}
              className={cn(
                "block h-[2px] rounded-sm transition-all",
                index === page ? "w-4 bg-white" : "w-3 bg-white/35",
              )}
            />
          ))}
        </div>
      </div>

      {/* Slider */}
      <div className="relative overflow-visible px-5 md:px-14">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={page}
            custom={direction}
            variants={pageVariants(direction)}
            initial="enter"
            animate="center"
            exit="exit"
            className="grid gap-2"
            style={{ gridTemplateColumns: `repeat(${itemsPerPage}, 1fr)` }}
          >
            {visibleMovies.map((movie, index) => (
              <MovieCard
                key={`${row.id}-${movie.id}`}
                movie={movie}
                rank={row.variant === "ranked" ? page * itemsPerPage + index + 1 : undefined}
                expandDirection={
                  index === 0
                    ? "right"
                    : index === visibleMovies.length - 1
                    ? "left"
                    : "center"
                }
                userRating={ratings[movie.id] ?? null}
                pending={pending?.has(movie.id)}
                onRate={onRate}
                onMoreInfo={onMoreInfo}
              />
            ))}
          </motion.div>
        </AnimatePresence>

        {/* Nav arrows */}
        {totalPages > 1 && (
          <>
            <button
              className="absolute left-0 top-0 grid h-full w-11 place-items-center bg-black/50 transition-all duration-300 hover:bg-black/75"
              style={{ opacity: hovering ? 1 : 0 }}
              onClick={() => go(-1)}
              aria-label="Previous page"
            >
              <ChevronLeft size={26} />
            </button>
            <button
              className="absolute right-0 top-0 grid h-full w-11 place-items-center bg-black/50 transition-all duration-300 hover:bg-black/75"
              style={{ opacity: hovering ? 1 : 0 }}
              onClick={() => go(1)}
              aria-label="Next page"
            >
              <ChevronRight size={26} />
            </button>
          </>
        )}
      </div>
    </section>
  )
}
