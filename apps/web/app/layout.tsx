import type { Metadata } from "next"
import { Inter } from "next/font/google"

import { Navbar } from "@/components/layout/Navbar"
import "./globals.css"

const inter = Inter({ subsets: ["latin"], display: "swap" })

export const metadata: Metadata = {
  title: "Kino",
  description: "A neural movie recommendation experience.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Navbar />
        {children}
      </body>
    </html>
  )
}
