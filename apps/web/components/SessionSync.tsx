"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export function SessionSync() {
  const { data: session } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (session?.kinoToken && session?.kinoUserId) {
      const isNewLogin = !localStorage.getItem("kino_token")
      localStorage.setItem("kino_token", session.kinoToken)
      localStorage.setItem("kino_user_id", session.kinoUserId)
      if (session.user?.email) {
        localStorage.setItem("kino_email", session.user.email)
      }
      if (isNewLogin) {
        window.dispatchEvent(new Event("kino:signin"))
        if (!localStorage.getItem("kino_onboarded")) {
          router.push("/onboarding")
        }
      }
    }
  }, [session, router])

  return null
}
