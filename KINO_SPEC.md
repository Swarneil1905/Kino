# Kino

A Netflix-style movie recommendation web application powered by a two-tower neural retrieval
model. Built as a portfolio project targeting ML and AI engineering roles at companies like
Netflix, Amazon, and Google.

---

## Project Goals

Kino demonstrates end-to-end machine learning engineering across three layers: a two-tower
neural retrieval model trained on MovieLens 25M, a production-style FastAPI inference backend
with FAISS vector search, and a Netflix-quality frontend with real-time recommendation updates.

The project is designed to signal genuine ML engineering depth rather than surface-level API
wrapping. Every component mirrors how Netflix, Amazon, and Google run recommendation systems
in production.

---

## Tech Stack

### Frontend
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- Framer Motion for animations
- Lucide React for icons

### Backend
- FastAPI (Python 3.11)
- PostgreSQL via Railway
- Redis via Railway for recommendation caching
- PyTorch for the two-tower model and ranker
- FAISS for approximate nearest neighbor retrieval
- MLflow for experiment tracking
- Docker and Docker Compose

### Deployment
- Railway for API, PostgreSQL, Redis, and the Next.js frontend
- GitHub Actions for CI/CD on both services

---

## UI Architecture

### Design System

The UI is a faithful reproduction of Netflix's current interface. No emojis, no decorative
dividers, no icon-heavy layouts, no gradients on text. The aesthetic is dark, cinematic, and
high-contrast throughout.

Color palette:
- Background: #141414
- Card surface: #181818
- Brand red: #E50914
- Match percentage green: #46D369
- Primary text: #FFFFFF
- Secondary text: #B3B3B3

Typography uses Inter at varying weights. Cards use 4px border radius. All hover states apply
a 400-420ms delay before triggering to prevent accidental expansion during fast mouse movement.
All page transitions and card animations use Framer Motion with cubic-bezier easing.

No rounded pill navigation. No gradient text. No box shadows on cards in default state.
Shadow appears only on expanded hover cards to lift them visually above surrounding content.

### Navbar

Fixed position, full viewport width. When the page scroll position is below 60px, the navbar
shows a bottom-fading gradient from rgba(0,0,0,0.8) to transparent. Once the user scrolls
past 60px, it transitions to a solid #141414 background over 500ms.

Left side: Kino wordmark in #E50914, font-weight 900, followed by navigation links (Home,
Movies, My List) at 14px in rgba(255,255,255,0.7), transitioning to white on hover.

Right side: expandable search input, notification bell, and a profile avatar (32x32, red
background, white initials). The search input slides open on click with a width transition.
The profile chevron rotates 180 degrees on hover.

### HeroBanner

Full viewport width, 85vh height, minimum 520px. Background is the featured movie's backdrop
image loaded at original resolution, scaled to 1.05x to avoid edge visibility.

Two gradient overlays are layered on top of the backdrop:
- Left-to-right: rgba(20,20,20,0.85) at 0% to transparent at 100%, for text readability
- Bottom-to-top: rgba(20,20,20,1) at 0% to transparent at 35%, to blend into content rows

Content block sits in the bottom-left, max-width 500px. It contains a "Kino Pick" label in
#E50914 at 11px with 3px letter spacing, the movie title at 56px font-weight 900, a metadata
row with match percentage in green, year, maturity rating badge with border, and duration,
a 3-line capped overview in rgba(255,255,255,0.75), and two buttons.

Play button: white background, black text, black filled play icon, 10px 24px padding.
More Info button: rgba(109,109,110,0.7) background, white text, info icon, same padding.

The entire content block animates from opacity 0 and translateY 20px to its resting state
over 600ms on mount. A mute toggle button sits in the bottom-right corner as a circle with
a border at 1px rgba(255,255,255,0.4).

### MovieCard

Default state: poster image at 2:3 aspect ratio, 4px border radius, no visible text.
Widths: 148px on mobile, 180px on tablet, 210px on desktop.

On mouse enter, a 420ms timer starts. If the mouse leaves before 420ms, the timer clears
and nothing happens. After 420ms, the poster fades to opacity 0 and an expanded panel
animates in using Framer Motion.

Expanded panel animation: initial state is opacity 0, scale 0.85, translateY 8px. Final
state is opacity 1, scale 1, translateY -36px. Duration is 220ms with ease-out cubic-bezier.
The panel is 280px wide with 8px border radius, #181818 background, and a subtle 1px border
at rgba(255,255,255,0.05). Box shadow at 0 16px 40px rgba(0,0,0,0.7).

Top of expanded panel: 16:9 backdrop image with a bottom gradient overlay, movie title in
white bold at 13px pinned to the bottom-left.

Below the backdrop: two rows of controls. First row has circular buttons (32x32) for Play
(white fill), Add to List, Thumbs Up, Thumbs Down, and a More Info chevron aligned right.
All outline buttons use 1.5px border at rgba(255,255,255,0.4), transitioning to white on hover.
Active rating buttons (thumbs up or down) get a rgba(255,255,255,0.15) background fill.

Second row: match percentage in #46D369, year, maturity rating badge, duration, then genre
dots separated by 4px white circles at rgba(255,255,255,0.25).

Cards at position 0 in a row expand rightward. Cards at the last position expand leftward.
All others expand from center. This prevents edge clipping on first and last cards.

### ContentRow

Page-based carousel. Each row displays 6 items per page. Navigation is handled by left and
right arrow buttons that fade in on row hover over 200ms transition.

Current page progress indicator: horizontal bars that slide in from the left side on row
hover. The active bar is 16px wide and white. Inactive bars are 12px wide at
rgba(255,255,255,0.4). The bars sit beside the row title in the header.

Page transitions use Framer Motion AnimatePresence in wait mode. Clicking next: current
page exits with opacity 0 and translateX -40px, incoming page enters from translateX 40px.
Clicking previous: directions reverse. Duration is 300ms with ease-out cubic-bezier.

The row wrapper applies 48px top padding and 72px bottom padding via negative margin
technique (padding is added, then equivalent negative margin cancels the layout impact).
This creates vertical clearance for expanded cards without shifting surrounding rows.

Arrow buttons are 48px wide, span full row height, use rgba(0,0,0,0.5) background
transitioning to rgba(0,0,0,0.7) on hover, and contain left or right chevron icons in white
at 28px.

### Onboarding Flow

Shown on first visit before the home screen. A centered page with the Kino wordmark, a
subtitle explaining that ratings are used to personalize recommendations, and a grid of
20 seed movies spanning diverse genres.

