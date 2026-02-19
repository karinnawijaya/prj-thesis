import "./globals.css";
import "./styles/shared.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ArtWeave",
  description: "ArtWeave: compare artworks with concise summaries.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="app-body">
        {children}
      </body>
    </html>
  );
}