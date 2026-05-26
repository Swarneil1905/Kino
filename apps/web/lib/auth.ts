import type { NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"

const API_URL = process.env.API_URL ?? "http://localhost:8000"

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId:     process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],

  callbacks: {
    async jwt({ token, account }) {
      // On first sign-in, exchange the Google ID token for a Kino JWT
      if (account?.id_token) {
        try {
          const res = await fetch(`${API_URL}/auth/google`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ id_token: account.id_token }),
          })
          if (res.ok) {
            const data = await res.json()
            token.kinoToken  = data.access_token
            token.kinoUserId = data.user_id
          }
        } catch {
          // Keep token without kino credentials — will show error on protected routes
        }
      }
      return token
    },

    async session({ session, token }) {
      session.kinoToken  = token.kinoToken  as string | undefined
      session.kinoUserId = token.kinoUserId as string | undefined
      return session
    },
  },

  pages: {
    signIn: "/login",
  },

  secret: process.env.NEXTAUTH_SECRET,
}