Each seed movie shows only the poster with a hover overlay containing a Thumbs Up and
Thumbs Down button. Rating a movie applies an immediate visual response: liked movies get
a 2px solid #46D369 border and a brief scale pulse, disliked movies dim to 40% opacity.

A progress bar at the bottom fills from 0 to 10 as ratings are submitted. The Continue
button is disabled and grayed out until 10 ratings are submitted. On click, it calls the
POST /recommendations/refresh endpoint, then redirects to the home screen.

Ratings are stored in component state and submitted as a batch on Continue. A loading state
replaces the Continue button with a spinner and "Building your recommendations..." label.

---

## UI Coding Spec

This section defines how every UI layer is actually built — component interfaces, state
ownership, server vs client boundaries, animation variants, hooks, and the API client.
This is the reference to open in Cursor before writing any component.

### Server vs Client Component Boundaries

Next.js App Router distinguishes server components (run only on the server, can fetch data,
cannot use hooks or browser APIs) from client components (marked with "use client", run in
the browser, can use hooks and events).

Server components in Kino:
  app/layout.tsx          Root layout, no interactivity, sets font and metadata
  app/page.tsx            Home page data fetcher, passes data to HomeClient
  app/metrics/page.tsx    Fetches model metrics from the API, passes to MetricsClient

Client components in Kino (all require "use client" at the top):
  components/layout/Navbar.tsx          Reads scroll position, manages search state
  components/home/HomeClient.tsx        Owns rating state, renders hero and rows
  components/home/HeroBanner.tsx        Manages muted toggle state
  components/home/ContentRow.tsx        Manages page, direction, hovering state
  components/home/MovieCard.tsx         Manages expanded state, hover timer, user rating
  components/onboarding/RatingFlow.tsx  Manages seed ratings, progress, submission
  components/onboarding/SeedCard.tsx    Handles individual seed movie rating

The pattern for every page route: the page.tsx server component fetches data and renders
a single *Client.tsx client component, passing the fetched data as props. This keeps data
fetching on the server while all interactivity stays in the client tree.

HomeClient.tsx is the top-level client component for the home screen. It owns the global
rating state (RatingStore) and the rate() callback, passing both down to every ContentRow
which passes them further down to every MovieCard. This single-owner pattern avoids
duplicate rating state across rows.

### TypeScript Interfaces

All shared types live in lib/types.ts. No type is defined inline inside a component file.

```typescript
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

export type ContentRowData = {
  id: string
  title: string
  movies: Movie[]
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
```

### Component Props Interfaces

Each component's props are defined in the same file, directly above the component function.
No separate props files.

```typescript
// HomeClient.tsx
type HomeClientProps = {
  featured: Movie
  initialRows: ContentRowData[]
}

// HeroBanner.tsx
type HeroBannerProps = {
  movie: Movie
}

// ContentRow.tsx
type ContentRowProps = {
  row: ContentRowData
  ratings?: RatingStore
  onRate?: (movieId: number, rating: UserRating | null) => void
  onMoreInfo?: (movie: Movie) => void
}

// MovieCard.tsx
type MovieCardProps = {
  movie: Movie
  expandDirection?: "left" | "center" | "right"
  userRating?: UserRating | null
  onRate?: (movieId: number, rating: UserRating | null) => void
  onMoreInfo?: (movie: Movie) => void
}

// SeedCard.tsx (onboarding)
type SeedCardProps = {
  movie: Movie
  rating: UserRating | null
  onRate: (movieId: number, rating: UserRating) => void
}

// RatingFlow.tsx (onboarding container)
type RatingFlowProps = {
  seedMovies: Movie[]
  onComplete: (ratings: RatingStore) => Promise<void>
}

// MetricCard.tsx
type MetricCardProps = {
  label: string
  value: string | number
  description: string
}

// SkeletonCard.tsx - no props
// SkeletonRow.tsx
type SkeletonRowProps = {
  title: string
  count?: number  // defaults to 6
}
```

### Component State and Refs

Defines every piece of local state and every ref inside each client component. Nothing
in this list should surprise Cursor when it generates the component bodies.

Navbar:
  scrollY: number                     from useScrollPosition hook, drives bg transition
  searchOpen: boolean                 controls search input visibility, default false
  searchQuery: string                 controlled input value, default ""

HeroBanner:
  muted: boolean                      toggles mute icon appearance, default true
  No other state. The featured movie is a prop, no local data fetching.

MovieCard:
  expanded: boolean                   whether the hover panel is showing, default false
  userRating: UserRating | null       tracks the active rating for this card, default null
                                      initialized from the userRating prop on mount
  timerRef: RefObject<ReturnType<typeof setTimeout>>
                                      holds the 420ms delay timer, cleared on mouse leave

  Note: userRating is derived from the parent's RatingStore on every render via the
  userRating prop. The local state is only used for optimistic visual updates before
  the parent's onRate callback propagates the new value back down.

ContentRow:
  page: number                        current page index, default 0
  direction: 1 | -1                   last navigation direction for animation, default 1
  hovering: boolean                   whether the row is being hovered, default false

  itemsPerPage: number                from useItemsPerPage hook, responsive value
  totalPages: number                  derived: Math.ceil(row.movies.length / itemsPerPage)
  visibleMovies: Movie[]              derived: row.movies.slice(page * itemsPerPage,
                                        (page + 1) * itemsPerPage)

RatingFlow:
  ratings: RatingStore                accumulates user ratings during onboarding, default {}
  submitting: boolean                 true while the onComplete callback is running
  ratedCount: number                  derived: Object.keys(ratings).length

### Framer Motion Variants

All animation variants are defined as constants at the top of each component file,
outside the component function, so they are not recreated on every render.

```typescript
// HeroBanner.tsx
const heroContentVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] },
  },
}

// MovieCard.tsx
const expandedPanelVariants = {
  hidden: { opacity: 0, scale: 0.85, y: 8 },
  visible: {
    opacity: 1,
    scale: 1,
    y: -36,
    transition: { duration: 0.22, ease: [0.25, 0.46, 0.45, 0.94] },
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    y: 0,
    transition: { duration: 0.15, ease: "easeIn" },
  },
}

// ContentRow.tsx
// Direction-aware page transition: pass direction as the custom prop to AnimatePresence
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
// Usage inside ContentRow:
// <AnimatePresence mode="wait" custom={direction}>
//   <motion.div
//     key={page}
//     custom={direction}
//     variants={pageVariants(direction)}
//     initial="enter"
//     animate="center"
//     exit="exit"
//   >
```

