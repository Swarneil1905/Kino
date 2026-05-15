import { MetricCard } from "@/components/ui/MetricCard"

async function getMetrics() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
  try {
    const res = await fetch(`${apiUrl}/metrics`, { next: { revalidate: 3600 } })
    if (!res.ok) return null
    return res.json() as Promise<{
      recall_at_10: number
      ndcg_at_10: number
      ips_ndcg_at_10: number
      model_version: string
    }>
  } catch {
    return null
  }
}

export default async function MetricsPage() {
  const metrics = await getMetrics()

  return (
    <main className="min-h-screen bg-netflix-black px-4 py-24 sm:px-8 lg:px-14">
      <h1 className="mb-2 text-2xl font-semibold text-white">Model Performance</h1>
      <p className="mb-10 max-w-2xl text-netflix-text-muted">
        Offline evaluation on the held-out test split of MovieLens 25M. IPS-NDCG corrects for popularity bias using
        inverse propensity scores.
      </p>
      {metrics === null ? (
        <p className="text-netflix-text-muted">Model metrics unavailable.</p>
      ) : (
        <>
          <div className="grid max-w-2xl grid-cols-1 gap-6 sm:grid-cols-3">
            <MetricCard label="Recall@10" value={`${(metrics.recall_at_10 * 100).toFixed(1)}%`} description="Coverage of relevant items in top 10." />
            <MetricCard label="NDCG@10" value={`${(metrics.ndcg_at_10 * 100).toFixed(1)}%`} description="Ranking quality at position 10." />
            <MetricCard label="IPS-NDCG@10" value={`${(metrics.ips_ndcg_at_10 * 100).toFixed(1)}%`} description="Bias-corrected NDCG." />
          </div>
          <p className="mt-6 text-sm text-netflix-text-muted">Model version: {metrics.model_version}</p>
        </>
      )}
    </main>
  )
}
