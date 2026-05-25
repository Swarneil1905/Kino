"use client"

import { useState } from "react"

import {
  AlertTriangle,
  Clapperboard,
  Compass,
  Film,
  Flame,
  Globe,
  Heart,
  Laugh,
  Mic2,
  Music2,
  Palette,
  Rocket,
  Search,
  Shield,
  Skull,
  Target,
  Wand2,
  Zap,
} from "lucide-react"

const ALL_GENRES = [
  { name: "Action",      Icon: Zap         },
  { name: "Adventure",   Icon: Compass     },
  { name: "Animation",   Icon: Palette     },
  { name: "Comedy",      Icon: Laugh       },
  { name: "Crime",       Icon: Shield      },
  { name: "Documentary", Icon: Mic2        },
  { name: "Drama",       Icon: Clapperboard },
  { name: "Fantasy",     Icon: Wand2       },
  { name: "Horror",      Icon: Skull       },
  { name: "Musical",     Icon: Music2      },
  { name: "Mystery",     Icon: Search      },
  { name: "Romance",     Icon: Heart       },
  { name: "Sci-Fi",      Icon: Rocket      },
  { name: "Thriller",    Icon: AlertTriangle },
  { name: "War",         Icon: Target      },
]

const MIN_PICKS = 3

type GenrePickerProps = {
  onComplete: (genres: string[]) => void
}

export function GenrePicker({ onComplete }: GenrePickerProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const toggle = (genre: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(genre)) next.delete(genre)
      else next.add(genre)
      return next
    })
  }

  const ready = selected.size >= MIN_PICKS
  const remaining = MIN_PICKS - selected.size

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm">
      <div className="w-full max-w-lg mx-4 bg-zinc-900 border border-zinc-800 rounded-2xl p-8 shadow-2xl">

        {/* Header */}
        <div className="flex items-center gap-3 mb-1">
          <Film className="text-red-500 w-5 h-5" />
          <span className="text-xs font-semibold tracking-widest text-red-500 uppercase">Kino</span>
        </div>
        <h2 className="text-2xl font-bold text-white mb-1">What do you like to watch?</h2>
        <p className="text-zinc-400 text-sm mb-6">
          Pick at least {MIN_PICKS} genres — we'll personalise your feed right away.
        </p>

        {/* Genre grid */}
        <div className="grid grid-cols-3 gap-2 mb-5">
          {ALL_GENRES.map(({ name, Icon }) => {
            const active = selected.has(name)
            return (
              <button
                key={name}
                onClick={() => toggle(name)}
                className={[
                  "group flex items-center gap-2 rounded-xl px-3 py-3 text-sm font-medium transition-all duration-150 border",
                  active
                    ? "bg-red-600/20 border-red-500 text-white"
                    : "bg-zinc-800/60 border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-white",
                ].join(" ")}
              >
                <Icon
                  className={[
                    "w-4 h-4 shrink-0 transition-colors",
                    active ? "text-red-400" : "text-zinc-500 group-hover:text-zinc-300",
                  ].join(" ")}
                />
                <span className="truncate">{name}</span>
              </button>
            )
          })}
        </div>

        {/* Progress bar */}
        <div className="w-full bg-zinc-800 rounded-full h-1 mb-4">
          <div
            className="bg-red-600 h-1 rounded-full transition-all duration-300"
            style={{ width: `${Math.min((selected.size / MIN_PICKS) * 100, 100)}%` }}
          />
        </div>

        {/* CTA */}
        <button
          disabled={!ready}
          onClick={() => onComplete(Array.from(selected))}
          className={[
            "w-full py-3 rounded-xl font-semibold text-sm transition-all duration-150",
            ready
              ? "bg-red-600 hover:bg-red-500 text-white cursor-pointer"
              : "bg-zinc-800 text-zinc-500 cursor-not-allowed",
          ].join(" ")}
        >
          {ready
            ? "Find My Movies"
            : `Select ${remaining} more genre${remaining === 1 ? "" : "s"} to continue`}
        </button>

      </div>
    </div>
  )
}
