import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Metrica Logistics Intelligence',
  description: 'Independent, decision-specific carrier performance evidence for UK retailers.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
