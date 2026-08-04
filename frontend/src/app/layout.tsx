import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Personal Task Manager Agent',
  description: 'AI-Powered Task Management with Google Calendar Integration & Daily Planning Agent',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-background text-gray-100 min-h-screen font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
