import type { Metadata } from "next";
import { Inter } from "next/font/google"; // Using Inter for now, component has its own fonts
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Bug Exorcist",
    description: "Autonomous AI debugger",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={inter.className}>{children}</body>
        </html>
    );
}
