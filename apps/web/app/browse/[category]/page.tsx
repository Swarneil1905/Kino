import { notFound } from "next/navigation"
import { BrowseClient } from "@/components/browse/BrowseClient"
import { CATEGORY_CONFIG } from "@/lib/browse-config"

type PageProps = { params: Promise<{ category: string }> }

export function generateStaticParams() {
  return Object.keys(CATEGORY_CONFIG).map((category) => ({ category }))
}

export default async function BrowsePage({ params }: PageProps) {
  const { category } = await params
  const config = CATEGORY_CONFIG[category]
  if (!config) notFound()

  return <BrowseClient category={category} label={config.label} genres={config.genres} />
}
