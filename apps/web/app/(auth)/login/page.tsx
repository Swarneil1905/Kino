"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { FormEvent, useState } from "react"

import { api, ApiError } from "@/lib/api-client"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const data = await api.auth.login(email, password)
      localStorage.setItem("kino_token", data.access_token)
      localStorage.setItem("kino_user_id", data.user_id)
      localStorage.setItem("kino_email", email)
      router.push("/")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-netflix-black px-4">
      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-6 rounded bg-netflix-card/80 p-10">
        <h1 className="text-3xl font-black text-netflix-red">Kino</h1>
        <p className="text-netflix-text-muted">Sign in to get personalized recommendations.</p>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded bg-[#333] px-4 py-3 text-white outline-none focus:ring-2 focus:ring-netflix-red"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded bg-[#333] px-4 py-3 text-white outline-none focus:ring-2 focus:ring-netflix-red"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded bg-netflix-red py-3 font-semibold text-white transition hover:bg-red-700 disabled:opacity-50"
        >
          {loading ? "Signing in..." : "Sign In"}
        </button>
        <p className="text-sm text-netflix-text-muted">
          New to Kino?{" "}
          <Link href="/register" className="text-white hover:underline">
            Create an account
          </Link>
        </p>
      </form>
    </main>
  )
}
