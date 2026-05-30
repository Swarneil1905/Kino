"use client"

import { motion } from "framer-motion"
import { Info, Play } from "lucide-react"

import type { Movie } from "@/lib/types"
import { imageUrl } from "@/lib/utils"

const heroVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] },
  },
}

type HeroBannerProps = {
  movie: Movie
}

export function HeroBanner({ movie }: HeroBannerProps) {
  const backdrop = imageUrl(movie.backdropPath, "original")
  const genreLabels = movie.genres.slice(0, 3)

  return (
    <section className="relative overflow-hidden" style={{ height: "88vh", minHeight: "520px" }}>
      {/* Backdrop */}
      <div
        className="absolute inset-0 scale-[1.04] bg-zinc-900 bg-cover bg-center"
        style={{
          backgroundImage: backdrop
            ? `url(${backdrop})`
            : "linear-gradient(145deg, #03000D 0%, #0D0030 45%, #1E0050 75%, #0A0020 100%)",
        }}
      />

      {/* Left fog gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#0B0B0B] via-[#0B0B0B]/60 to-transparent" />
      {/* Bottom fade */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#0B0B0B] via-[#0B0B0B]/20 to-transparent" />
      {/* Top fade */}
      <div className="absolute inset-x-0 top-0 h-28 bg-gradient-to-b from-black/50 to-transparent" />

      {/* Content block */}
      <motion.div
        className="absolute bottom-32 left-6 max-w-[520px] md:left-12"
        variants={heroVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Kino Original badge */}
        <div
          className="mb-4 inline-block text-[10px] font-bold uppercase"
          style={{ color: "var(--accent)", letterSpacing: "0.12em" }}
        >
          Kino Original
        </div>

        {/* Playfair Display serif title */}
        <h1
          className="mb-4 font-serif font-bold text-balance"
          style={{
            fontSize: "clamp(42px, 6vw, 72px)",
            letterSpacing: "-0.025em",
            lineHeight: 1.0,
            color: "var(--text)",
          }}
        >
          {movie.title}
        </h1>

        {/* Meta row */}
        <div className="mb-4 flex flex-wrap items-center gap-x-3 gap-y-1 text-[13px] font-semibold">
          <span style={{ color: "#4ADE80" }}>{movie.matchPercent}% Match</span>
          <span style={{ color: "var(--text2)" }}>{movie.releaseYear}</span>
          <span
            className="border px-1 text-[11px] font-normal"
            style={{ borderColor: "rgba(255,255,255,0.3)", color: "var(--text2)" }}
          >
            {movie.maturityRating}
          </span>
          {movie.duration && <span style={{ color: "var(--text2)" }}>{movie.duration}</span>}
          {genreLabels.length > 0 && (
            <span style={{ color: "var(--text3)" }}>{genreLabels.join(" · ")}</span>
          )}
        </div>

        {/* Description */}
        <p
          className="mb-6 line-clamp-3 text-[15px] leading-relaxed"
          style={{ color: "rgba(240,238,232,0.7)" }}
        >
          {movie.overview}
        </p>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            className="flex items-center gap-2 px-7 py-2.5 text-[14px] font-semibold text-black transition-opacity hover:opacity-85"
            style={{ background: "var(--text)", borderRadius: "var(--r)" }}
          >
            <Play size={18} fill="currentColor" />
            Play
          </button>
          <button
            className="flex items-center gap-2 px-6 py-2.5 text-[14px] font-semibold transition-colors hover:bg-white/15"
            style={{
              background: "rgba(240,238,232,0.12)",
              border: "1px solid rgba(255,255,255,0.15)",
              borderRadius: "var(--r)",
              color: "var(--text)",
            }}
          >
            <Info size={18} />
            More Info
          </button>
        </div>
      </motion.div>

      {/* Right rail — faint italic genre labels */}
      <div
        className="absolute bottom-40 right-12 hidden flex-col items-end gap-2 md:flex"
        style={{ opacity: 0.22 }}
      >
        {genreLabels.map((g) => (
          <span key={g} className="font-serif text-[15px] italic" style={{ color: "var(--text)" }}>
            {g}
          </span>
        ))}
      </div>
    </section>
  )
}
