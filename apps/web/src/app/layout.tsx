import type { Metadata, Viewport } from "next";
import { Inter, Fraunces, JetBrains_Mono } from "next/font/google";
import { Toaster } from "sonner";
import { ServiceWorkerRegistrar } from "@/components/brand/ServiceWorker";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-display",
  axes: ["opsz"],
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: {
    default: "DAMAY — Paluwagan, naka-record sa Stellar.",
    template: "%s · DAMAY",
  },
  description:
    "Paluwagan rotating-savings circles for Filipinos. Contributions and reputation verifiable on Stellar. Members stay on WhatsApp.",
  applicationName: "DAMAY",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "DAMAY",
  },
  icons: {
    icon: "/favicon.ico",
    apple: "/icon-192.png",
  },
  openGraph: {
    title: "DAMAY — Paluwagan, naka-record sa Stellar.",
    description:
      "A trustless protocol for Filipino informal financial behaviors. Built for the Stellar Philippines Hackathon.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#C2410C",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${fraunces.variable} ${jetbrains.variable}`}
    >
      <body className="min-h-screen bg-bg-base text-fg-base">
        {children}
        <Toaster
          position="top-right"
          theme="light"
          richColors
          toastOptions={{
            classNames: {
              toast: "border border-border-subtle bg-bg-raised text-fg-base shadow-md rounded-md",
            },
          }}
        />
        <ServiceWorkerRegistrar />
      </body>
    </html>
  );
}
