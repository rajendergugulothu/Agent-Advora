import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy Policy" };

export default function PrivacyPage() {
  return (
    <main className="max-w-3xl mx-auto px-6 py-16 text-gray-800">
      <h1 className="text-3xl font-bold mb-2">Privacy Policy</h1>
      <p className="text-sm text-gray-500 mb-10">Last updated: April 28, 2026</p>

      <section className="space-y-8 text-sm leading-7">
        <div>
          <h2 className="text-lg font-semibold mb-2">1. Introduction</h2>
          <p>
            Advora (&quot;we&quot;, &quot;our&quot;, or &quot;us&quot;) operates an automated Instagram content
            platform for financial advisors. This Privacy Policy explains how we collect, use,
            and protect your information when you use our service.
          </p>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">2. Information We Collect</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>Account information: name, email address</li>
            <li>Instagram account data: username, profile picture, access tokens (encrypted)</li>
            <li>Facebook Page data: page ID used to publish content</li>
            <li>WhatsApp number (optional, for draft notifications)</li>
            <li>Post preferences: posting schedule, timezone, audience, themes</li>
            <li>Instagram analytics: impressions, reach, likes, comments, shares, saves</li>
          </ul>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">3. How We Use Your Information</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>To generate and publish Instagram content on your behalf</li>
            <li>To send you post drafts via WhatsApp for approval</li>
            <li>To display analytics from your Instagram account</li>
            <li>To schedule and automate your posting calendar</li>
            <li>To improve our AI-generated content quality</li>
          </ul>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">4. Third-Party Services</h2>
          <p>We use the following third-party services:</p>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>Meta (Facebook/Instagram)</strong> — to publish posts and read analytics via the Instagram Graph API</li>
            <li><strong>OpenAI</strong> — to generate post captions and images</li>
            <li><strong>Cloudinary</strong> — to store and serve generated images</li>
            <li><strong>WhatsApp Cloud API</strong> — to deliver draft notifications</li>
            <li><strong>Supabase</strong> — for secure database storage and authentication</li>
          </ul>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">5. Data Security</h2>
          <p>
            All Instagram access tokens are encrypted at rest using AES-256 encryption.
            We never store your Instagram or Facebook password. Access tokens are only used
            to perform actions you have explicitly authorized.
          </p>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">6. Data Retention</h2>
          <p>
            We retain your data for as long as your account is active. You may disconnect
            your Instagram account or delete your account at any time, which will remove
            your stored tokens and connection data.
          </p>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">7. Your Rights</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>Access the data we hold about you</li>
            <li>Request deletion of your data</li>
            <li>Disconnect your Instagram account at any time from the dashboard</li>
            <li>Revoke app permissions from your Facebook settings at any time</li>
          </ul>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">8. Contact Us</h2>
          <p>
            If you have questions about this Privacy Policy, contact us at:{" "}
            <a href="mailto:rajendernaik80@gmail.com" className="text-blue-600 underline">
              rajendernaik80@gmail.com
            </a>
          </p>
        </div>
      </section>
    </main>
  );
}
