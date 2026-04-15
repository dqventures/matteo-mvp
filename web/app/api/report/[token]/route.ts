import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

/* ------------------------------------------------------------------ */
/* Report PDF API — Validates token and serves the PDF inline          */
/* GET /api/report/abc123-def456-ghi789                                */
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

export async function GET(
  request: NextRequest,
  { params }: { params: { token: string } }
) {
  const tokens = loadTokens()
  const entry = tokens[params.token]

  // Invalid or missing token
  if (!entry) {
    return NextResponse.json({ error: 'Report not found' }, { status: 404 })
  }

  // Expired token
  if (new Date(entry.expires_at) < new Date()) {
    return NextResponse.json({ error: 'Report expired' }, { status: 410 })
  }

  // Serve the PDF file
  const pdfPath = path.join(process.cwd(), 'public', 'reports', entry.report_file)

  if (!fs.existsSync(pdfPath)) {
    return NextResponse.json({ error: 'Report file not found' }, { status: 404 })
  }

  const pdfBuffer = fs.readFileSync(pdfPath)

  return new NextResponse(pdfBuffer, {
    status: 200,
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': `inline; filename="${entry.report_file}"`,
      'Cache-Control': 'private, no-cache',
    },
  })
}
