import type { Metadata, Viewport } from "next";
import { Navbar } from "@/components/common/Navbar";
import { Footer } from "@/components/common/Footer";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "CareerShield AI — Verify Opportunities. Protect Futures.",
  description:
    "AI-Powered Job Opportunity Verification & Career-Risk Analysis Platform for Indian Students and Freshers.",
  keywords: [
    "job verification",
    "recruitment fraud detection",
    "career shield",
    "fake job scam analyzer",
    "fresher job safety",
    "explainable AI",
  ],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="flex min-h-screen flex-col bg-navy-950 font-sans text-slate-100 antialiased selection:bg-shield-cyan/30 selection:text-shield-brightCyan">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
