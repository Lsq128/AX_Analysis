import type { Metadata } from "next";
import { Fraunces, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

const sans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ibm-plex",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AX_Analysis",
  description: "AI 多 Agent 投研工作台",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={`${display.variable} ${sans.variable}`}>
      <body
        style={
          {
            ["--font-display" as string]: "var(--font-fraunces), 'Songti SC', serif",
            ["--font-sans" as string]:
              "var(--font-ibm-plex), 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
          } as React.CSSProperties
        }
      >
        {children}
      </body>
    </html>
  );
}
