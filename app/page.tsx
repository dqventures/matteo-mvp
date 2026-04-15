import Link from 'next/link'

/* ------------------------------------------------------------------ */
/* Metrica — Marketing Landing Page                                    */
/* Single-scroll B2B page for UK logistics decision-makers             */
/* ------------------------------------------------------------------ */

const CALENDLY_URL = 'https://calendly.com/metrica'

const NAV_LINKS = [
  { label: 'The Data', href: '#solution' },
  { label: 'What It Is', href: '#problem' },
  { label: 'When to Use', href: '#when' },
  { label: 'How It Works', href: '#process' },
  { label: 'About', href: '#about' },
]

/* ---- Reusable components ---- */

function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-navy/95 backdrop-blur-sm border-b border-white/10">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <span className="text-white text-xl font-bold tracking-tight">Metrica</span>
        <nav className="hidden md:flex items-center gap-6">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm text-gray-300 hover:text-white transition-colors"
            >
              {link.label}
            </a>
          ))}
          <a
            href={CALENDLY_URL}
            className="ml-2 px-4 py-2 bg-blue-500 text-white text-sm font-medium rounded-md hover:bg-blue-600 transition-colors"
          >
            Book a call
          </a>
        </nav>
      </div>
    </header>
  )
}

function Footer() {
  return (
    <footer className="bg-navy text-gray-400 py-12 border-t border-white/10">
      <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4">
        <span className="text-white font-bold text-lg">Metrica</span>
        <p className="text-sm">© 2026 Metrica Logistics Intelligence. All rights reserved.</p>
      </div>
    </footer>
  )
}

/* ---- Section components ---- */

