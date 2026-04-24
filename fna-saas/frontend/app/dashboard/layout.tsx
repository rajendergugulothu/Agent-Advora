import { redirect } from "next/navigation";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { DashboardNav } from "@/components/DashboardNav";

async function getUser() {
  const cookieStore = await cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { getAll: () => cookieStore.getAll() } }
  );
  const { data: { user } } = await supabase.auth.getUser();
  return user;
}

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const user = await getUser();
  if (!user) redirect("/login");

  return (
    <div className="premium-shell min-h-screen flex text-gray-900">
      <DashboardNav userEmail={user.email ?? ""} />

      <main className="flex-1 min-w-0 flex flex-col">
        <div className="lg:hidden h-14 shrink-0" />

        <div className="flex-1 p-5 sm:p-6 lg:p-8 pb-24 lg:pb-8">
          <div className="mx-auto w-full max-w-7xl">
          {children}
          </div>
        </div>
      </main>
    </div>
  );
}
