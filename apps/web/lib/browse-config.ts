export const CATEGORY_CONFIG: Record<string, { label: string; genres: string[] }> = {
  movies:        { label: "Movies",        genres: ["Action", "Drama", "Comedy", "Thriller", "Romance", "Crime", "Mystery", "Adventure", "Fantasy", "Horror", "Western", "War", "Musical"] },
  series:        { label: "Series",        genres: ["Drama", "Crime", "Mystery", "Thriller", "Adventure"] },
  documentaries: { label: "Documentaries", genres: ["Documentary"] },
  anime:         { label: "Anime",         genres: ["Animation"] },
  sports:        { label: "Sports",        genres: ["Action", "Adventure"] },
}
