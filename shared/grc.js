/* GRC Wiki — behaviour.
   Five jobs: theme, the corpus drawer, the clause-map disclosure, the reading
   position, and search.

   No framework and no dependencies, because both builds run this same file.
   The static build boots it once on DOMContentLoaded; the Next.js build calls
   window.GRC.boot() again after each client-side navigation, so everything
   here is written to be torn down and re-bound safely. Every init is a no-op
   when its markup is absent, so one file serves every page type. */

(function () {
    "use strict";

    var $ = function (sel, root) { return (root || document).querySelector(sel); };
    var $$ = function (sel, root) {
        return Array.prototype.slice.call((root || document).querySelectorAll(sel));
    };

    /* Listeners bound to document or window survive a client-side navigation,
       so they are registered once and look their elements up when they fire.
       Anything bound to a page element is collected here and released on the
       next boot. */
    var teardown = [];
    var globalsBound = false;

    function release() {
        while (teardown.length) {
            try { teardown.pop()(); } catch (e) { /* element already gone */ }
        }
    }

    function on(target, type, handler, opts) {
        target.addEventListener(type, handler, opts);
        teardown.push(function () { target.removeEventListener(type, handler, opts); });
    }

    /* --- Theme ---------------------------------------------------------- */

    function currentTheme() {
        var set = document.documentElement.getAttribute("data-theme");
        if (set) { return set; }
        // Light is the default; dark is opt-in only, so an unset theme is light
        // regardless of the OS preference.
        return "light";
    }

    function initTheme() {
        var btn = $("[data-theme-toggle]");
        if (!btn) { return; }

        var label = $("[data-theme-label]", btn);

        function paint() {
            var mode = currentTheme();
            btn.setAttribute("aria-label", mode === "dark" ? "Switch to light mode" : "Switch to dark mode");
            if (label) { label.textContent = mode === "dark" ? "light" : "dark"; }
        }

        on(btn, "click", function () {
            var next = currentTheme() === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", next);
            try { localStorage.setItem("grc-theme", next); } catch (e) { /* private mode */ }
            paint();
        });

        paint();
    }

    /* --- Corpus drawer (below 1000px) ----------------------------------- */

    function setDrawer(open) {
        var rail = $("[data-drawer]");
        var btn = $("[data-drawer-btn]");
        var scrim = $("[data-drawer-scrim]");
        if (!rail || !btn) { return; }
        rail.setAttribute("data-open", open ? "true" : "false");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        if (scrim) { scrim.hidden = !open; }
    }

    function initDrawer() {
        var btn = $("[data-drawer-btn]");
        var rail = $("[data-drawer]");
        var scrim = $("[data-drawer-scrim]");
        if (!btn || !rail) { return; }
        setDrawer(false);
        on(btn, "click", function () {
            setDrawer(rail.getAttribute("data-open") !== "true");
        });
        if (scrim) { on(scrim, "click", function () { setDrawer(false); }); }
        on(document, "keydown", function (ev) {
            if (ev.key === "Escape" && rail.getAttribute("data-open") === "true") { setDrawer(false); }
        });
    }

    /* --- Clause map disclosure ------------------------------------------ */

    /* Above 1200px CSS unwraps the <details> with display:contents and hides
       the summary, so it has to stay open there. Below, it is a collapsed
       disclosure above the article. With JS off it stays open everywhere:
       long, but never broken. */
    function initDisclosure() {
        var details = $("[data-page-rail] > details");
        if (!details) { return; }

        var wide = window.matchMedia("(min-width: 1201px)");
        var touched = false;

        function sync() {
            if (wide.matches) {
                details.open = true;
            } else if (!touched) {
                details.open = false;
            }
        }

        on(details, "toggle", function () {
            if (!wide.matches) { touched = true; }
        });
        on(wide, "change", function () { touched = false; sync(); });
        sync();
    }

    /* --- Clause map ------------------------------------------------------ */

    function initContents() {
        var items = $$("[data-toc] li[data-for]").filter(function (li) {
            return li.getAttribute("data-for");
        });
        if (!items.length || !("IntersectionObserver" in window)) { return; }

        var headings = items
            .map(function (li) { return document.getElementById(li.getAttribute("data-for")); })
            .filter(Boolean);
        if (!headings.length) { return; }

        var seen = {};
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (en) { seen[en.target.id] = en.isIntersecting; });

            var active = null;
            for (var i = 0; i < headings.length; i++) {
                var h = headings[i];
                if (seen[h.id]) { active = h.id; break; }
                if (h.getBoundingClientRect().top < 120) { active = h.id; }
            }

            items.forEach(function (li) {
                li.setAttribute("data-active", li.getAttribute("data-for") === active ? "true" : "false");
            });
        }, { rootMargin: "-46px 0px -70% 0px", threshold: 0 });

        headings.forEach(function (h) { io.observe(h); });
        teardown.push(function () { io.disconnect(); });
    }

    /* --- Reading position ------------------------------------------------ */

    /* The meter shows live position, because that is what a progress bar is
       for and a page that opens at 19% just looks broken. What persists is the
       furthest you have reached, and it surfaces as the read-mark in the corpus
       rail rather than in the meter. Private-mode failures are silent — the
       meter still works, it just forgets. */

    var READ_KEY = "grc-read";
    var READ_DONE = 90;   // the pager and sources sit below the last prose
    var READ_CAP = 400;   // entries remembered, oldest dropped

    function readMap() {
        try {
            var raw = JSON.parse(localStorage.getItem(READ_KEY) || "{}");
            return (raw && typeof raw === "object") ? raw : {};
        } catch (e) {
            return {};
        }
    }

    function rememberRead(path, value) {
        try {
            var map = readMap();
            if ((map[path] || 0) >= value) { return; }
            map[path] = value;

            var keys = Object.keys(map);
            if (keys.length > READ_CAP) {
                delete map[keys[0]];
            }
            localStorage.setItem(READ_KEY, JSON.stringify(map));
        } catch (e) { /* private mode, or quota */ }
    }

    function headerHeight() {
        var raw = getComputedStyle(document.documentElement).getPropertyValue("--header-h");
        return parseFloat(raw) || 46;
    }

    function initProgress() {
        var bar = $("[data-progress]");
        var article = $("[data-article]");
        if (!bar || !article) { return; }

        var pct = $("[data-progress-pct]");
        var meter = bar.parentNode;
        var path = window.location.pathname;
        var best = Math.min(100, Math.max(0, readMap()[path] || 0));
        var written = best;

        function paint(value) {
            bar.style.width = value + "%";
            if (pct) { pct.textContent = value + "%"; }
            if (meter && meter.setAttribute) { meter.setAttribute("aria-valuenow", value); }
        }

        /* Live scroll position, 0 to 100.
         *
         * `from` is the scroll offset at which the article's first line sits
         * under the header; `to` is the offset at which its last line reaches
         * the bottom of the viewport. Both ends are asserted rather than left
         * to the arithmetic, so no layout quirk can strand the meter short of
         * 0 or 100. */
        function measure() {
            var doc = document.documentElement;
            var scrolled = window.pageYOffset || doc.scrollTop || 0;
            var box = article.getBoundingClientRect();
            var articleTop = box.top + scrolled;

            var from = articleTop - headerHeight();
            var to = articleTop + box.height - window.innerHeight;

            if (to <= from) { return 100; }                                    // fits on one screen
            if (scrolled + window.innerHeight >= doc.scrollHeight - 2) { return 100; }  // document bottom
            if (scrolled <= from) { return 0; }
            if (scrolled >= to) { return 100; }
            return Math.round(((scrolled - from) / (to - from)) * 100);
        }

        /* Computed synchronously. Gating this behind requestAnimationFrame
           strands the meter whenever rAF is throttled — a background tab, a
           busy main thread — and one rect read per scroll event costs nothing.
           The write is what is expensive, so that is what gets rationed. */
        function update() {
            var value = measure();
            paint(value);
            if (value > best) { best = value; }
            if (best - written >= 5 || (best >= READ_DONE && written < READ_DONE)) {
                written = best;
                rememberRead(path, best);
            }
        }

        function flush() {
            if (best > written) {
                written = best;
                rememberRead(path, best);
            }
        }

        on(window, "scroll", update, { passive: true });
        on(window, "resize", update);
        on(window, "pagehide", flush);
        on(document, "visibilitychange", function () {
            if (document.visibilityState === "hidden") { flush(); }
        });
        update();
    }

    /* An entry you have finished gets its clause number in the accent colour,
       in the corpus rail and anywhere else entries are listed. Quiet, and it
       reuses a mark the design already means something by. */
    function markRead() {
        var links = $$("[data-entry-link]");
        if (!links.length) { return; }

        var map = readMap();
        links.forEach(function (link) {
            var href = link.getAttribute("href") || "";
            var done = (map[href] || 0) >= READ_DONE;
            link.setAttribute("data-read", done ? "true" : "false");
            var flag = $("[data-read-flag]", link);
            if (flag) { flag.textContent = done ? " (read)" : ""; }
        });
    }

    /* --- Search --------------------------------------------------------- */

    var index = null;
    var loading = null;
    var results = [];
    var selected = 0;

    function base() {
        return document.documentElement.getAttribute("data-base") || "/";
    }

    function loadIndex() {
        if (index) { return Promise.resolve(index); }
        if (loading) { return loading; }
        loading = fetch(base() + "search-index.json")
            .then(function (r) { return r.json(); })
            .then(function (data) { index = data.records || data; return index; })
            .catch(function () { index = []; return index; });
        return loading;
    }

    function norm(s) { return String(s).toLowerCase().replace(/[^a-z0-9 ]+/g, " "); }

    function score(rec, terms) {
        var hay = norm(rec.t + " " + (rec.k || "") + " " + (rec.x || ""));
        var title = norm(rec.t);
        var total = 0;
        for (var i = 0; i < terms.length; i++) {
            var term = terms[i];
            if (hay.indexOf(term) === -1) { return 0; }
            total += 1;
            if (title.indexOf(term) === 0) { total += 4; }
            else if (title.indexOf(term) !== -1) { total += 2; }
            if (rec.d === 1) { total += 1; }
        }
        return total;
    }

    function escapeText(text) {
        var div = document.createElement("div");
        div.textContent = String(text);
        return div.innerHTML;
    }

    /* Wrap matches in sentinels the browser cannot interpret, escape the whole
       string through textContent, then swap the sentinels for real tags. Index
       text is authored copy, but it is escaped anyway. */
    var OPEN = "\u0001";
    var CLOSE = "\u0002";

    function mark(text, terms) {
        var out = String(text).replace(/[\u0001\u0002]/g, "");
        terms.forEach(function (term) {
            if (!term) { return; }
            var re = new RegExp("(" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
            out = out.replace(re, OPEN + "$1" + CLOSE);
        });
        return escapeText(out).split(OPEN).join("<mark>").split(CLOSE).join("</mark>");
    }

    function render(q) {
        var dialog = $("[data-finder]");
        if (!dialog) { return; }
        var list = $("[data-finder-results]", dialog);
        var empty = $("[data-finder-empty]", dialog);

        var terms = norm(q).split(/\s+/).filter(Boolean);
        list.innerHTML = "";
        results = [];

        if (!terms.length || !index) {
            empty.hidden = false;
            empty.textContent = terms.length
                ? "Loading the index…"
                : "Type to search entries, clauses and definitions.";
            return;
        }

        results = index
            .map(function (rec) { return { rec: rec, s: score(rec, terms) }; })
            .filter(function (r) { return r.s > 0; })
            .sort(function (a, b) { return b.s - a.s; })
            .slice(0, 12)
            .map(function (r) { return r.rec; });

        if (!results.length) {
            empty.hidden = false;
            empty.textContent = "Nothing for “" + q + "”. Try a framework name or a clause number.";
            return;
        }

        empty.hidden = true;
        selected = 0;

        results.forEach(function (rec, i) {
            var li = document.createElement("li");
            li.setAttribute("data-sel", i === 0 ? "true" : "false");
            li.innerHTML =
                '<a href="' + base() + encodeURI(rec.u) + '">' +
                '<span class="finder__ref">' + escapeText(rec.c) + "</span>" +
                '<span><span class="finder__title">' + mark(rec.t, terms) + "</span>" +
                (rec.x ? '<span class="finder__ctx">' + mark(rec.x, terms) + "</span>" : "") +
                "</span></a>";
            list.appendChild(li);
        });
    }

    function move(step) {
        var list = $("[data-finder-results]");
        if (!list || !results.length) { return; }
        var lis = $$("li", list);
        lis[selected].setAttribute("data-sel", "false");
        selected = (selected + step + lis.length) % lis.length;
        lis[selected].setAttribute("data-sel", "true");
        lis[selected].scrollIntoView({ block: "nearest" });
    }

    function openFinder(seed) {
        var dialog = $("[data-finder]");
        if (!dialog || typeof dialog.showModal !== "function") { return; }
        var input = $("[data-finder-input]", dialog);
        if (!dialog.open) { dialog.showModal(); }
        if (seed) { input.value = seed; }
        input.focus();
        input.select();
        render(input.value);
        loadIndex().then(function () { render(input.value); });
    }

    function initSearch() {
        var dialog = $("[data-finder]");
        if (!dialog || typeof dialog.showModal !== "function") { return; }

        var input = $("[data-finder-input]", dialog);

        $$("[data-finder-open]").forEach(function (el) {
            on(el, "click", function (ev) {
                ev.preventDefault();
                openFinder(el.getAttribute("data-seed") || "");
            });
        });

        on(input, "input", function () {
            loadIndex().then(function () { render(input.value); });
        });

        on(dialog, "keydown", function (ev) {
            if (ev.key === "ArrowDown") { ev.preventDefault(); move(1); }
            else if (ev.key === "ArrowUp") { ev.preventDefault(); move(-1); }
            else if (ev.key === "Enter") {
                var lis = $$("li", $("[data-finder-results]", dialog));
                if (lis[selected]) { ev.preventDefault(); $("a", lis[selected]).click(); }
            }
        });

        on(dialog, "click", function (ev) {
            if (ev.target === dialog) { dialog.close(); }
        });
    }

    /* --- A-Z index filters ---------------------------------------------- */

    /* The filters are declared on each row as a space-separated flag list.
       Checked boxes are ANDed: "has a worked example" and "revised recently"
       means both, which is what a reader assembling a reading list wants. */
    function initIndexFilters() {
        var host = $("[data-index]");
        var boxes = $$("[data-index-filter]");
        if (!host || !boxes.length) { return; }

        var rows = $$("li[data-flags]", host);
        var groups = $$(".idx__group", host);
        var count = $("[data-index-count]");
        var total = rows.length;

        function apply() {
            var want = boxes.filter(function (b) { return b.checked; })
                            .map(function (b) { return b.value; });
            var shown = 0;

            rows.forEach(function (row) {
                var flags = (row.getAttribute("data-flags") || "").split(" ");
                var ok = want.every(function (w) { return flags.indexOf(w) !== -1; });
                row.hidden = !ok;
                if (ok) { shown += 1; }
            });

            groups.forEach(function (group) {
                var any = $$("li[data-flags]", group).some(function (r) { return !r.hidden; });
                group.hidden = !any;
            });

            if (count) {
                count.textContent = "Showing " + shown + " of " + total;
            }
        }

        boxes.forEach(function (box) { on(box, "change", apply); });
        apply();
    }

    /* --- Global listeners, registered once ------------------------------ */

    function initGlobals() {
        if (globalsBound) { return; }
        globalsBound = true;

        document.addEventListener("keydown", function (ev) {
            if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === "k") {
                ev.preventDefault();
                openFinder();
                return;
            }
            if (ev.key === "Escape") {
                var rail = $("[data-drawer]");
                if (rail && rail.getAttribute("data-open") === "true") {
                    setDrawer(false);
                    var btn = $("[data-drawer-btn]");
                    if (btn) { btn.focus(); }
                }
                return;
            }
            if (ev.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) {
                ev.preventDefault();
                openFinder();
            }
        });

        document.addEventListener("click", function (ev) {
            var rail = $("[data-drawer]");
            var btn = $("[data-drawer-btn]");
            if (!rail || rail.getAttribute("data-open") !== "true") { return; }
            if (rail.contains(ev.target) || (btn && btn.contains(ev.target))) { return; }
            setDrawer(false);
        });

        window.addEventListener("pointerover", loadIndex, { once: true });
    }

    function boot() {
        release();
        initGlobals();
        initTheme();
        initDisclosure();
        initDrawer();
        initContents();
        initProgress();
        markRead();
        initIndexFilters();
        initSearch();
    }

    window.GRC = { boot: boot, open: openFinder, theme: currentTheme };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
