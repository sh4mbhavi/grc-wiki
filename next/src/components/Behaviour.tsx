"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

declare global {
    interface Window {
        GRC?: { boot: () => void };
    }
}

/* The interactive layer lives in shared/grc.js, which the static build loads
 * too. It is attribute-driven and safe to re-bind, so the only thing this app
 * has to add is a re-boot after a client-side navigation replaces the DOM.
 * Two renderers, one behaviour implementation. */
export function Behaviour() {
    const pathname = usePathname();

    useEffect(() => {
        let cancelled = false;

        const boot = () => {
            if (!cancelled) {
                window.GRC?.boot();
            }
        };

        if (window.GRC) {
            boot();
        } else {
            // The script tag is afterInteractive; on a first paint it may not
            // have run yet. One frame is enough, and boot() is idempotent.
            const id = window.setTimeout(boot, 60);
            return () => {
                cancelled = true;
                window.clearTimeout(id);
            };
        }

        return () => {
            cancelled = true;
        };
    }, [pathname]);

    return null;
}
