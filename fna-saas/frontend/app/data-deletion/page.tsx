import type { Metadata } from "next";

export const metadata: Metadata = { title: "Data Deletion" };

export default function DataDeletionPage() {
  return (
    <main className="max-w-3xl mx-auto px-6 py-16 text-gray-800">
      <h1 className="text-3xl font-bold mb-2">Data Deletion Request</h1>
      <p className="text-sm text-gray-500 mb-10">Last updated: April 28, 2026</p>

      <section className="space-y-6 text-sm leading-7">
        <p>
          If you would like to delete your data from Advora, you have two options:
        </p>

        <div>
          <h2 className="text-lg font-semibold mb-2">Option 1 — From the Dashboard</h2>
          <p>
            Log in to your Advora account → go to <strong>Settings</strong> →
            disconnect your Instagram account. This removes all stored tokens and connection data immediately.
          </p>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">Option 2 — Email Request</h2>
          <p>
            Send an email to{" "}
            <a href="mailto:rajendernaik80@gmail.com" className="text-blue-600 underline">
              rajendernaik80@gmail.com
            </a>{" "}
            with the subject <strong>&quot;Data Deletion Request&quot;</strong> and include your
            registered email address. We will delete all your data within 30 days and confirm via email.
          </p>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">What gets deleted</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>Your account profile and preferences</li>
            <li>Your Instagram access tokens</li>
            <li>Your generated post drafts and analytics</li>
            <li>Your WhatsApp number</li>
          </ul>
        </div>
      </section>
    </main>
  );
}