function Hero() {
  return (
    <section className="bg-navy pt-32 pb-20 md:pb-28">
      <div className="max-w-6xl mx-auto px-6 grid md:grid-cols-2 gap-12 items-center">
        <div>
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white leading-tight mb-6">
            Reduce the risk of switching parcel carriers in your next UK tender.
          </h1>
          <p className="text-lg text-gray-300 mb-8 leading-relaxed">
            Independent, decision-specific performance evidence to help you decide
            whether to stay with Carrier&nbsp;A or switch to Carrier&nbsp;B — before you commit.
          </p>
          <a
            href={CALENDLY_URL}
            className="inline-block px-8 py-4 bg-blue-500 text-white font-semibold rounded-lg text-lg hover:bg-blue-600 transition-colors"
          >
            Book a call
          </a>
        </div>

        {/* Report mock-up card */}
        <div className="bg-white/5 border border-white/10 rounded-xl p-6 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <span className="text-white font-bold text-sm">Carrier Performance Analysis</span>
            <span className="text-gray-400 text-xs">Sample Report</span>
          </div>
          <div className="space-y-3">
            <div className="bg-white/10 rounded-lg p-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400">
                    <th className="text-left pb-2 font-medium">KPI</th>
                    <th className="text-right pb-2 font-medium">Carrier A</th>
                    <th className="text-right pb-2 font-medium">Carrier B</th>
                  </tr>
                </thead>
                <tbody className="text-white">
                  <tr><td className="py-1">On-Time (Overall)</td><td className="text-right font-mono">89.5%</td><td className="text-right font-mono">89.2%</td></tr>
                  <tr><td className="py-1">On-Time (Next Day)</td><td className="text-right font-mono">92.1%</td><td className="text-right font-mono">87.8%</td></tr>
                  <tr><td className="py-1">On-Time (Standard)</td><td className="text-right font-mono">88.4%</td><td className="text-right font-mono">90.1%</td></tr>
                  <tr><td className="py-1">Weekly Consistency</td><td className="text-right font-mono text-green-400">2.3%</td><td className="text-right font-mono text-amber-400">5.7%</td></tr>
                  <tr><td className="py-1">Peak Delta</td><td className="text-right font-mono text-green-400">-7.1pp</td><td className="text-right font-mono text-red-400">-13.2pp</td></tr>
                </tbody>
              </table>
            </div>
            <p className="text-xs text-gray-400 italic">
              &quot;Carrier A delivers more consistently. Carrier B outperforms on standard deliveries
              but carries higher peak risk.&quot;
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

function TrustBar() {
  const stats = [
    { value: '200+', label: 'Years Combined Experience' },
    { value: '100%', label: 'Founder-led' },
    { value: 'UK', label: 'Focused' },
    { value: '✓', label: 'Evidence-Based' },
  ]
  return (
    <section className="bg-gray-50 py-8 border-y border-gray-200">
      <div className="max-w-6xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-6">
        {stats.map((s) => (
          <div key={s.label} className="text-center">
            <div className="text-2xl font-bold text-navy">{s.value}</div>
            <div className="text-sm text-gray-500 mt-1">{s.label}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

function Problem() {
  const pains = [
    { title: 'Service SLAs not matched', icon: '⚠' },
    { title: 'OTIF and T+1 adjust and decline', icon: '📉' },
    { title: 'Increased customer service cost', icon: '💷' },
    { title: 'Increased WISMO & damage / loss frequency', icon: '📦' },
  ]
  return (
    <section id="problem" className="py-20 bg-white scroll-mt-16">
      <div className="max-w-4xl mx-auto px-6">
        <h2 className="text-3xl font-bold text-navy mb-6">
          Switching parcel carriers is a high-stakes decision.
        </h2>
        <p className="text-lg text-gray-600 mb-10 leading-relaxed">
          You are expected to commit based on carrier sales claims, anecdotal reference calls,
          and surface-level data. The real risk is not imperfect information — it&apos;s discovering
          too late that the new carrier underperforms in the geographies and services that matter
          most to your operation.
        </p>
        <div className="grid md:grid-cols-2 gap-4">
          {pains.map((p) => (
            <div
              key={p.title}
              className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200"
            >
              <span className="text-2xl">{p.icon}</span>
              <span className="text-gray-700 font-medium">{p.title}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Solution() {
  const pillars = [
    { title: 'Decision-specific', desc: 'Shaped around your actual switching question, not a generic benchmark.' },
    { title: 'Evidence-led', desc: 'Based on third-party shipment tracking data, not carrier self-reporting.' },
    { title: 'Practical, not philosophical', desc: 'Focused on what matters for your tender decision right now.' },
  ]
  return (
    <section id="solution" className="py-20 bg-gray-50 scroll-mt-16">
      <div className="max-w-4xl mx-auto px-6">
        <h2 className="text-3xl font-bold text-navy mb-6">
          We&apos;ll help you make an informed decision.
        </h2>
        <p className="text-lg text-gray-600 mb-8 leading-relaxed">
          This work helps you decide whether to stay with your current carrier or switch
          to an alternative in your next UK parcel tender. It pressure-tests carrier
          performance — with your specific question in mind.
        </p>

        <div className="bg-white border-l-4 border-blue-500 rounded-r-lg p-6 mb-10 shadow-sm">
          <p className="text-gray-500 text-sm mb-2 font-medium">Example question</p>
          <p className="text-navy text-lg italic font-medium">
            &quot;Will Carrier B actually perform acceptably for our specific parcel profile
            compared to Carrier A?&quot;
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {pillars.map((p) => (
            <div key={p.title} className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
              <h3 className="font-bold text-navy mb-2">{p.title}</h3>
              <p className="text-sm text-gray-600">{p.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function WhenToUse() {
  const triggers = [
    { title: 'An upcoming annual or half-yearly carrier tender' },
    { title: 'Pressure to reduce on-time-to-customer delivery rates' },
    { title: 'Dissatisfaction with current carrier performance' },
    { title: 'Leadership scrutiny of peak period carrier performance' },
  ]
  return (
    <section id="when" className="py-20 bg-white scroll-mt-16">
      <div className="max-w-4xl mx-auto px-6">
        <h2 className="text-3xl font-bold text-navy mb-4">
          When this is worth doing.
        </h2>
        <p className="text-lg text-gray-600 mb-10">
          This is most useful when a real switching decision is expected within approximately 90 days.
        </p>
        <div className="grid md:grid-cols-2 gap-4">
          {triggers.map((t, i) => (
            <div
              key={i}
              className="p-5 bg-blue-light border border-blue-100 rounded-lg flex items-start gap-3"
            >
              <span className="text-blue-500 font-bold text-lg">{i + 1}</span>
              <p className="text-gray-700 font-medium">{t.title}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Process() {
  const steps = [
    { num: '01', title: 'Discovery call', desc: 'We understand your switching question, carrier context, and timeline.' },
    { num: '02', title: 'Scope definition', desc: 'We agree the carriers, services, geographies, and time periods to analyse.' },
    { num: '03', title: 'Data analysis', desc: 'We source and analyse third-party shipment tracking data against your specific question.' },
    { num: '04', title: 'Report delivery', desc: 'You receive a clear, evidence-based comparison report to support your decision.' },
  ]
  return (
    <section id="process" className="py-20 bg-gray-50 scroll-mt-16">
      <div className="max-w-4xl mx-auto px-6">
        <h2 className="text-3xl font-bold text-navy mb-10">
          How the work is shaped.
        </h2>
        <div className="space-y-6">
          {steps.map((s) => (
            <div key={s.num} className="flex gap-6 items-start">
              <div className="flex-shrink-0 w-12 h-12 bg-navy text-white rounded-lg flex items-center justify-center font-bold text-sm">
                {s.num}
              </div>
              <div>
                <h3 className="font-bold text-navy text-lg">{s.title}</h3>
                <p className="text-gray-600 mt-1">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-10 p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
          <p className="text-gray-700 italic">
            &quot;Clarity, not optimism. At the end of the work, you should be able to say:
            &apos;We have enough evidence to switch — or enough evidence not to.&apos;&quot;
          </p>
        </div>
      </div>
    </section>
  )
}

function Positioning() {
  return (
    <section className="py-20 bg-white">
      <div className="max-w-5xl mx-auto px-6">
        <h2 className="text-3xl font-bold text-navy mb-10">
          Where other approaches break down.
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-navy text-white">
                <th className="text-left p-3 rounded-tl-lg">Approach</th>
                <th className="text-left p-3">Strength</th>
                <th className="text-left p-3">Limitation</th>
                <th className="text-left p-3 rounded-tr-lg">vs Metrica</th>
              </tr>
            </thead>
            <tbody className="text-gray-700">
              <tr className="bg-gray-50">
                <td className="p-3 font-medium">Carrier sales data</td>
                <td className="p-3">Free, readily available</td>
                <td className="p-3">Self-reported, cherry-picked metrics</td>
                <td className="p-3">Independent third-party data</td>
              </tr>
              <tr>
                <td className="p-3 font-medium">Reference calls</td>
                <td className="p-3">Real customer experience</td>
                <td className="p-3">Anecdotal, different parcel profile</td>
                <td className="p-3">Data-driven, specific to your profile</td>
              </tr>
              <tr className="bg-gray-50">
                <td className="p-3 font-medium">Broad pilots</td>
                <td className="p-3">Real performance data</td>
                <td className="p-3">Expensive, slow, disruptive</td>
                <td className="p-3">Evidence before commitment</td>
              </tr>
              <tr>
                <td className="p-3 font-medium">Management consultants</td>
                <td className="p-3">Strategic framing</td>
                <td className="p-3">Expensive, generic, slow</td>
                <td className="p-3 rounded-br-lg">Focused, fast, affordable</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

function About() {
  const credentials = [
    { title: '25+ years in logistics' },
    { title: 'Senior leadership at major carriers' },
    { title: 'Deep expertise in UK parcel market' },
  ]
  return (
    <section id="about" className="py-20 bg-gray-50 scroll-mt-16">
      <div className="max-w-4xl mx-auto px-6">
        <h2 className="text-3xl font-bold text-navy mb-10">About</h2>
        <div className="flex flex-col md:flex-row gap-8 items-start">
          {/* Photo placeholder */}
          <div className="flex-shrink-0 w-32 h-32 bg-gray-300 rounded-xl flex items-center justify-center text-gray-500 text-sm">
            Photo
          </div>
          <div>
            <h3 className="text-xl font-bold text-navy">Matteo Weindelmayer</h3>
            <p className="text-gray-500 mb-4">Founder, Metrica Logistics Intelligence</p>
            <p className="text-gray-600 leading-relaxed mb-6">
              This work is led by Matteo Weindelmayer, an independent consultant who helps
              companies pressure-test high-stakes logistics decisions.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {credentials.map((c) => (
                <div
                  key={c.title}
                  className="p-3 bg-white rounded-lg border border-gray-200 text-center"
                >
                  <p className="text-sm font-medium text-navy">{c.title}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function FinalCTA() {
  return (
    <section className="py-20 bg-navy">
      <div className="max-w-3xl mx-auto px-6 text-center">
        <h2 className="text-2xl md:text-3xl font-bold text-white mb-6 leading-tight">
          If you are a Head of Logistics facing a real carrier switching decision,
          this work can help you pressure-test it before committing.
        </h2>
        <a
          href={CALENDLY_URL}
          className="inline-block px-8 py-4 bg-blue-500 text-white font-semibold rounded-lg text-lg hover:bg-blue-600 transition-colors"
        >
          Book a call
        </a>
      </div>
    </section>
  )
}

/* ---- Page ---- */

export default function HomePage() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <TrustBar />
        <Problem />
        <Solution />
        <WhenToUse />
        <Process />
        <Positioning />
        <About />
        <FinalCTA />
      </main>
      <Footer />
    </>
  )
}
