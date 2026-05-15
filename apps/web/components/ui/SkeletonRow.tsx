import { SkeletonCard } from "./SkeletonCard"

type SkeletonRowProps = {
  title?: string
  count?: number
}

export function SkeletonRow({ title, count = 6 }: SkeletonRowProps) {
  return (
    <section className="px-5 py-8 md:px-14">
      {title ? (
        <h2 className="mb-3 text-xl font-bold">{title}</h2>
      ) : (
        <div className="mb-3 h-5 w-40 animate-pulse rounded bg-netflix-card" aria-hidden />
      )}
      <div className="flex gap-3">
        {Array.from({ length: count }).map((_, index) => (
          <SkeletonCard key={index} />
        ))}
      </div>
    </section>
  )
}