### Hooks

#### useScrollPosition (hooks/useScrollPosition.ts)

Returns the current window.scrollY as a number, updating on every scroll event with a
passive listener. Used only by Navbar to drive the background transition.

```typescript
"use client"
import { useState, useEffect } from "react"

export function useScrollPosition(): number {
  const [scrollY, setScrollY] = useState(0)
  useEffect(() => {
    const handler = () => setScrollY(window.scrollY)
    window.addEventListener("scroll", handler, { passive: true })
    return () => window.removeEventListener("scroll", handler)
  }, [])
  return scrollY
}
```

#### useItemsPerPage (hooks/useItemsPerPage.ts)

Returns the number of movie cards to show per page in ContentRow, based on viewport width.
Recalculates on window resize. Used only by ContentRow.

```typescript
"use client"
import { useState, useEffect } from "react"

export function useItemsPerPage(): number {
  const [count, setCount] = useState(6)
  useEffect(() => {
    const update = () => {
      if (window.innerWidth < 640) setCount(3)
      else if (window.innerWidth < 768) setCount(4)
      else if (window.innerWidth < 1024) setCount(5)
      else setCount(6)
    }
    update()
    window.addEventListener("resize", update, { passive: true })
    return () => window.removeEventListener("resize", update)
  }, [])
  return count
}
```

#### useRatings (hooks/useRatings.ts)

Owns the global RatingStore for the home screen. Provides an optimistic rate() function
that updates local state immediately, calls the API in the background, and reverts on
failure. Also triggers a background recommendation cache refresh after each rating.

```typescript
"use client"
import { useState, useCallback } from "react"
import { api } from "@/lib/api-client"
import type { RatingStore, UserRating } from "@/lib/types"

export function useRatings(initial: RatingStore = {}) {
  const [ratings, setRatings] = useState<RatingStore>(initial)
  const [pending, setPending] = useState<Set<number>>(new Set())

  const rate = useCallback(
    async (movieId: number, value: UserRating | null) => {
      const previous = ratings[movieId] ?? null

      setRatings((prev) => {
        const next = { ...prev }
        if (value === null) delete next[movieId]
        else next[movieId] = value
        return next
      })
      setPending((prev) => new Set(prev).add(movieId))

      try {
        await api.ratings.submit(movieId, value)
        api.recommendations.refresh().catch(() => {})
      } catch {
        setRatings((prev) => {
          const next = { ...prev }
          if (previous === null) delete next[movieId]
          else next[movieId] = previous
          return next
        })
      } finally {
        setPending((prev) => {
          const next = new Set(prev)
          next.delete(movieId)
          return next
        })
      }
    },
    [ratings]
  )

  return { ratings, rate, pending }
}
```

The pending set tracks which movie IDs have in-flight API calls. MovieCard can read
pending.has(movie.id) to disable rating buttons while a submission is in progress.

#### useRecommendations (hooks/useRecommendations.ts)

Fetches personalized recommendations from the API when a logged-in user lands on the
home screen. Falls back to the initial server-fetched rows on error or when unauthenticated.

```typescript
"use client"
import { useState, useEffect } from "react"
import { api } from "@/lib/api-client"
import type { ContentRowData } from "@/lib/types"

type Status = "idle" | "loading" | "success" | "error"

export function useRecommendations(fallback: ContentRowData[]) {
  const [rows, setRows] = useState<ContentRowData[]>(fallback)
  const [status, setStatus] = useState<Status>("idle")

  useEffect(() => {
    const token = localStorage.getItem("kino_token")
    if (!token) return

    setStatus("loading")
    api.recommendations
      .get(60)
      .then((data) => {
        // Group flat recommendation list into thematic rows
        // Row 0: first 18 movies as "Top Picks for You"
        // Row 1: next 18 filtered to the user's most-rated genre
        // Row 2: remaining movies as "Discover Something New"
        const picks = data.movies.slice(0, 18)
        const genre = data.movies.slice(18, 36)
        const discover = data.movies.slice(36)
        setRows([
          { id: "picks", title: "Top Picks for You", movies: picks },
          { id: "genre", title: "Based on Your Ratings", movies: genre },
          { id: "discover", title: "Discover Something New", movies: discover },
        ])
        setStatus("success")
      })
      .catch(() => setStatus("error"))
  }, [])

  return { rows, status }
}
```

### API Client (lib/api-client.ts)

Single module that owns all communication with the FastAPI backend. Every function returns
a typed Promise. Auth tokens are read from localStorage under the key `kino_token`. The
module exports a single `api` object with five namespaces so imports are stable across
refactors.

```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = true
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }
  if (auth) {
    const token = typeof window !== "undefined" ? localStorage.getItem("kino_token") : null
    if (token) headers["Authorization"] = `Bearer ${token}`
  }
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail ?? "Request failed")
  }
  return res.json() as Promise<T>
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

export const api = {
  auth: {
    register: (email: string, password: string) =>
      request<{ access_token: string; user_id: string }>(
        "/auth/register",
        { method: "POST", body: JSON.stringify({ email, password }) },
        false
      ),
    login: (email: string, password: string) =>
      request<{ access_token: string; user_id: string }>(
        "/auth/login",
        { method: "POST", body: JSON.stringify({ email, password }) },
        false
      ),
    me: () =>
      request<{ id: string; email: string; rating_count: number }>("/auth/me"),
  },

  movies: {
    list: (page = 1, limit = 20, genre?: string) => {
      const params = new URLSearchParams({ page: String(page), limit: String(limit) })
      if (genre) params.set("genre", genre)
      return request<{ items: import("@/lib/types").Movie[]; total: number; page: number }>(
        `/movies?${params.toString()}`
      )
    },
    get: (id: number) =>
      request<import("@/lib/types").Movie>(`/movies/${id}`),
    search: (q: string) =>
      request<{ items: import("@/lib/types").Movie[] }>(`/movies/search?q=${encodeURIComponent(q)}`),
  },

  ratings: {
    submit: (movieId: number, value: 1 | -1 | null) =>
      request<{ movie_id: number; value: 1 | -1 | null; updated_at: string }>(
        "/ratings",
        { method: "POST", body: JSON.stringify({ movie_id: movieId, value }) }
      ),
    mine: () =>
      request<{ ratings: { movie_id: number; value: 1 | -1 }[] }>("/ratings/me"),
  },

  recommendations: {
    get: (limit = 20) =>
      request<{ movies: import("@/lib/types").Movie[]; cache_hit: boolean; computed_at: string }>(
        `/recommendations?limit=${limit}`
      ),
    similar: (movieId: number, limit = 10) =>
      request<{ movies: import("@/lib/types").Movie[] }>(
        `/recommendations/similar/${movieId}?limit=${limit}`
      ),
    refresh: () =>
      request<{ status: string; computed_at: string }>(
        "/recommendations/refresh",
        { method: "POST" }
      ),
  },

  metrics: {
    get: () =>
      request<{
        recall_at_10: number
        ndcg_at_10: number
        ips_ndcg_at_10: number
        model_version: string
      }>("/metrics"),
  },
}
```

