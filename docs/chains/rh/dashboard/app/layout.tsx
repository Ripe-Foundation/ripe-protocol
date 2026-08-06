import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://ripe-robinhood-status.mickhagen.chatgpt.site"),
  title: "Ripe × Robinhood — Private Program Status",
  description:
    "Private Robinhood program status. The engineering foundation is integrated; nothing is deployed or active.",
  openGraph: {
    title: "Ripe × Robinhood — Private Program Status",
    description:
      "Foundation integrated. Nothing is deployed or active. See the exact current authority boundary and critical path.",
    type: "website",
    images: [
      {
        url: "/og.png",
        width: 1200,
        height: 630,
        alt: "Abstract private program status graphic for Ripe and Robinhood",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Ripe × Robinhood — Private Program Status",
    description:
      "Foundation integrated. Nothing is deployed or active.",
    images: ["/og.png"],
  },
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
