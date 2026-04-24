"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase";
import { AuthShowcase } from "@/components/AuthShowcase";

export default function SignupPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: fullName, company_name: companyName },
      },
    });

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    router.push("/dashboard");
  }

  const passwordStrength = password.length === 0 ? 0 : password.length < 8 ? 1 : password.length < 12 ? 2 : 3;

  return (
    <AuthShowcase mode="signup">
          <form onSubmit={handleSignup} className="space-y-3.5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label htmlFor="fullName" className="auth-label">Full name</label>
                <input
                  id="fullName"
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="auth-input"
                  placeholder="Jane"
                  autoComplete="name"
                />
              </div>

              <div>
                <label htmlFor="companyName" className="auth-label">
                  Company <span className="font-normal text-sky-100/65">(optional)</span>
                </label>
                <input
                  id="companyName"
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="auth-input"
                  placeholder="Smith Co."
                  autoComplete="organization"
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="auth-label">Email</label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="auth-input"
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <div>
              <label htmlFor="password" className="auth-label">Password</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="auth-input pr-16"
                  placeholder="8+ characters"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-gray-400 transition-colors hover:text-navy-800"
                  tabIndex={-1}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>

              {password.length > 0 && (
                <div className="mt-2 space-y-1.5">
                  <div className="flex gap-1">
                    {[1, 2, 3].map((level) => (
                      <div
                        key={level}
                        className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
                          passwordStrength >= level
                            ? level === 1 ? "bg-red-400" : level === 2 ? "bg-yellow-400" : "bg-green-500"
                            : "bg-gray-100"
                        }`}
                      />
                    ))}
                  </div>
                  <p className="text-xs font-semibold text-sky-100/65">
                    {passwordStrength === 1 ? "Weak - try a longer password" :
                     passwordStrength === 2 ? "Fair - add numbers or symbols" :
                     "Strong password"}
                  </p>
                </div>
              )}
            </div>

            {error && (
              <div className="rounded-xl border border-red-200/60 bg-red-50 px-4 py-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="auth-submit mt-1"
            >
              {loading ? "Creating account..." : "Create free account"}
            </button>

            <p className="text-center text-xs text-sky-100/65">
              By signing up you agree to our{" "}
              <span className="cursor-pointer font-semibold text-white hover:underline">Terms</span>{" "}
              and{" "}
              <span className="cursor-pointer font-semibold text-white hover:underline">Privacy Policy</span>
            </p>
          </form>

          <p className="mt-6 text-center text-sm text-sky-100/75">
            Already have an account?{" "}
            <Link href="/login" className="font-bold text-white hover:underline">
              Sign in
            </Link>
          </p>
    </AuthShowcase>
  );
}