Error handling pattern: callers `catch` `ApiError` and check `.status`. A 401 status
anywhere in the app triggers a token clear and redirect to /login. This is centralised in
a top-level error boundary in app/layout.tsx rather than repeated per-hook.

### Tailwind Configuration

The complete `tailwind.config.ts` establishes the design system used throughout the app.

```typescript
import type { Config } from "tailwindcss"

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        netflix: {
          red: "#E50914",
          black: "#141414",
          card: "#181818",
          "text-muted": "#B3B3B3",
          "match-green": "#46D369",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Helvetica Neue", "Arial", "sans-serif"],
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out forwards",
        "slide-up": "slide-up 0.6s ease-out forwards",
      },
    },
  },
  plugins: [],
}

export default config
```

The `fade-in` animation is used on the Navbar logo and on lazy-loaded images as they
resolve. The `slide-up` animation is applied to the HeroBanner text block.

### Global CSS Utilities (app/globals.css)

Beyond Tailwind's reset, globals.css adds three things:

1. `color-scheme: dark` on `:root` so browser chrome (scrollbars, inputs) matches the
   dark background without extra styling.

2. `scrollbar-hide` utility class used on ContentRow's inner container to suppress the
   horizontal scrollbar while preserving scroll functionality on touch devices.

3. `::selection` override sets the highlight color to Netflix red (#E50914) so text
   selections match the brand palette.

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    color-scheme: dark;
  }
  * {
    box-sizing: border-box;
  }
  html {
    scroll-behavior: smooth;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
  body {
    background-color: #141414;
    color: #ffffff;
    overflow-x: hidden;
  }
  ::selection {
    background-color: #e50914;
    color: #ffffff;
  }
}

@layer utilities {
  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
  .text-balance {
    text-wrap: balance;
  }
}
```

### Skeleton Loading States

Skeletons are shown in two situations: when the home page loads and the API call for
personalized recommendations is in-flight (status === "loading" from useRecommendations),
and when movie images are loading for the first time.

#### SkeletonCard

Matches the dimensions of a collapsed MovieCard exactly so the layout does not shift when
real cards replace skeletons. Uses a CSS shimmer animation defined inline.

```typescript
// components/ui/SkeletonCard.tsx
export function SkeletonCard() {
  return (
    <div
      className="relative flex-shrink-0 rounded overflow-hidden bg-netflix-card"
      style={{ width: "calc((100% - 5 * 0.5rem) / 6)", aspectRatio: "2/3" }}
    >
      <div className="absolute inset-0 animate-pulse bg-gradient-to-r from-netflix-card via-white/5 to-netflix-card bg-[length:200%_100%]" />
    </div>
  )
}
```

#### SkeletonRow

Renders a row title placeholder and six SkeletonCard instances to fill a full content row.

```typescript
// components/ui/SkeletonRow.tsx
import { SkeletonCard } from "./SkeletonCard"

export function SkeletonRow() {
  return (
    <section className="py-2 mb-6">
      <div className="px-4 sm:px-8 lg:px-14 mb-3">
        <div className="h-5 w-40 rounded bg-netflix-card animate-pulse" />
      </div>
      <div className="flex gap-2 px-4 sm:px-8 lg:px-14">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    </section>
  )
}
```

ContentRow renders SkeletonRow when status === "loading" is passed as a prop from the
parent HomeClient component.

### Page Compositions

#### HomeClient (components/home/HomeClient.tsx)

The home screen is split between a server component (app/page.tsx) that fetches the
initial data and a client component (HomeClient) that owns interactive state. This
separation keeps the initial render fast (no JS bundle needed for first paint) while
enabling real-time rating and recommendation updates.

```typescript
"use client"

import { HeroBanner } from "@/components/home/HeroBanner"
import { ContentRow } from "@/components/home/ContentRow"
import { SkeletonRow } from "@/components/ui/SkeletonRow"
import { useRecommendations } from "@/hooks/useRecommendations"
import { useRatings } from "@/hooks/useRatings"
import type { Movie, ContentRowData, RatingStore } from "@/lib/types"

interface HomeClientProps {
  featured: Movie
  fallbackRows: ContentRowData[]
  initialRatings?: RatingStore
}

export function HomeClient({ featured, fallbackRows, initialRatings = {} }: HomeClientProps) {
  const { rows, status } = useRecommendations(fallbackRows)
  const { ratings, rate, pending } = useRatings(initialRatings)

  return (
    <main className="min-h-screen bg-netflix-black">
      <HeroBanner movie={featured} />
      <div className="relative z-10 -mt-24 space-y-2 pb-20">
        {status === "loading"
          ? Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)
          : rows.map((row) => (
              <ContentRow
                key={row.id}
                row={row}
                ratings={ratings}
                pending={pending}
                onRate={rate}
              />
            ))}
      </div>
    </main>
  )
}
```

app/page.tsx stays a server component and only renders `<HomeClient>`. It passes
`fallbackRows` from the TMDB server fetch so unauthenticated users see real content
immediately without waiting for the API.

#### Model Dashboard (app/metrics/page.tsx)

Server component. Fetches from GET /metrics and renders three MetricCard components.
Falls back to null values with a "Model metrics unavailable" message if the API is down.

```typescript
// app/metrics/page.tsx
import { api } from "@/lib/api-client"

async function getMetrics() {
  try {
    return await api.metrics.get()
  } catch {
    return null
  }
}

