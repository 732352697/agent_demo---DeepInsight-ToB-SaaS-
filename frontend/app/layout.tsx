import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DeepInsight 2.0 - AI 直播助手",
  description: "下一代 AI 直播策划与执行平台",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
