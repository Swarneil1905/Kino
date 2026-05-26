import "next-auth"
import "next-auth/jwt"

declare module "next-auth" {
  interface Session {
    kinoToken?:  string
    kinoUserId?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    kinoToken?:  string
    kinoUserId?: string
  }
}
