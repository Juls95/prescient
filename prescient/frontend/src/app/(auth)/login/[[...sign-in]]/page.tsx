import { SignIn } from "@clerk/nextjs";

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-[#fafafa] flex items-center justify-center px-4">
      <SignIn
        appearance={{
          elements: {
            rootBox: "mx-auto",
            card: "rounded-2xl border border-[#e5e5e5] shadow-sm",
            headerTitle: "text-[#0a0a0a] font-bold tracking-tight",
            headerSubtitle: "text-[#666]",
            formButtonPrimary: "bg-[#0a0a0a] hover:opacity-85 transition",
            footerActionLink: "text-[#7c3aed] hover:text-[#6d28d9]",
          },
        }}
      />
    </div>
  );
}
