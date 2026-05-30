type MetricCardProps = {
  label: string
  value: string | number
  description: string
}

export function MetricCard({ label, value, description }: MetricCardProps) {
  return (
    <div className="rounded bg-[var(--surface)] p-5">
      <div className="mb-2 text-sm text-kino-muted">{label}</div>
      <div className="mb-3 text-3xl font-black">{value}</div>
      <p className="text-sm leading-relaxed text-white/70">{description}</p>
    </div>
  )
}
