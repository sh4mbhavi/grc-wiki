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

const FONTS = "https://cdn.jsdelivr.net/npm/@fontsource-variable/hubot-sans/index.css";

export const metadata: Metadata = {
    metadataBase: new URL(site.origin),
    title: { default: site.name, template: `%s - ${site.name}` },
    description: site.description,
    alternates: { canonical: "/" },
    icons: {
        icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
        apple: [{ url: "/favicon.svg" }],
    },
    openGraph: {
        type: "article",
        siteName: site.name,
        locale: site.locale.replace("-", "_"),
        images: [{ url: "/assets/logo.svg", width: 148, height: 34 }],
    },
    twitter: { card: "summary", images: ["/assets/logo.svg"] },
};

export default function RootLayout({ children }: { children: ReactNode }) {
    return (
        <html lang={site.locale} data-base={site.base_path} suppressHydrationWarning>
            <head>
                <link rel="preconnect" href="https://cdn.jsdelivr.net" crossOrigin="" />
                <link rel="stylesheet" href={FONTS} />
                <meta name="theme-color" content="#f1f2f3" />
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
