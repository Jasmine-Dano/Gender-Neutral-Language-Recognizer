"""Polished, dependency-free Tkinter UI for the DFA language recognizer.

All files are processed locally. No cloud calls or accounts are involved.
"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
import os

from dfa_engine import TermDFA
from document_reader import extract_text
from reporting import csv_report, plain_report, summarize, word_count
from terms import GENDER_TERMS


# Cohesive dark desktop palette.
COL = {
    "canvas": "#090F1D",
    "sidebar": "#0D1728",
    "surface": "#131F34",
    "surface2": "#192940",
    "surface3": "#223650",
    "border": "#293B56",
    "text": "#F2F6FF",
    "muted": "#9FB2CC",
    "subtle": "#7086A5",
    "accent": "#40D9B6",
    "accent_ink": "#08271F",
    "purple": "#A09CFF",
    "warn": "#FFC479",
    "good": "#59DDB8",
}

FONT = "Segoe UI"
MONO = "Consolas"
PREVIEW_LIMIT = 60000


def txt(parent, value, *, size=11, color=None, weight="normal", bg=None,
        wraplength=0, anchor="w", **kwargs):
    return tk.Label(
        parent, text=value, font=(FONT, size, weight), fg=color or COL["text"],
        bg=bg or parent.cget("bg"), anchor=anchor, justify="left",
        wraplength=wraplength, **kwargs,
    )


def btn(parent, title, action, *, kind="primary", size=10, width=None):
    variants = {
        "primary": (COL["accent"], COL["accent_ink"], "#78F3D4"),
        "secondary": (COL["surface3"], COL["text"], "#304763"),
        "outline": (COL["surface"], COL["muted"], COL["surface3"]),
        "nav": (COL["sidebar"], COL["muted"], COL["surface3"]),
    }
    background, foreground, hovered = variants[kind]
    control = tk.Button(
        parent, text=title, command=action, font=(FONT, size, "bold"),
        fg=foreground, bg=background, activeforeground=foreground,
        activebackground=hovered, cursor="hand2", relief="flat", bd=0,
        highlightthickness=0, padx=18, pady=11, width=width,
    )
    control.bind("<Enter>", lambda _event: control.configure(bg=hovered)
                 if control["state"] == "normal" else None)
    control.bind("<Leave>", lambda _event: control.configure(bg=background)
                 if control["state"] == "normal" else None)
    return control


def panel(parent, *, bg=None, padding=18):
    outer = tk.Frame(parent, bg=bg or COL["surface"],
                     highlightbackground=COL["border"], highlightthickness=1, bd=0)
    inner = tk.Frame(outer, bg=bg or COL["surface"])
    inner.pack(fill="both", expand=True, padx=padding, pady=padding)
    return outer, inner


class NeutralLensApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NeutralLens — Gender-Neutral Language Recognizer")
        self.geometry("1270x840")
        self.minsize(990, 680)
        self.configure(bg=COL["canvas"])

        self.dfa = TermDFA(GENDER_TERMS)
        self.source_path: Path | None = None
        self.source_text = ""
        self.findings = None
        self.active_page = "Overview"
        self.nav_controls = {}
        self.preview_text = None
        self.row_terms = {}

        self._configure_table_theme()
        self._layout_shell()
        self.render()

    def _configure_table_theme(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(
            "Neutral.Treeview", background=COL["surface"],
            fieldbackground=COL["surface"], foreground=COL["text"],
            borderwidth=0, relief="flat", rowheight=35,
            font=(FONT, 10),
        )
        style.configure(
            "Neutral.Treeview.Heading", background=COL["surface2"],
            foreground=COL["muted"], font=(FONT, 9, "bold"),
            borderwidth=0, relief="flat", padding=9,
        )
        style.map(
            "Neutral.Treeview", background=[("selected", "#26584D")],
            foreground=[("selected", "#F2FFFA")],
        )
        style.map(
            "Neutral.Treeview.Heading", background=[("active", COL["surface3"])],
        )
        style.configure("Neutral.Vertical.TScrollbar", background=COL["surface3"],
                        troughcolor=COL["surface"], borderwidth=0,
                        arrowcolor=COL["muted"])

    def _layout_shell(self):
        # Sidebar.
        self.sidebar = tk.Frame(self, bg=COL["sidebar"], width=246)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=COL["sidebar"])
        brand.pack(fill="x", padx=21, pady=(29, 24))
        logo = tk.Canvas(brand, bg=COL["sidebar"], width=41, height=45,
                         bd=0, highlightthickness=0)
        logo.pack(side="left", padx=(0, 11))
        logo.create_oval(5, 5, 37, 37, fill=COL["accent"], outline="")
        logo.create_line(12, 22, 18, 22, 22, 14, 26, 29, 31, 22,
                         fill=COL["accent_ink"], width=3, smooth=True)
        brandtext = tk.Frame(brand, bg=COL["sidebar"])
        brandtext.pack(side="left")
        txt(brandtext, "NeutralLens", size=15, weight="bold").pack(anchor="w")
        txt(brandtext, "LANGUAGE INTELLIGENCE", size=7, color=COL["subtle"]).pack(anchor="w")

        tk.Frame(self.sidebar, bg=COL["border"], height=1).pack(
            fill="x", padx=20, pady=(0, 23))
        txt(self.sidebar, "WORKSPACE", size=9, weight="bold", color=COL["subtle"]).pack(
            anchor="w", padx=27, pady=(0, 12))

        nav = [
            ("Overview", "▦"),
            ("Findings", "≡"),
            ("Report", "▤"),
            ("About the DFA", "◇"),
        ]
        for name, symbol in nav:
            holder = tk.Frame(self.sidebar, bg=COL["sidebar"])
            holder.pack(fill="x", padx=13, pady=3)
            item = tk.Button(
                holder, text=f"  {symbol}    {name}", anchor="w", padx=9, pady=12,
                font=(FONT, 11, "bold"), relief="flat", bd=0,
                fg=COL["muted"], bg=COL["sidebar"],
                activebackground=COL["surface2"], activeforeground=COL["accent"],
                cursor="hand2", command=lambda n=name: self.switch_page(n),
            )
            item.pack(fill="x")
            self.nav_controls[name] = item

        footer = tk.Frame(self.sidebar, bg=COL["sidebar"])
        footer.pack(side="bottom", fill="x", padx=20, pady=(8, 23))
        box = tk.Frame(footer, bg=COL["surface"], padx=13, pady=13)
        box.pack(fill="x")
        txt(box, "●  OFFLINE & PRIVATE", size=9, weight="bold",
            color=COL["accent"]).pack(anchor="w")
        txt(box, "Files are analyzed on your PC.\nNo account or API required.",
            size=9, color=COL["muted"]).pack(anchor="w", pady=(6, 0))
        txt(footer, "AUTOMATA THEORY  /  STUDENT PROJECT", size=7,
            color=COL["subtle"]).pack(anchor="w", pady=(16, 0))

        # Main area.
        self.main = tk.Frame(self, bg=COL["canvas"])
        self.main.pack(side="left", fill="both", expand=True)
        top = tk.Frame(self.main, bg=COL["canvas"], height=67)
        top.pack(side="top", fill="x", padx=34)
        top.pack_propagate(False)
        txt(top, "ACADEMIC PROJECT   /   FINITE STATE AUTOMATA", size=9,
            color=COL["subtle"], weight="bold").pack(side="left", pady=23)
        pill = tk.Frame(top, bg=COL["surface2"], padx=12, pady=7)
        pill.pack(side="right", pady=14)
        txt(pill, "●  DFA ENGINE ACTIVE", size=9, color=COL["accent"],
            weight="bold").pack()
        tk.Frame(self.main, height=1, bg=COL["border"]).pack(fill="x")

        area = tk.Frame(self.main, bg=COL["canvas"])
        area.pack(fill="both", expand=True)
        self.scroll = tk.Canvas(area, bg=COL["canvas"], bd=0, highlightthickness=0)
        self.scroll.pack(side="left", fill="both", expand=True)
        self.bar = ttk.Scrollbar(area, orient="vertical", command=self.scroll.yview,
                                 style="Neutral.Vertical.TScrollbar")
        self.bar.pack(side="right", fill="y")
        self.scroll.configure(yscrollcommand=self.bar.set)
        self.content = tk.Frame(self.scroll, bg=COL["canvas"])
        self.window_id = self.scroll.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", self._update_scroll)
        self.scroll.bind("<Configure>", self._resize_content)
        self.bind_all("<MouseWheel>", self._mouse_wheel)

    def _update_scroll(self, _event=None):
        self.scroll.configure(scrollregion=self.scroll.bbox("all"))

    def _resize_content(self, event):
        self.scroll.itemconfigure(self.window_id, width=event.width)

    def _mouse_wheel(self, event):
        # Text controls should retain their own scroll handling.
        if isinstance(event.widget, (tk.Text, ttk.Treeview)):
            return
        self.scroll.yview_scroll(int(-event.delta / 120), "units")

    def switch_page(self, page):
        self.active_page = page
        self.render()

    def render(self):
        for child in self.content.winfo_children():
            child.destroy()
        self.preview_text = None
        self.row_terms = {}
        for page, button in self.nav_controls.items():
            active = page == self.active_page
            button.configure(
                bg=COL["surface2"] if active else COL["sidebar"],
                fg=COL["accent"] if active else COL["muted"],
            )
        self.body = tk.Frame(self.content, bg=COL["canvas"])
        self.body.pack(fill="both", expand=True, padx=34, pady=(28, 44))

        pages = {
            "Overview": self._overview,
            "Findings": self._findings,
            "Report": self._report,
            "About the DFA": self._about,
        }
        pages[self.active_page]()
        self.after_idle(lambda: self.scroll.yview_moveto(0))

    def _page_heading(self, heading, desc, right_action=None):
        header = tk.Frame(self.body, bg=COL["canvas"])
        header.pack(fill="x", pady=(0, 24))
        left = tk.Frame(header, bg=COL["canvas"])
        left.pack(side="left", fill="x", expand=True)
        txt(left, heading, size=25, weight="bold").pack(anchor="w")
        txt(left, desc, size=11, color=COL["muted"]).pack(anchor="w", pady=(7, 0))
        if right_action:
            right_action(header).pack(side="right", padx=(10, 0))

    def _section_head(self, parent, title, note=""):
        line = tk.Frame(parent, bg=COL["canvas"])
        line.pack(fill="x", pady=(22, 13))
        txt(line, title, size=13, weight="bold").pack(side="left")
        if note:
            txt(line, note, size=9, color=COL["subtle"]).pack(side="right")

    def _overview(self):
        self._page_heading(
            "Inclusive writing starts here.",
            "Scan your documents, identify gendered terms, and discover thoughtful alternatives.",
        )

        hero = tk.Frame(self.body, bg=COL["surface2"],
                        highlightbackground=COL["border"], highlightthickness=1,
                        height=208)
        hero.pack(fill="x")
        hero.pack_propagate(False)
        tk.Frame(hero, bg=COL["accent"], width=5).pack(side="left", fill="y")
        copy = tk.Frame(hero, bg=COL["surface2"])
        copy.pack(side="left", padx=(26, 6), pady=21, fill="both", expand=True)
        txt(copy, "INTELLIGENT TEXT SCANNING", size=9, weight="bold",
            color=COL["accent"]).pack(anchor="w")
        txt(copy, "Small words. Bigger impact.", size=21, weight="bold").pack(
            anchor="w", pady=(7, 3))
        txt(copy, "Powered by a deterministic finite automaton —\n"
            "not a black-box AI model.", size=10, color=COL["muted"]).pack(anchor="w")
        row = tk.Frame(copy, bg=COL["surface2"])
        row.pack(anchor="w", pady=(16, 0))
        btn(row, "Browse document   →", self.choose_file).pack(side="left")
        btn(row, "Try sample", self.load_sample, kind="secondary").pack(
            side="left", padx=(10, 0))

        art = tk.Canvas(hero, width=235, bg=COL["surface2"],
                        bd=0, highlightthickness=0)
        art.pack(side="right", fill="y", padx=(0, 22))
        self._hero_illustration(art)

        self._section_head(self.body, "Your document", "TXT   •   DOCX   •   PDF")
        upload, inside = panel(self.body, padding=16)
        upload.pack(fill="x")
        icon = tk.Canvas(inside, bg=COL["surface2"], width=49, height=50,
                         highlightthickness=0)
        icon.pack(side="left", padx=(0, 14))
        icon.create_rectangle(15, 10, 35, 40, fill="", outline=COL["accent"], width=2)
        icon.create_line(19, 19, 31, 19, fill=COL["accent"], width=2)
        icon.create_line(19, 25, 31, 25, fill=COL["accent"], width=2)
        icon.create_line(19, 31, 28, 31, fill=COL["accent"], width=2)
        name_frame = tk.Frame(inside, bg=COL["surface"])
        name_frame.pack(side="left", fill="x", expand=True)
        if self.source_path:
            txt(name_frame, self.source_path.name, size=11, weight="bold").pack(anchor="w")
            try:
                size_kb = self.source_path.stat().st_size / 1024
                meta = f"{self.source_path.suffix.upper()[1:]} DOCUMENT    ·    {size_kb:,.1f} KB"
            except OSError:
                meta = "SELECTED DOCUMENT"
            txt(name_frame, meta, size=9, color=COL["muted"]).pack(anchor="w", pady=(4, 0))
        else:
            txt(name_frame, "No document selected", size=11, weight="bold").pack(anchor="w")
            txt(name_frame, "Choose a document to begin your analysis.", size=9,
                color=COL["muted"]).pack(anchor="w", pady=(4, 0))
        go = btn(inside, "Analyze now  ↗", self.analyze)
        go.pack(side="right")
        if not self.source_path:
            go.configure(state="disabled", bg=COL["surface3"], fg=COL["subtle"])

        self._section_head(self.body, "At a glance", "LIVE ANALYSIS SUMMARY")
        stats = tk.Frame(self.body, bg=COL["canvas"])
        stats.pack(fill="x")
        stats_values = [
            (str(len(self.findings)) if self.findings is not None else "—", "Occurrences", COL["accent"]),
            (str(len(summarize(self.findings))) if self.findings is not None else "—", "Unique terms", COL["purple"]),
            (f"{word_count(self.source_text):,}" if self.findings is not None else "—", "Words scanned", COL["text"]),
            (str(self.dfa.state_count), "DFA states", COL["warn"]),
        ]
        for col, (value, title, color) in enumerate(stats_values):
            stats.grid_columnconfigure(col, weight=1, uniform="stat")
            card, c = panel(stats, padding=15)
            card.grid(row=0, column=col, sticky="nsew", padx=(0, 12) if col < 3 else 0)
            txt(c, value, size=23, weight="bold", color=color).pack(anchor="w")
            txt(c, title, size=10, color=COL["muted"]).pack(anchor="w", pady=(4, 0))

        self._section_head(self.body, "Recognition results", "PREDEFINED VOCABULARY SCAN")
        if self.findings is None:
            self._empty_panel(self.body, "A clearer picture is one scan away.",
                              "Select your document and press Analyze now to see your results.")
        elif not self.findings:
            self._clear_panel(self.body)
        else:
            resultbox, content = panel(self.body, padding=17)
            resultbox.pack(fill="x")
            txt(content, f"{len(self.findings)} occurrences detected in your document",
                size=12, weight="bold", color=COL["accent"]).pack(anchor="w")
            txt(content, "Review suggested alternatives below. All changes are optional and context-dependent.",
                size=10, color=COL["muted"]).pack(anchor="w", pady=(5, 14))
            self._summary_table(content, height=6)
            btn(content, "See all findings  →", lambda: self.switch_page("Findings"),
                kind="secondary").pack(anchor="e", pady=(12, 0))

    def _hero_illustration(self, canvas):
        canvas.create_oval(23, 24, 215, 213, outline="#2E5770", width=2)
        canvas.create_oval(49, 50, 187, 185, outline="#376475", width=1)
        canvas.create_oval(71, 75, 164, 162, outline="#3B666C", width=1)
        canvas.create_line(48, 123, 94, 97, 139, 136, 184, 91,
                           fill=COL["accent"], width=3, smooth=True)
        for x, y, n in ((48, 123, "q0"), (94, 97, "q1"),
                        (139, 136, "q2"), (184, 91, "q3")):
            canvas.create_oval(x-16, y-16, x+16, y+16,
                               fill=COL["accent"] if n == "q3" else COL["surface3"],
                               outline=COL["accent"], width=2)
            canvas.create_text(x, y, text=n, fill=COL["accent_ink"] if n == "q3"
                               else COL["text"], font=(MONO, 9, "bold"))
        canvas.create_text(118, 197, text="FINITE  ·  DETERMINISTIC", fill=COL["subtle"],
                           font=(FONT, 8, "bold"))

    def _empty_panel(self, parent, heading, info):
        item, inner = panel(parent, padding=33)
        item.pack(fill="x")
        txt(inner, "◌", size=30, color=COL["subtle"], anchor="center").pack()
        txt(inner, heading, size=14, weight="bold", anchor="center").pack(pady=(2, 7))
        txt(inner, info, size=10, color=COL["muted"], anchor="center").pack()

    def _clear_panel(self, parent):
        item, inner = panel(parent, padding=26)
        item.pack(fill="x")
        txt(inner, "✓  No predefined gender-specific terms were detected.", size=15,
            weight="bold", color=COL["accent"]).pack(anchor="w")
        txt(inner, "No terms in the predefined vocabulary were found. This does not guarantee "
            "every sentence is contextually gender-neutral.", size=10,
            color=COL["muted"], wraplength=680).pack(anchor="w", pady=(9, 0))

    def _summary_table(self, parent, *, height=8):
        region = tk.Frame(parent, bg=COL["surface"])
        region.pack(fill="x")
        cols = ("term", "count", "suggest", "lines")
        table = ttk.Treeview(region, columns=cols, show="headings",
                             style="Neutral.Treeview", height=height)
        specs = [
            ("term", "DETECTED TERM", 155),
            ("count", "COUNT", 70),
            ("suggest", "SUGGESTED ALTERNATIVE", 290),
            ("lines", "LINE(S)", 150),
        ]
        for key, heading, width in specs:
            table.heading(key, text=heading)
            table.column(key, width=width, anchor="center" if key == "count" else "w",
                         stretch=key in ("suggest", "lines"))
        for row in summarize(self.findings or []):
            table.insert("", "end", values=(row["term"], row["count"],
                                             row["suggestion"],
                                             ", ".join(map(str, row["lines"]))))
        bar = ttk.Scrollbar(region, orient="vertical", command=table.yview,
                            style="Neutral.Vertical.TScrollbar")
        table.configure(yscrollcommand=bar.set)
        table.pack(side="left", fill="x", expand=True)
        bar.pack(side="right", fill="y")
        table.bind("<<TreeviewSelect>>", lambda e: self._table_select(table))
        return table

    def _table_select(self, table):
        if self.preview_text is None or not table.selection():
            return
        term = table.item(table.selection()[0], "values")[0]
        match = next((m for m in self.findings if m.term == term), None)
        if match and match.start < PREVIEW_LIMIT:
            self.preview_text.see(f"1.0+{match.start}c")
            self.preview_text.tag_remove("selected_hit", "1.0", "end")
            self.preview_text.tag_add("selected_hit", f"1.0+{match.start}c",
                                      f"1.0+{match.end}c")

    def _findings(self):
        self._page_heading(
            "Detection details",
            "Review every recognized term and its location in the original document.",
            right_action=lambda p: btn(p, "Export CSV  ↗", self.export_csv, kind="secondary"),
        )
        if self.findings is None:
            self._empty_panel(self.body, "No results to review yet.",
                              "Run a document scan from the Overview page first.")
            btn(self.body, "Go to Overview  →", lambda: self.switch_page("Overview")).pack(
                anchor="w", pady=20)
            return
        if not self.findings:
            self._clear_panel(self.body)
        else:
            left, inside = panel(self.body)
            left.pack(fill="x")
            txt(inside, "TERM SUMMARY", size=9, weight="bold",
                color=COL["accent"]).pack(anchor="w", pady=(0, 12))
            self._summary_table(inside, height=min(11, max(5, len(summarize(self.findings)))))

        self._section_head(self.body, "Document preview", "HIGHLIGHTED MATCHES")
        preview_panel, inner = panel(self.body, padding=15)
        preview_panel.pack(fill="both", expand=True)
        txt(inner, (self.source_path.name if self.source_path else "Document"),
            size=10, weight="bold").pack(anchor="w", pady=(0, 10))
        textbox = tk.Frame(inner, bg=COL["surface2"])
        textbox.pack(fill="both", expand=True)
        view = tk.Text(textbox, height=17, wrap="word", bg=COL["surface2"],
                       fg=COL["text"], insertbackground=COL["text"],
                       font=(MONO, 10), relief="flat", bd=0, padx=16, pady=16,
                       selectbackground="#35635D")
        sb = ttk.Scrollbar(textbox, command=view.yview,
                           style="Neutral.Vertical.TScrollbar")
        view.configure(yscrollcommand=sb.set)
        view.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.preview_text = view
        view.insert("1.0", self.source_text[:PREVIEW_LIMIT])
        view.tag_configure("detected", background="#645033", foreground="#FFF0C5")
        view.tag_configure("selected_hit", background=COL["accent"],
                            foreground=COL["accent_ink"])
        for match in self.findings:
            if match.end <= PREVIEW_LIMIT:
                view.tag_add("detected", f"1.0+{match.start}c", f"1.0+{match.end}c")
        view.configure(state="disabled")
        if len(self.source_text) > PREVIEW_LIMIT:
            txt(inner, f"Preview limited to the first {PREVIEW_LIMIT:,} characters; "
                "the full document was analyzed.", size=9,
                color=COL["warn"]).pack(anchor="w", pady=(9, 0))
        txt(inner, "Highlighted text is detected by the DFA. Click a term in the table "
            "to jump to its first occurrence.", size=9,
            color=COL["muted"]).pack(anchor="w", pady=(9, 0))

    def _report(self):
        self._page_heading(
            "Analysis report",
            "Save a clear, shareable summary of your document's language patterns.",
        )
        controls = tk.Frame(self.body, bg=COL["canvas"])
        controls.pack(anchor="w", pady=(0, 18))
        btn(controls, "Save TXT report  ↓", self.export_txt).pack(side="left")
        btn(controls, "Export CSV  ↗", self.export_csv, kind="secondary").pack(
            side="left", padx=(10, 0))
        btn(controls, "Copy report", self.copy_report, kind="outline").pack(
            side="left", padx=(10, 0))
        board, inner = panel(self.body, padding=14)
        board.pack(fill="both", expand=True)
        frame = tk.Frame(inner, bg=COL["surface"])
        frame.pack(fill="both", expand=True)
        report = tk.Text(frame, bg=COL["surface"], fg=COL["text"],
                         font=(MONO, 10), bd=0, relief="flat", padx=12, pady=9,
                         wrap="word", height=25, insertbackground=COL["text"])
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=report.yview,
                                  style="Neutral.Vertical.TScrollbar")
        report.configure(yscrollcommand=scrollbar.set)
        report.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        report.insert("1.0", self.current_report() if self.findings is not None
                      else "Your report will appear here after you analyze a document.")
        report.configure(state="disabled")

    def _about(self):
        self._page_heading(
            "Behind the recognizer",
            "A transparent, character-by-character deterministic finite automaton.",
        )
        explanation = [
            ("01", "Upload & extract", "The user selects a TXT, DOCX or text-based PDF. "
             "The program extracts readable text locally on the computer."),
            ("02", "Tokenize", "Text is split into word-like tokens and candidate phrases. "
             "Punctuation is not accepted as part of a standalone word."),
            ("03", "Traverse DFA", "Each candidate begins at q0. Every character "
             "moves to exactly one next state. An invalid transition enters the rejecting sink."),
            ("04", "Accept & report", "If the final state is accepting, the system records "
             "the matching word, suggestion, character offsets and line number."),
        ]
        for number, title, description in explanation:
            card, inner = panel(self.body, padding=15)
            card.pack(fill="x", pady=(0, 10))
            counter = txt(inner, number, size=17, weight="bold", color=COL["accent"])
            counter.pack(side="left", padx=(3, 19))
            desc = tk.Frame(inner, bg=COL["surface"])
            desc.pack(side="left", fill="x", expand=True)
            txt(desc, title, size=12, weight="bold").pack(anchor="w")
            txt(desc, description, size=10, color=COL["muted"],
                wraplength=680).pack(anchor="w", pady=(5, 0))

        self._section_head(self.body, "Example transition", "FOR THE INPUT  'he'")
        card, inside = panel(self.body, padding=26)
        card.pack(fill="x")
        dfa = tk.Canvas(inside, bg=COL["surface"], height=105,
                        highlightthickness=0)
        dfa.pack(fill="x")
        # Static DFA illustration: start q0, transition h/e, accepting q2.
        for x, value in ((105, "q0"), (310, "q1"), (515, "q2")):
            dfa.create_oval(x-31, 20, x+31, 82, outline=COL["accent"], width=2,
                            fill=COL["surface2"])
            if value == "q2":
                dfa.create_oval(x-25, 26, x+25, 76, outline=COL["accent"], width=1)
            dfa.create_text(x, 51, text=value, fill=COL["text"],
                            font=(MONO, 13, "bold"))
        for x1, x2, char in ((136, 279, "h"), (341, 484, "e")):
            dfa.create_line(x1, 51, x2, 51, fill=COL["accent"], width=2, arrow="last")
            dfa.create_text((x1+x2)/2, 34, text=char, fill=COL["accent"],
                            font=(MONO, 12, "bold"))
        txt(inside, "q0 = start  •  q2 = accepting state  •  missing transitions = rejecting sink",
            size=10, color=COL["muted"]).pack(anchor="w", pady=(8, 0))
        self._section_head(self.body, "Project notes")
        notes, textframe = panel(self.body, padding=20)
        notes.pack(fill="x")
        txt(textframe, f"{self.dfa.term_count} known terms and phrases  •  "
            f"{self.dfa.state_count} DFA states (including rejecting sink)",
            size=11, weight="bold", color=COL["accent"]).pack(anchor="w")
        txt(textframe,
            "This is a rule-based academic scanner, not a grammar checker. Results only cover "
            "the predefined vocabulary. Pronouns and gendered references can be appropriate "
            "in context; recommendations require human judgment. Scanned PDF images "
            "require OCR, which is not included.", size=10,
            color=COL["muted"], wraplength=700).pack(anchor="w", pady=(12, 0))

    # ----- User actions -----

    def choose_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Choose a document for DFA analysis",
            filetypes=[
                ("Supported documents", "*.txt *.docx *.pdf"),
                ("Text file", "*.txt"),
                ("Word document", "*.docx"),
                ("PDF document", "*.pdf"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.set_source(path)

    def load_sample(self):
        path = Path(__file__).resolve().parent / "samples" / "sample_with_gender_terms.txt"
        self.set_source(path)
        self.analyze()

    def set_source(self, path):
        self.source_path = Path(path)
        self.source_text = ""
        self.findings = None
        self.active_page = "Overview"
        self.render()

    def analyze(self):
        if not self.source_path:
            messagebox.showwarning("Select a document", "Please select a document first.")
            return
        try:
            extracted = extract_text(self.source_path)
            if not extracted.strip():
                messagebox.showwarning(
                    "No readable text",
                    "This document has no readable text. Scanned PDFs may need OCR."
                )
                return
            matches = self.dfa.scan(extracted)
        except Exception as exc:
            messagebox.showerror("Could not analyze document", str(exc))
            return

        self.source_text = extracted
        self.findings = matches
        self.active_page = "Overview"
        self.render()

    def current_report(self):
        return plain_report(
            str(self.source_path), self.findings or [],
            self.dfa.state_count, self.source_text,
        )

    def export_txt(self):
        if self.findings is None:
            messagebox.showinfo("No report yet", "Analyze a document first.")
            return
        stem = self.source_path.stem if self.source_path else "document"
        target = filedialog.asksaveasfilename(
            parent=self, defaultextension=".txt", initialfile=f"{stem}_report.txt",
            filetypes=[("Text report", "*.txt")], title="Save analysis report",
        )
        if not target:
            return
        try:
            Path(target).write_text(self.current_report(), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save error", str(exc))
            return
        messagebox.showinfo("Report saved", f"Saved to:\n{target}")

    def export_csv(self):
        if self.findings is None:
            messagebox.showinfo("No results yet", "Analyze a document first.")
            return
        stem = self.source_path.stem if self.source_path else "document"
        target = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv", initialfile=f"{stem}_findings.csv",
            filetypes=[("CSV file", "*.csv")], title="Export findings as CSV",
        )
        if not target:
            return
        try:
            # utf-8-sig opens neatly in Excel on Windows.
            Path(target).write_text(csv_report(self.findings), encoding="utf-8-sig")
        except OSError as exc:
            messagebox.showerror("Save error", str(exc))
            return
        messagebox.showinfo("CSV exported", f"Saved to:\n{target}")

    def copy_report(self):
        if self.findings is None:
            messagebox.showinfo("No report yet", "Analyze a document first.")
            return
        self.clipboard_clear()
        self.clipboard_append(self.current_report())
        messagebox.showinfo("Copied", "Analysis report copied to clipboard.")
