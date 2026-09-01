import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { AuthProvider } from "@/components/providers/AuthProvider";


export const metadata: Metadata = {
  title: { default: "Zenglow", template: "%s | Zenglow" },
  description: "Discover and book appointments at top salons, spas, and wellness centres near you.",
  keywords: ["salon", "spa", "booking", "appointment", "beauty", "wellness"],
  openGraph: {
    type: "website",
    siteName: "Zenglow",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`font-sans antialiased`}>
        <QueryProvider>
          <AuthProvider>
            {children}
            <Toaster position="top-right" richColors />
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}

