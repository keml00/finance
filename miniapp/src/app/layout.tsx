import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinAI Assistant",
  description: "AI-powered personal finance manager",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className="dark">
      <head>
        <script src="https://telegram.org/js/telegram-web-app.js" />
      </head>
      <body className="bg-dark-950 text-white min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
