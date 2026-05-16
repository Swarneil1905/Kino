"use client"

import { motion } from "framer-motion"
import { Info, Play, Volume2, VolumeX } from "lucide-react"
import { useState } from "react"

import type { Movie } from "@/lib/types"
import { imageUrl } from "@/lib/utils"

const heroContentVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] },
  },
}

type HeroBannerProps = {
  movie: Movie
}

export function HeroBanner({ movie }: HeroBannerProps) {
  const [muted, setMuted] = useState(true)
  const backdrop = imageUrl(movie.backdropPath, "original")

  return (
    <section className="relative min-h-[520px] h-[85vh] overflow-hidden">
      <div
        className="absolute inset-0 scale-[1.05] bg-zinc-900 bg-cover bg-center"
        style={{
          backgroundImage: backdrop
            ? `url(${backdrop})`
            : "linear-gradient(120deg, #1b1b1b 0%, #303030 50%, #101010 100%)",
        }}
      />
      {/* Left vignette — makes text legible against any backdrop */}
      <div className="absolute inset-0 bg-gradient-to-r from-kino-background/90 via-kino-background/40 to-transparent" />
      {/* Bottom fade — blends into content rows */}
      <div className="absolute inset-0 bg-gradient-to-t from-kino-background via-transparent to-transparent" />
      {/* Top fade — softens top edge behind navbar */}
      <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-black/60 to-transparent" />

      <motion.div
        className="absolute bottom-28 left-5 max-w-[500px] md:left-14"
        variants={heroContentVariants}
        initial="hidden"
        animate="visible"
      >
        <div className="mb-3 text-[11px] font-bold uppercase tracking-[3px] text-kino-red">Kino Pick</div>
        <h1 className="mb-4 text-5xl font-black leading-none md:text-6xl">{movie.title}</h1>
        <div className="mb-4 flex items-center gap-3 text-sm font-semibold">
          <span className="text-kino-green">{movie.matchPercent}% Match</span>
          <span>{movie.releaseYear}</span>
          <span className="border border-white/50 px-1 text-xs">{movie.maturityRating}</span>
          <span>{movie.duration}</span>
        </div>
        <p className="mb-6 line-clamp-3 text-lg leading-snug text-white/75">{movie.overview}</p>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 rounded bg-white px-6 py-2.5 font-bold text-black">
            <Play size={20} fill="currentColor" /> Play
          </button>
          <button className="flex items-center gap-2 rounded bg-[#6d6d6e]/70 px-6 py-2.5 font-bold text-white">
            <Info size={20} /> More Info
          </button>
        </div>
      </motion.div>

      <button
        className="absolute bottom-24 right-5 grid h-10 w-10 place-items-center rounded-full border border-white/40 md:right-14"
        onClick={() => setMuted((value) => !value)}
        aria-label={muted ? "Unmute" : "Mute"}
      >
        {muted ? <VolumeX size={20} /> : <Volume2 size={20} />}
      </button>
    </section>
  )
}