export default async function MetricsPage() {
  const metrics = await getMetrics()

  return (
    <main className="min-h-screen bg-netflix-black px-4 sm:px-8 lg:px-14 py-24">
      <h1 className="text-2xl font-semibold text-white mb-2">Model Performance</h1>
      <p className="text-netflix-text-muted mb-10 max-w-2xl">
        Offline evaluation on the held-out test split of MovieLens 25M.
        IPS-NDCG corrects for popularity bias using inverse propensity scores.
      </p>
      {metrics === null ? (
        <p className="text-netflix-text-muted">Model metrics unavailable.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-2xl">
          <MetricCard label="Recall@10" value={metrics.recall_at_10} />
          <MetricCard label="NDCG@10" value={metrics.ndcg_at_10} />
          <MetricCard label="IPS-NDCG@10" value={metrics.ips_ndcg_at_10} />
        </div>
      )}
    </main>
  )
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-netflix-card rounded p-6">
      <p className="text-netflix-text-muted text-sm mb-1">{label}</p>
      <p className="text-white text-3xl font-bold">{(value * 100).toFixed(1)}%</p>
    </div>
  )
}
```

#### Movie Detail (app/movie/[id]/page.tsx)

Server component. Fetches the movie by ID from GET /movies/{id} and renders a full-screen
detail view with the backdrop, metadata, and a horizontally scrollable similar movies row
populated from GET /recommendations/similar/{id}.

The full implementation is deferred to Phase 3 but the route exists as a placeholder from
Phase 1 to allow `<Link href={/movie/${movie.id}}>` in MovieCard.

### Responsive Breakpoints

Card widths are set using a CSS calc() expression inside ContentRow so that exactly N
cards fit the row with consistent 8px gaps, regardless of container width:

```
width: calc((100% - (N - 1) * 0.5rem) / N)
```

The value of N is provided by useItemsPerPage. At each breakpoint:

| Viewport      | N (cards per page) | Card width (approx) |
|---------------|-------------------|----------------------|
| < 640px       | 3                 | ~30% of row          |
| 640px – 767px | 4                 | ~23% of row          |
| 768px – 1023px| 5                 | ~18% of row          |
| >= 1024px     | 6                 | ~15% of row          |

MovieCard's expanded state uses `width: 110%` to grow beyond the grid cell. The
`expandDirection` logic (left / center / right) shifts the expanded panel using absolute
positioning anchored to the card's left or right edge so it always stays within the row
container's visual bounds.

The HeroBanner is always 85vh with a max content width of 600px for the title/description
block. Below 640px the action buttons stack vertically and the description is truncated to
3 lines.

The Navbar collapses the full navigation link list at breakpoints below 1024px, showing
only the logo, a hamburger icon, and the right-side icons (search, notifications, profile).

---

## Backend API

### Architecture

FastAPI application with async request handlers throughout. PostgreSQL stores all persistent
data. Redis caches computed user embeddings and recommendation lists to avoid running
inference on every request. The ML inference layer (two-tower model, FAISS index, ranker)
is loaded into memory once at application startup using FastAPI lifespan events, making
subsequent requests fast.

All endpoints require a valid JWT in the Authorization header except for the auth routes.
JWT tokens expire after 7 days. Passwords are hashed with bcrypt at 12 rounds.

Request validation uses Pydantic v2 models throughout. All database operations use
SQLAlchemy 2.0 async sessions. Database connection pooling is configured with a pool size
of 10 and max overflow of 20 for Railway's PostgreSQL.

### API Endpoints

#### Authentication

POST /auth/register
Request: { email, password }
Response: { access_token, token_type, user_id }
Creates a new user, hashes the password, returns a JWT.

POST /auth/login
Request: { email, password }
Response: { access_token, token_type, user_id }
Validates credentials, returns a JWT.

GET /auth/me
Response: { id, email, created_at, rating_count }
Returns the current authenticated user's profile.

#### Movies

GET /movies
Query params: page (int), limit (int, max 50), genre (str), year (int)
Response: { items: Movie[], total: int, page: int }
Paginated movie list with optional genre and year filtering.

GET /movies/{id}
Response: Movie object with full metadata
Single movie detail endpoint used by the More Info panel.

GET /movies/search
Query params: q (str, min length 2)
Response: { items: Movie[] }
Full-text search across title and overview using PostgreSQL tsvector.

#### Ratings

POST /ratings
Request: { movie_id: int, value: 1 | -1 | null }
Response: { movie_id, value, updated_at }
Submits or updates a rating. A null value removes an existing rating.
After insertion, invalidates the Redis cache for that user.

GET /ratings/me
Response: { ratings: { movie_id: int, value: 1 | -1 }[] }
Returns all ratings submitted by the current user.

#### Recommendations

GET /recommendations
Query params: limit (int, default 20, max 50)
Response: { movies: Movie[], cache_hit: bool, computed_at: str }
Returns personalized recommendations. Checks Redis first. On a cache miss, computes the
user embedding from stored ratings, runs FAISS retrieval, applies the ranker, filters
already-rated movies, and caches the result with a 15-minute TTL.

GET /recommendations/similar/{movie_id}
Query params: limit (int, default 10)
Response: { movies: Movie[] }
Item-to-item retrieval. Fetches the stored item embedding for movie_id from the FAISS
index and retrieves the nearest neighbors. Does not require authentication.

POST /recommendations/refresh
Response: { status: "ok", computed_at: str }
Forces a recompute of the user's embedding and recommendation list regardless of cache state.
Called by the frontend after the onboarding flow and after batch rating sessions.

#### Model Metrics

GET /metrics
Response: { recall_at_10: float, ndcg_at_10: float, ips_ndcg_at_10: float, model_version: str }
Returns the offline evaluation metrics computed during training. Values are read from a
static JSON file bundled with the API at build time. Used by the model dashboard page.

### Data Models (Pydantic Schemas)

Movie:
  id: int
  tmdb_id: int
  title: str
  overview: str
  poster_path: str | None
  backdrop_path: str | None
  release_year: int
  runtime_minutes: int
  maturity_rating: str
  vote_average: float
  genres: list[str]
  popularity_score: float
  match_percent: int  (computed per-user, not stored)

RatingSubmit:
  movie_id: int
  value: Literal[1, -1] | None

RecommendationResponse:
  movies: list[Movie]
  cache_hit: bool
  computed_at: datetime

UserProfile:
  id: UUID
  email: str
  created_at: datetime
  rating_count: int

---

## ML Architecture

### Dataset

MovieLens 25M contains 25 million ratings from 162,000 users on 62,000 movies.
Each record: user_id, movie_id, rating (0.5 to 5.0 in 0.5 increments), timestamp.

Rating treatment for training:
- Ratings 4.0 and above are treated as implicit positives
- Ratings below 2.5 are treated as implicit negatives
- Ratings between 2.5 and 3.5 are excluded (ambiguous signal)

Train / validation / test split: 80% / 10% / 10%, split by timestamp per user so
the validation and test sets always contain each user's most recent interactions.
This mirrors a realistic recommendation scenario where models are evaluated on
future behavior, not random holdouts.

Movie metadata is supplemented from the TMDB API via a title-year join to obtain
poster paths, backdrop paths, overview text, genres, and runtime minutes. The join
is done once during preprocessing and the result is stored in PostgreSQL.

### Two-Tower Model

The two-tower model is a dual-encoder architecture. The User Tower and Item Tower
independently map their inputs to a shared 128-dimensional embedding space. Similarity
is the dot product of their L2-normalized output vectors, which is equivalent to cosine
similarity and maps directly to FAISS IndexFlatIP retrieval.

#### User Tower

Input features:
- User ID: learned embedding lookup, dimension 64
- Interaction history: mean-pooled item embeddings of the user's top 50 rated movies,
  weighted by rating value (positives weighted +1, negatives -0.5)
- Genre affinity vector: 18-dimensional, one value per genre representing the user's
  average normalized rating for movies of that genre

These three signals are concatenated to form the user input vector. The tower applies:
  Linear(input_dim, 256) -> BatchNorm -> ReLU -> Dropout(0.2)
  Linear(256, 128) -> BatchNorm -> ReLU -> Dropout(0.2)
  Linear(128, 128) -> L2Normalize

#### Item Tower

Input features:
- Movie ID: learned embedding lookup, dimension 64
- Genre encoding: 18-dimensional multi-hot vector
- Release decade: scalar, normalized to [0, 1] over the range 1920-2030
- Log popularity score: log(1 + raw_popularity), StandardScaler normalized

Concatenated and passed through:
  Linear(input_dim, 256) -> BatchNorm -> ReLU -> Dropout(0.2)
  Linear(256, 128) -> BatchNorm -> ReLU -> Dropout(0.2)
  Linear(128, 128) -> L2Normalize

#### Training

Loss: sampled softmax cross-entropy with in-batch negatives.
For each positive (user, item) pair in a batch, all other items in the batch serve as
negatives. Logits are the matrix product of user embeddings and item embeddings, scaled
by a learned temperature parameter initialized to 0.07.

Optimizer: AdamW, learning rate 1e-3, weight decay 1e-4
Schedule: cosine annealing over 20 epochs, minimum learning rate 1e-5
Batch size: 2048
Device: single GPU (A100 or T4 in Google Colab)
Approximate training time: 3 hours on MovieLens 25M

After each epoch the FAISS index is rebuilt from all item embeddings and Recall@10 and
NDCG@10 are computed on the validation set. The checkpoint with the best validation
NDCG@10 is saved as the final model.

### FAISS Index

After training, all 62,000 item embeddings are computed from the Item Tower in a single
forward pass and stored in a FAISS IndexFlatIP (inner product) index. L2 normalization
on both user and item embeddings makes inner product equivalent to cosine similarity,
so IndexFlatIP gives exact nearest neighbor results without approximation error.

For 62,000 items at 128 dimensions, the index occupies roughly 32 MB in memory, which
is well within Railway's service limits. Query latency for top-200 retrieval is 2-5ms.

The index is serialized to faiss_index.bin using faiss.write_index and bundled into the
Docker image. At API startup, it is loaded via faiss.read_index and kept in memory for
the lifetime of the process. A separate movie_id_map.json maps FAISS index positions
(0 to 61,999) back to database movie IDs.

At inference time for a given user:
1. Compute user features from their stored ratings in PostgreSQL
2. Run User Tower forward pass to get 128-dim embedding
3. Query FAISS for top 200 candidates
4. Filter out movies the user has already rated
5. Pass candidates to the ranking layer
6. Return top 20 ranked results

The user embedding is cached in Redis after computation (key: emb:{user_id}, TTL 1 hour).
The full recommendation list is cached separately (key: rec:{user_id}, TTL 15 minutes).

### Ranking Layer

A lightweight MLP reranker rescores the 200 FAISS candidates. The ranker uses richer
feature interactions that the two-tower model cannot capture due to its decoupled architecture.

Input features (per candidate):
- 128-dim user embedding
- 128-dim item embedding
- Element-wise product of user and item embeddings (128-dim)
- User's genre affinity score for the item's primary genre (scalar)
- Item log-popularity score (scalar)
- Item release decade (scalar)

Total input dimension: 387

Architecture:
  Linear(387, 256) -> ReLU -> Dropout(0.1)
  Linear(256, 64) -> ReLU -> Dropout(0.1)
  Linear(64, 1) -> Sigmoid

Training loss: Bayesian Personalized Ranking (BPR) loss, which optimizes for correct
relative ordering of positive items over negative items rather than absolute relevance
prediction. Optimizer: Adam at 5e-4. 10 epochs. Trained on the same train split as
the two-tower model.

The ranker adds approximately 3-8ms of latency per request when scoring 200 candidates,
bringing total recommendation latency to roughly 15-30ms on Railway's standard tier.

### Offline Evaluation

Three metrics are computed on the held-out test set and reported in the model dashboard.

Recall@10: the fraction of held-out positive interactions that appear in the model's top
10 predictions. Measures coverage of relevant items.

NDCG@10: normalized discounted cumulative gain at rank 10. Rewards correct predictions
appearing at higher ranks more than lower ranks. The primary training metric.

IPS-weighted NDCG@10: the Netflix-specific metric. MovieLens ratings suffer from popularity
bias because users are more likely to have seen (and therefore rated) popular movies.
A model trained naively on this data will systematically over-recommend popular items even
when a user's actual preferences differ.

Inverse Propensity Scoring (IPS) corrects for this bias by re-weighting each evaluation
sample by the inverse of the item's selection probability. The selection probability for
a movie is estimated as its rating frequency in the training set divided by the maximum
frequency across all movies, clipped at a minimum of 0.01 to prevent extreme weights.

IPS-NDCG@10 = sum( (IPS_weight_i * gain_i) / ideal_DCG ) over test users

This is the metric Netflix's experimentation team uses in their published research on
observational causal inference and heterogeneous treatment effects. Including it in the
evaluation notebook and model dashboard is the signal that separates this portfolio project
from standard recommendation system implementations.

### Model Artifacts

The following files are produced by training and bundled into the API Docker image:

  ml/artifacts/user_tower.pt       PyTorch state dict for the User Tower
  ml/artifacts/item_tower.pt       PyTorch state dict for the Item Tower
  ml/artifacts/ranker.pt           PyTorch state dict for the MLP ranker
  ml/artifacts/faiss_index.bin     Serialized FAISS IndexFlatIP
  ml/artifacts/movie_id_map.json   FAISS position to database movie ID mapping
  ml/artifacts/genre_encoder.pkl   scikit-learn LabelEncoder for genre one-hot
  ml/artifacts/feature_scaler.pkl  StandardScaler for numeric item features
  ml/artifacts/eval_metrics.json   Final Recall@10, NDCG@10, IPS-NDCG@10 values

All artifacts are versioned by training run date in the filename during development and
the production versions are copied to the standard names above before Docker build.

---

## Database Schema

### PostgreSQL Tables

users
  id             uuid          primary key, default gen_random_uuid()
  email          varchar(255)  unique, not null
  password_hash  varchar(255)  not null
  created_at     timestamptz   default now()
  updated_at     timestamptz   default now()

movies
  id              integer       primary key (MovieLens movie ID)
  tmdb_id         integer       unique
  title           varchar(500)  not null
  overview        text
  poster_path     varchar(255)
  backdrop_path   varchar(255)
  release_year    smallint
  runtime_minutes smallint
  maturity_rating varchar(10)
  vote_average    numeric(3,1)
  genres          varchar(50)[] not null default '{}'
  popularity_score numeric(10,4)
  search_vector   tsvector      generated from title and overview, indexed with GIN

ratings
  id          uuid      primary key, default gen_random_uuid()
  user_id     uuid      not null, references users(id) on delete cascade
  movie_id    integer   not null, references movies(id) on delete cascade
  value       smallint  not null, check (value in (1, -1))
  created_at  timestamptz  default now()
  unique constraint on (user_id, movie_id)
  index on (user_id, created_at desc) for fast user rating history lookup

interactions
  id          uuid      primary key, default gen_random_uuid()
  user_id     uuid      not null, references users(id) on delete cascade
  movie_id    integer   not null, references movies(id)
  action      varchar(20)  not null, check (action in ('view', 'play', 'add_to_list'))
  created_at  timestamptz  default now()
  index on (user_id, created_at desc)

user_embeddings
  user_id      uuid      primary key, references users(id) on delete cascade
  embedding    float4[]  not null (128 elements, stored as PostgreSQL float array)
  computed_at  timestamptz  not null

### Redis Keys

rec:{user_id}    JSON string, array of up to 50 movie IDs in ranked order, TTL 15 minutes
emb:{user_id}    Base64-encoded numpy float32 array (128 dims), TTL 60 minutes

Cache invalidation: any new rating submission deletes rec:{user_id} immediately so the
next GET /recommendations triggers a fresh computation.

---

## Monorepo Structure

```
kino/
  apps/
    web/
      app/
        layout.tsx
        page.tsx
        globals.css
        (auth)/
          onboarding/
            page.tsx
        movie/
          [id]/
            page.tsx
        metrics/
          page.tsx
      components/
        layout/
          Navbar.tsx
        home/
          HeroBanner.tsx
          MovieCard.tsx
          ContentRow.tsx
        onboarding/
          RatingFlow.tsx
          SeedCard.tsx
        ui/
          SkeletonCard.tsx
          MetricCard.tsx
      lib/
        types.ts
        utils.ts
        tmdb.ts
        mock-data.ts
        api-client.ts
      hooks/
        useScrollPosition.ts
        useRecommendations.ts
        useRatings.ts
      tailwind.config.ts
      package.json
      next.config.ts
      tsconfig.json
      .env.example
    api/
      main.py
      requirements.txt
      Dockerfile
      .env.example
      app/
        routers/
          auth.py
          movies.py
          ratings.py
          recommendations.py
          metrics.py
        models/
          user.py
          movie.py
          rating.py
          interaction.py
          user_embedding.py
        ml/
          inference.py
          user_tower.py
          item_tower.py
          ranker.py
          faiss_store.py
          features.py
        db/
          session.py
          base.py
          migrations/
        cache/
          redis_client.py
        schemas/
          user.py
          movie.py
          rating.py
          recommendation.py
        core/
          config.py
          security.py
          lifespan.py
        artifacts/
          (model files bundled at build time)
  ml/
    notebooks/
      01_data_exploration.ipynb
      02_feature_engineering.ipynb
      03_two_tower_training.ipynb
      04_ranker_training.ipynb
      05_evaluation.ipynb
    src/
      data/
        loader.py
        features.py
        splitter.py
      models/
        user_tower.py
        item_tower.py
        two_tower.py
        ranker.py
      training/
        train_two_tower.py
        train_ranker.py
      evaluation/
        metrics.py
        ips_weighting.py
    artifacts/
      (generated after training)
    requirements.txt
  .github/
    workflows/
      web-ci.yml
      api-ci.yml
  docker-compose.yml
  .env.example
  README.md
