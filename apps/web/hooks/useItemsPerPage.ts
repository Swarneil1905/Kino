"use client"

import { useEffect, useState } from "react"

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
