"use client"

import { AnimatePresence, motion } from "framer-motion"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { useState } from "react"

import { useItemsPerPage } from "@/hooks/useItemsPerPage"
import type { ContentRowData } from "@/lib/types"
import { cn } from "@/lib/utils"

import { Top10Card } from "./Top10Card"

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

type Top10RowProps = {
  row: ContentRowData
}

export function Top10Row({ row }: Top10RowProps) {
  const [page, setPage] = useState(0)
  const [direction, setDirection] = useState<1 | -1>(1)
  const [hovering, setHovering] = useState(false)

  // Top 10 rows fit fewer items per page than standard rows because each card
  // has the rank numeral next to it. Tie to global breakpoints, then clamp.
  const perPage = Math.min(useItemsPerPage() - 1, 5)
  const itemsPerPage = Math.max(2, perPage)
  const top10 = row.movies.slice(0, 10)
  const totalPages = Math.max(1, Math.ceil(top10.length / itemsPerPage))
  const visible = top10.slice(page * itemsPerPage, (page + 1) * itemsPerPage)

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
      <div className="mb-2 flex items-baseline gap-3 px-5 md:px-14">
        <h2 className="text-[18px] font-bold tracking-tight text-white">{row.title}</h2>
        <span
          className="flex items-center text-[13px] font-semibold text-kino-cyan transition-opacity duration-300"
          style={{ opacity: hovering && totalPages > 1 ? 1 : 0 }}
        >
          Explore All
          <ChevronRight className="ml-1 inline-block" size={10} />
        </span>
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

      <div className="relative overflow-visible px-5 md:px-14">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={page}
            custom={direction}
            variants={pageVariants(direction)}
            initial="enter"
            animate="center"
            exit="exit"
            className="grid gap-3"
            style={{ gridTemplateColumns: `repeat(${itemsPerPage}, 1fr)` }}
          >
            {visible.map((movie, index) => (
              <Top10Card
                key={`${row.id}-${movie.id}`}
                rank={page * itemsPerPage + index + 1}
                movie={movie}
              />
            ))}
          </motion.div>
        </AnimatePresence>

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