```

---

## Deployment

### Railway

Three services run under one Railway project.

API service: Docker container built from apps/api/Dockerfile. Runs uvicorn with 2 workers
on port 8000. The ML model artifacts are copied into the image during the Docker build so
no external model storage is needed. Railway injects all environment variables as secrets.
Health check endpoint at GET /health returns 200 and the model load status.

PostgreSQL: Railway's managed PostgreSQL service. The DATABASE_URL environment variable
is injected automatically and consumed by SQLAlchemy's async engine.

Redis: Railway's managed Redis service. The REDIS_URL environment variable is injected
automatically and consumed by the redis.asyncio client.

Railway auto-deploys from the main branch when api-ci.yml passes. Rollback is done by
redeploying a previous Railway deployment snapshot.

### Frontend Service on Railway

The Next.js frontend runs as a separate Railway service within the same Railway project
as the API. Railway detects the Next.js app automatically via the nixpacks builder and
runs next build followed by next start on port 3000.

A Dockerfile is not required for the frontend since Railway's nixpacks builder handles
Next.js natively. The build command is set to `npm run build` and the start command is
`npm run start` in the Railway service settings.

Environment variables set in the Railway frontend service dashboard:
- TMDB_API_KEY: used server-side in Next.js route handlers for fetching movie metadata
- NEXT_PUBLIC_API_URL: the internal Railway API service URL, available to client components

Using Railway's internal networking, NEXT_PUBLIC_API_URL can point to the private Railway
hostname of the API service (e.g. kino-api.railway.internal) to avoid public internet
latency between the frontend and backend within the same Railway project.

### GitHub Actions

web-ci.yml
Triggers on push to main or pull request where apps/web/** changes.
Steps: checkout, setup Node 20, install dependencies, run tsc --noEmit, run eslint,
run next build. If all pass, triggers a Railway redeploy of the frontend service via
the Railway CLI using a scoped deploy token stored as a GitHub secret.

api-ci.yml
Triggers on push to main or pull request where apps/api/** or ml/** changes.
Steps: checkout, setup Python 3.11, install requirements, run pytest on apps/api/tests/,
run docker build to validate the Dockerfile compiles. If all pass, triggers a Railway
redeploy via the Railway CLI using a scoped deploy token stored as a GitHub secret.

### Environment Variables Reference

Frontend (apps/web/.env.local):
  TMDB_API_KEY             Free TMDB v3 API key from themoviedb.org/settings/api
  NEXT_PUBLIC_API_URL      Railway API service URL (e.g. https://kino-api.railway.app)
                           In production use the internal Railway hostname for lower latency

Backend (apps/api/.env):
  DATABASE_URL             PostgreSQL connection string (injected by Railway)
  REDIS_URL                Redis connection string (injected by Railway)
  SECRET_KEY               Random 64-character string for JWT signing
  ALGORITHM                HS256
  ACCESS_TOKEN_EXPIRE_DAYS 7

---

## Build Phases

### Phase 1: ML Pipeline

Goal: produce trained model artifacts from MovieLens 25M locally. No web app involved.

Steps:
1. Download MovieLens 25M and place in ml/data/
2. Write ml/src/data/loader.py to parse ratings.csv and movies.csv
3. Write ml/src/data/features.py for user and item feature construction
4. Write ml/src/data/splitter.py for timestamp-based train/val/test split
5. Write ml/src/models/user_tower.py and item_tower.py
6. Write ml/src/models/two_tower.py combining both towers with temperature scaling
7. Write ml/src/training/train_two_tower.py with in-batch negative sampling loop
8. Build FAISS index from trained item embeddings
9. Write ml/src/evaluation/metrics.py for Recall@K and NDCG@K
10. Write ml/src/evaluation/ips_weighting.py for IPS-weighted NDCG
11. Write ml/src/models/ranker.py and ml/src/training/train_ranker.py
12. Save all artifacts to ml/artifacts/
13. Document results in 05_evaluation.ipynb

Deliverable: trained artifacts folder, eval_metrics.json showing Recall@10 and NDCG@10.

### Phase 2: Backend API

Goal: running local FastAPI service that serves real recommendations from trained models.

Steps:
1. Set up apps/api/ with FastAPI, SQLAlchemy 2.0 async, Alembic for migrations
2. Write database models (users, movies, ratings, interactions, user_embeddings)
3. Implement Alembic migration for initial schema
4. Write core/security.py for password hashing and JWT generation
5. Implement auth router (register, login, me)
6. Write movie population script to load MovieLens + TMDB data into PostgreSQL
7. Implement movies router with pagination and full-text search
8. Implement ratings router with cache invalidation on submission
9. Write ml/inference.py: loads artifacts at startup, exposes embed_user() and retrieve()
10. Implement recommendations router using inference.py and Redis caching
11. Implement metrics router reading from eval_metrics.json
12. Write pytest tests for all routers
13. Write Dockerfile and test with docker-compose locally

Deliverable: docker-compose up brings up the API, PostgreSQL, and Redis locally with
real recommendations returned from GET /recommendations.

### Phase 3: Frontend

Goal: running Next.js app with Netflix UI that shows real personalized recommendations.

Steps:
1. Rename all TwinLens references in apps/web/ to Kino
2. Update mock-data.ts and tmdb.ts with Kino branding
3. Write lib/api-client.ts for typed fetch wrappers to all API endpoints
4. Write hooks/useRecommendations.ts to fetch and cache recommendations client-side
5. Write hooks/useRatings.ts to manage rating submission and optimistic UI updates
6. Build onboarding/RatingFlow.tsx with the seed movie grid and progress bar
7. Update MovieCard.tsx to call the ratings API on thumbs up/down interaction
8. Update page.tsx to fetch from API instead of mock data when authenticated
9. Add the /metrics page with MetricCard components showing model evaluation results
10. Wire up the recommendation refresh call after the onboarding flow completes
11. Test end-to-end: create account, onboard, rate movies, see personalized home screen

Deliverable: full local stack running with real-time recommendation updates on rating.

### Phase 4: Deployment and Polish

Goal: live public URL, clean GitHub repo, portfolio-ready README.

Steps:
1. Set up Railway project, add PostgreSQL and Redis services
2. Push API Docker image and verify it deploys with model artifacts bundled
3. Run Alembic migrations on the Railway PostgreSQL instance
4. Populate the movies table in production from the preprocessing script
5. Seed 5 demo accounts with pre-populated ratings across diverse genres
6. Add the frontend as a Railway service in the same project, configure environment variables
7. Verify internal Railway networking between frontend and API services
8. Set up GitHub Actions workflows for both services
9. Verify CI passes on both, verify auto-deploy works end-to-end
10. Write README.md with architecture diagram, demo GIF, setup instructions,
    explanation of two-tower model, FAISS retrieval, ranking layer, and IPS evaluation
11. Add model architecture diagram (simple ASCII or image) to README

Deliverable: public URL that works, GitHub repo that reads as a serious ML engineering
project to a recruiter or engineer reviewing it cold.

---

## Definition of Done

The project is complete when a recruiter or engineer can visit the deployed URL, create
an account, rate 10 movies in the onboarding flow, and receive personalized recommendations
on the home screen that visibly change as they rate more movies.

The GitHub repository must contain:
- Full ML training pipeline in ml/ with documented evaluation results
- Trained model artifacts bundled into the API Docker image
- Clean monorepo structure with no dead code or placeholder files
- Passing CI on both frontend (type check, lint, build) and backend (pytest, docker build)
- A README that explains the two-tower architecture, FAISS retrieval step, ranking layer,
  IPS-weighted causal evaluation metric, and how to run the project locally from scratch

The model dashboard page must show Recall@10, NDCG@10, and IPS-NDCG@10 computed on the
held-out test set so anyone reviewing the repo can see the model actually works.
