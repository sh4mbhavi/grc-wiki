import type { Metadata } from "next";
import Script from "next/script";
import type { ReactNode } from "react";

import { Behaviour } from "@/components/Behaviour";
import { Colophon, Finder } from "@/components/Chrome";
import { href, site } from "@/lib/content";

import "@/styles/grc.css";

/* Applied before first paint so a stored preference never flashes the wrong
   theme. Deliberately not a React state: the value has to be on <html> before
   the first byte of CSS is applied. */
const THEME_BOOT =
    "try{var t=localStorage.getItem('grc-theme');" +
    "if(t){document.documentElement.setAttribute('data-theme',t)}}catch(e){}";

const FONTS =
    "https://fonts.googleapis.com/css2" +
    "?family=IBM+Plex+Mono:wght@400;500;600" +
    "&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400" +
    "&display=swap";

export const metadata: Metadata = {
    metadataBase: new URL(site.origin),
    title: { default: site.name, template: `%s — ${site.name}` },
    description: site.description,
    alternates: { canonical: "/" },
    openGraph: {
        type: "article",
        siteName: site.name,
        locale: site.locale.replace("-", "_"),
    },
    twitter: { card: "summary" },
};

export default function RootLayout({ children }: { children: ReactNode }) {
    return (
        <html lang={site.locale} data-base={site.base_path} suppressHydrationWarning>
            <head>
                <link rel="preconnect" href="https://fonts.googleapis.com" />
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
                <link rel="stylesheet" href={FONTS} />
                <meta name="theme-color" content="#f7f5f0" media="(prefers-color-scheme: light)" />
                <meta name="theme-color" content="#14130f" media="(prefers-color-scheme: dark)" />
                <script dangerouslySetInnerHTML={{ __html: THEME_BOOT }} />
            </head>
            <body>
                <a className="skip" href="#main">Skip to content</a>
                {children}
                <Colophon />
                <Finder />
                <Behaviour />
                <Script src={href("/assets/grc.js")} strategy="afterInteractive" />
            </body>
        </html>
    );
}
