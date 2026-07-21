import { Metadata } from "next";
import { LoginForm } from "@/components/auth/login-form";

export const metadata: Metadata = {
  title: "Login | Nyaya-ZTA Judicial Platform",
  description: "Sign in to the Nyaya-ZTA Zero Trust Explainable AI Judicial Platform",
};

export default function LoginPage() {
  return (
    <main className="relative flex min-h-screen items-center justify-center p-6 overflow-hidden">
      {/* Background Grid & Radial Gradient */}
      <div className="fixed inset-0 hero-grid pointer-events-none" />
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at 50% -20%, rgba(99, 102, 241, 0.15) 0%, transparent 60%)",
        }}
      />

      <div className="relative z-10 animate-slide-up">
        <LoginForm />
      </div>
    </main>
  );
}
