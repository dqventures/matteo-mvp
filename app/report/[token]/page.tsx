import { notFound } from 'next/navigation'
import fs from 'fs'
import path from 'path'
import PrintButton from './PrintButton'

/* ------------------------------------------------------------------ */
/* Report Portal — Authenticated PDF Viewer                            */
/* Token-based access: /report/abc123-def456-ghi789                    */
/* ------------------------------------------------------------------ */

interface TokenEntry {
  customer_name: string
  report_file: string
  created_at: string
  expires_at: string
}

interface TokenMap {
  [token: string]: TokenEntry
}

function loadTokens(): TokenMap {
  const tokensPath = path.join(process.cwd(), 'data', 'tokens.json')
  const data = fs.readFileSync(tokensPath, 'utf-8')
  return JSON.parse(data) as TokenMap
}

function isExpired(expiresAt: string): boolean {
  return new Date(expiresAt) < new Date()
}

export default function ReportPage({
  params,
}: {
  params: { token: string }
}) {
  const tokens = loadTokens()
  const entry = tokens[params.token]

  // Invalid token
  if (!entry) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center p-8">
          <div className="text-6xl mb-4">🔒</div>
          <h1 className="text-2xl font-bold text-navy mb-4">Report not found</h1>
          <p className="text-gray-600 mb-6">
            This report link is invalid or has expired. Please contact Metrica
            if you believe this is an error.
          </p>
          <a
            href="/"
            className="inline-block px-6 py-3 bg-navy text-white rounded-lg font-medium hover:bg-navy-light transition-colors"
          >
            Go to homepage
          </a>
        </div>
      </div>
    )
  }

  // Expired token
  if (isExpired(entry.expires_at)) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center p-8">
          <div className="text-6xl mb-4">⏰</div>
          <h1 className="text-2xl font-bold text-navy mb-4">Report expired</h1>
          <p className="text-gray-600 mb-6">
            This report link expired on {entry.expires_at}. Please contact Metrica
            to request a new link.
          </p>
          <a
            href="/"
            className="inline-block px-6 py-3 bg-navy text-white rounded-lg font-medium hover:bg-navy-light transition-colors"
          >
            Go to homepage
          </a>
        </div>
      </div>
    )
  }

  // Valid token — show report viewer
  const pdfUrl = `/api/report/${params.token}`

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Header */}
      <header className="bg-navy text-white py-4 px-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-xl font-bold tracking-tight">Metrica</span>
          <span className="text-gray-400">|</span>
          <div>
            <span className="text-sm text-gray-300">{entry.customer_name}</span>
            <span className="text-gray-500 text-xs ml-3">{entry.created_at}</span>
          </div>
        </div>
        <PrintButton />
      </header>

      {/* PDF Viewer */}
      <div className="flex-1 p-4">
        <iframe
          src={pdfUrl}
          className="w-full h-full min-h-[80vh] rounded-lg shadow-lg border border-gray-200 bg-white"
          title="Report PDF"
        />
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4 px-6 text-center">
        <p className="text-sm text-gray-500">
          This report is confidential and prepared exclusively for{' '}
          <strong>{entry.customer_name}</strong>.
        </p>
      </footer>
    </div>
  )
}
