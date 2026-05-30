"use client"

import { useEffect } from "react"
import { useImpressionClick } from "@/hooks/useImpressionClick"

export function ImpressionTracker({ movieId }: { movieId: number }) {
  const recordClick = useImpressionClick()
  useEffect(() => {
    recordClick(movieId)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [movieId])
  return null
}
