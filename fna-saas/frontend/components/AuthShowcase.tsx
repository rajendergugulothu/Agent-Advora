import { Logo } from "@/components/Logo";

interface AuthShowcaseProps {
  children: React.ReactNode;
  mode: "login" | "signup";
}

export function AuthShowcase({ children, mode }: AuthShowcaseProps) {
  return (
    <main className="auth-page min-h-screen overflow-hidden px-4 py-8 text-white sm:px-6">
      <div className="auth-stage mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl items-center justify-center">
        <div className="absolute left-6 top-6 z-20 sm:left-10 sm:top-8">
          <div className="flex items-center gap-3">
            <Logo size="sm" variant="icon" />
            <div>
              <p className="text-lg font-black leading-none tracking-tight text-white">Advora</p>
              <p className="mt-1 text-[10px] font-bold uppercase tracking-[0.18em] text-cyan-100">Your Voice</p>
            </div>
          </div>
        </div>

        <div aria-hidden="true" className="auth-scene pointer-events-none absolute inset-0">
          <div className="content-card content-card-main">
            <div className="flex items-center justify-between">
              <span className="rounded-full bg-white/14 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-cyan-100">
                Instagram post
              </span>
              <span className="text-[10px] font-semibold text-white/60">9:00 AM</span>
            </div>
            <div className="mt-4 aspect-square rounded-2xl bg-[linear-gradient(135deg,#7c3aed,#06b6d4_54%,#f97316)] p-4 shadow-2xl shadow-cyan-950/30">
              <div className="h-full rounded-xl border border-white/20 bg-white/12 p-4 backdrop-blur-sm">
                <p className="text-xs font-semibold uppercase tracking-wide text-white/70">Market Monday</p>
                <p className="mt-8 text-2xl font-black leading-tight">Small habits compound into big confidence.</p>
              </div>
            </div>
          </div>

          <div className="content-card content-card-caption">
            <p className="text-[10px] font-bold uppercase tracking-wide text-cyan-100">AI caption draft</p>
            <div className="mt-3 space-y-2">
              <span className="block h-2 rounded-full bg-white/70" />
              <span className="block h-2 w-10/12 rounded-full bg-cyan-100/70" />
              <span className="block h-2 w-7/12 rounded-full bg-orange-100/70" />
            </div>
            <p className="mt-4 text-xs font-semibold text-white/70">#financialadvisor #wealthplanning</p>
          </div>

          <div className="content-card content-card-reel">
            <div className="h-28 rounded-2xl bg-[linear-gradient(160deg,#0ea5e9,#8b5cf6_58%,#ec4899)] p-3">
              <div className="h-full rounded-xl border border-white/20 bg-black/12" />
            </div>
            <p className="mt-3 text-xs font-bold text-white">Reel idea ready</p>
          </div>

          <div className="schedule-chip schedule-chip-top">Auto publish</div>
          <div className="schedule-chip schedule-chip-bottom">Compliance-aware tone</div>
          <div className="auth-ribbon auth-ribbon-left" />
          <div className="auth-ribbon auth-ribbon-right" />
          <div className="auth-wave auth-wave-one" />
          <div className="auth-wave auth-wave-two" />
          <div className="auth-wave auth-wave-three" />
        </div>

        <section className="auth-panel relative z-10 w-full max-w-[25.25rem] px-5 py-6 sm:px-7 sm:py-7">
          <div className="mb-6 text-center">
            <div className="mx-auto mb-3 flex h-[3.25rem] w-[3.25rem] items-center justify-center rounded-2xl border border-white/[0.18] bg-white/[0.14] shadow-2xl shadow-cyan-950/20 backdrop-blur">
              <Logo size="sm" variant="icon" />
            </div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-cyan-100">Advora</p>
            <h1 className="mt-2 text-[1.65rem] font-black leading-tight tracking-tight text-white">
              {mode === "login" ? "Welcome back" : "Create your account"}
            </h1>
            <p className="mx-auto mt-2 max-w-xs text-sm leading-5 text-sky-100/78">
              {mode === "login"
                ? "Sign in to manage your Instagram content engine."
                : "Start generating Instagram content for your advisory brand."}
            </p>
          </div>

          {children}
        </section>
      </div>
    </main>
  );
}
