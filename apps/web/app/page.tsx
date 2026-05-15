import { HomeClient } from "@/components/home/HomeClient"
import { fetchHomeData } from "@/lib/tmdb"

export default async function Page() {
  const { featured, fallbackRows } = await fetchHomeData()
  return <HomeClient featured={featured} fallbackRows={fallbackRows} />
}
