import { Metadata } from "next";
import { RegisterForm } from "@/components/auth/register-form";

export const metadata: Metadata = {
  title: "Register Account | Nyaya-ZTA Judicial Platform",
  description: "Create an account on the Nyaya-ZTA Zero Trust Judicial Platform",
};

export default function RegisterPage() {
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
        <RegisterForm />
      </div>
    </main>
  );
}
