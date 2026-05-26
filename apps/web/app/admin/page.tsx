"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api, ApiError, type AdminUserRecord } from "@/lib/api-client"

type AdminUser = AdminUserRecord

function formatDate(iso: string | null) {
  if (!iso) return "never"
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export default function AdminPage() {
  const router = useRouter()
  const [users, setUsers] = useState<AdminUser[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.admin
      .users()
      .then((data) => setUsers(data))
      .catch((err) => {
        if (err instanceof ApiError && err.status === 403) {
          router.replace("/")
        } else if (err instanceof ApiError && err.status === 401) {
          router.replace("/login")
        } else {
          setError(err instanceof ApiError ? err.message : "Failed to load users")
        }
      })
      .finally(() => setLoading(false))
  }, [router])

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-netflix-black">
        <p className="text-netflix-text-muted">Loading...</p>
      </main>
    )
  }

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-netflix-black">
        <p className="text-red-400">{error}</p>
      </main>
    )
  }

  const totalRatings = users.reduce((sum, u) => sum + u.rating_count, 0)
  const googleUsers = users.filter((u) => u.auth_provider === "google").length
  const emailUsers = users.filter((u) => u.auth_provider === "email").length

  return (
    <main className="min-h-screen bg-netflix-black px-6 py-10 text-white">
      <div className="mx-auto max-w-6xl space-y-8">
        <div>
          <h1 className="text-3xl font-black text-netflix-red">Admin</h1>
          <p className="mt-1 text-sm text-netflix-text-muted">Registered users and activity</p>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Total users" value={users.length} />
          <StatCard label="Google sign-in" value={googleUsers} />
          <StatCard label="Email sign-in" value={emailUsers} />
          <StatCard label="Total ratings" value={totalRatings} />
        </div>

        {/* Users table */}
        <div className="overflow-x-auto rounded bg-netflix-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-700 text-left text-xs uppercase tracking-wide text-zinc-500">
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Provider</th>
                <th className="px-4 py-3">Ratings</th>
                <th className="px-4 py-3">Last login</th>
                <th className="px-4 py-3">Joined</th>
                <th className="px-4 py-3">Admin</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-zinc-800 hover:bg-zinc-800/40">
                  <td className="px-4 py-3 font-medium">{user.email}</td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        user.auth_provider === "google"
                          ? "rounded px-2 py-0.5 text-xs bg-blue-900/60 text-blue-300"
                          : "rounded px-2 py-0.5 text-xs bg-zinc-700 text-zinc-300"
                      }
                    >
                      {user.auth_provider}
                    </span>
                  </td>
                  <td className="px-4 py-3 tabular-nums text-zinc-300">{user.rating_count}</td>
                  <td className="px-4 py-3 text-zinc-400">{formatDate(user.last_login_at)}</td>
                  <td className="px-4 py-3 text-zinc-400">{formatDate(user.created_at)}</td>
                  <td className="px-4 py-3">
                    {user.is_admin ? (
                      <span className="rounded px-2 py-0.5 text-xs bg-netflix-red/20 text-netflix-red">yes</span>
                    ) : (
                      <span className="text-zinc-600">--</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {users.length === 0 && (
            <p className="px-4 py-8 text-center text-zinc-500">No users found.</p>
          )}
        </div>
      </div>
    </main>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded bg-netflix-card px-5 py-4">
      <p className="text-xs uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="mt-1 text-2xl font-bold tabular-nums">{value.toLocaleString()}</p>
    </div>
  )
}
