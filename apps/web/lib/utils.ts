export function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ")
}

export function imageUrl(path: string | null, size = "w780") {
  if (!path) return null
  if (path.startsWith("http")) return path
  return `https://image.tmdb.org/t/p/${size}${path}`
}
