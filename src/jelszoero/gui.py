"""Grafikus felület (CustomTkinter, világos téma).

Három oldal, a fejléc szöveges navigációjával:
    Vizsgálat   – a beírt jelszó élő értékelése (szabályalapú + gépi tanulás)
    Generátor   – erős jelszó vagy jelmondat generálása
    Modellek    – modellek tanítása CSV-ből, mérőszámok és ábrák

Tervezési döntések:
    * Betűtípus: Atkinson Hyperlegible – a Braille Institute olvashatósági
      betűtípusa, amelyben az összetéveszthető jelek (l, 1, I, 0, O) jól
      megkülönböztethetők. Jelszavaknál ez nem díszítés, hanem funkció.
      A jelszó maga az Atkinson Hyperlegible Mono változattal jelenik meg.
    * Egyetlen hangsúlyos elem: a jelszó „bontása” – a program a
      karakterek alatt aláhúzással mutatja, melyik rész kitalálható minta.
    * Kártyák és díszítő keretek helyett térköz és vékony elválasztó vonalak;
      színt csak az erősség jelzése kap.

A jelszavakat a program sehova nem menti és nem küldi tovább.
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from . import LEVEL_NAMES
from .generator import generate_passphrase, generate_password
from .ml_model import (
    DEFAULT_MODEL_PATH,
    PROJECT_ROOT,
    REPORTS_DIR,
    load_metrics,
    load_model,
    predict,
    train_and_compare,
)
from .rules import RuleResult, evaluate

# ---------------------------------------------------------------------------
# Színek
# ---------------------------------------------------------------------------
BG = "#F3F5F4"          # ablakháttér: hűvös, enyhén zöldes szürke
FIELD = "#FFFFFF"       # beviteli mezők
INK = "#1E2522"         # fő szövegszín és elsődleges gombok
INK_HOVER = "#39443F"
TEXT_2 = "#5E6964"      # másodlagos szöveg
TEXT_3 = "#8C9692"      # halvány szöveg (inaktív navigáció, üres állapot)
RULE = "#DCE1DE"        # elválasztó vonalak
EDGE = "#C3CBC7"        # mezők kerete
EDGE_FOCUS = "#1E2522"
TRACK = "#DFE4E1"       # sávok háttere

# négy megjelenítési fokozat (a 3 osztályos szintből és az entrópiából)
LEVELS = [
    ("Nagyon gyenge", "#A3301F"),
    ("Gyenge", "#C2541C"),
    ("Közepes", "#AD7C06"),
    ("Erős", "#2D7A4B"),
]
ML_COLORS = {0: LEVELS[1][1], 1: LEVELS[2][1], 2: LEVELS[3][1]}
VERY_WEAK_BITS = 20.0

EXAMPLES = ["123456", "Macska2024!", "qwertz123", "tulipán-vödör-rigó-kréta-malom42", "xK9#mQ2$vL7@pR4!"]

PLOTS = {
    "Modellek összehasonlítása": "model_comparison.png",
    "Tévesztési mátrixok": "confusion_matrices.png",
    "Jellemzők fontossága": "feature_importance.png",
    "Osztályeloszlás": "class_distribution.png",
}

FONT_DIR = Path(__file__).resolve().parent / "assets" / "fonts"
UI_FAMILY_WANTED = "Atkinson Hyperlegible"
MONO_FAMILY_WANTED = "Atkinson Hyperlegible Mono"


def display_level(r: RuleResult) -> int:
    """3 osztályos szint -> 4 fokozat (a gyenge osztályt kettébontjuk)."""
    if r.level == 0:
        return 0 if r.entropy_bits < VERY_WEAK_BITS else 1
    return r.level + 1


def hu_num(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def crack_sentence(r: RuleResult) -> str:
    off = r.crack_times_text["offline"]
    on = r.crack_times_text["online"]
    first = ("Egy jelszófeltörő gép azonnal kitalálja." if off == "azonnal"
             else f"Egy jelszófeltörő gépnek {off} kellene hozzá.")
    second = (" Bejelentkezési kísérletekkel is azonnal." if on == "azonnal"
              else f" Bejelentkezési kísérletekkel: {on}.")
    return first + second


def load_fonts() -> None:
    """A mellékelt betűtípusok regisztrálása (Windows és Linux; macOS-en rendszerfont)."""
    for ttf in FONT_DIR.glob("*.ttf"):
        try:
            ctk.FontManager.load_font(str(ttf))
        except Exception:
            pass


def resolve_family(root: tk.Misc, wanted: str, fallbacks: tuple[str, ...]) -> str:
    families = set(tkfont.families(root))
    for name in (wanted, *fallbacks):
        if name in families:
            return name
    return "TkDefaultFont"


# ---------------------------------------------------------------------------
# A jelszó bontása: karakterek + aláhúzott minták
# ---------------------------------------------------------------------------
class Breakdown(tk.Canvas):
    """A jelszót karakterenként rajzolja ki, a felismert mintákat aláhúzza,
    és alájuk írja a minta nevét. Rejtett módban pontokat mutat."""

    def __init__(self, master, mono: str, ui: str):
        super().__init__(master, height=64, bg=BG, highlightthickness=0, bd=0)
        self.mono = tkfont.Font(family=mono, size=17)
        self.label_font = tkfont.Font(family=ui, size=10)
        self._data = ("", [], True, INK)
        self.bind("<Configure>", lambda e: self._draw())

    def set(self, password: str, matches, hidden: bool, color: str) -> None:
        self._data = (password, matches, hidden, color)
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        pw, matches, hidden, color = self._data
        if not pw:
            self.create_text(0, 14, anchor="w", text="Itt jelennek meg a jelszó kitalálható részei.",
                             font=self.label_font, fill=TEXT_3)
            return
        cw = self.mono.measure("M")
        width = self.winfo_width()
        max_chars = max(1, width // cw)
        shown = pw[:max_chars]
        for i, ch in enumerate(shown):
            covered = any(m.start <= i < m.end for m in matches)
            self.create_text(i * cw + cw / 2, 14, text="•" if hidden else ch, font=self.mono,
                             fill=INK if covered or not matches else TEXT_2)
        # aláhúzások és címkék; az egymásba érő címkéket külön sorba tesszük
        row_ends: list[int] = []
        for m in sorted(matches, key=lambda m: m.start):
            if m.start >= len(shown):
                continue
            x0 = m.start * cw + 2
            x1 = min(m.end, len(shown)) * cw - 2
            self.create_line(x0, 30, x1, 30, fill=color, width=3, capstyle="round")
            text_w = self.label_font.measure(m.kind)
            row = next((k for k, end in enumerate(row_ends) if x0 > end + 8), len(row_ends))
            if row == len(row_ends):
                row_ends.append(0)
            row_ends[row] = x0 + text_w
            if row < 2:
                self.create_text(x0, 44 + row * 15, anchor="w", text=m.kind,
                                 font=self.label_font, fill=TEXT_2)


# ---------------------------------------------------------------------------
# Az alkalmazás
# ---------------------------------------------------------------------------
class App(ctk.CTk):
    def __init__(self) -> None:
        ctk.set_appearance_mode("light")
        load_fonts()
        super().__init__(fg_color=BG)
        self.title("Jelszóerősség")
        self.geometry("1080x760")
        self.minsize(940, 660)

        ui = resolve_family(self, UI_FAMILY_WANTED, ("Segoe UI", "Helvetica Neue", "Ubuntu", "DejaVu Sans"))
        mono = resolve_family(self, MONO_FAMILY_WANTED, ("Cascadia Mono", "Consolas", "Menlo", "DejaVu Sans Mono"))
        self.ui_family, self.mono_family = ui, mono
        self.f = {
            "small": ctk.CTkFont(ui, 12),
            "body": ctk.CTkFont(ui, 14),
            "body_b": ctk.CTkFont(ui, 14, "bold"),
            "nav": ctk.CTkFont(ui, 15),
            "nav_b": ctk.CTkFont(ui, 15, "bold"),
            "app": ctk.CTkFont(ui, 18, "bold"),
            "h": ctk.CTkFont(ui, 17, "bold"),
            "level": ctk.CTkFont(ui, 38, "bold"),
            "pw": ctk.CTkFont(mono, 21),
            "mono_s": ctk.CTkFont(mono, 13),
        }

        self.model = load_model(DEFAULT_MODEL_PATH)
        self._after_id = None
        self._train_queue: queue.Queue = queue.Queue()
        self._plot_image = None
        self._hidden = True

        self._build_header()
        self.pages: dict[str, ctk.CTkFrame] = {}
        self.body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.body.pack(fill="both", expand=True)
        self._build_check_page()
        self._build_gen_page()
        self._build_models_page()
        self.show_page("check")
        self.analyze()
        self._generate()
        self._refresh_metrics()

    # ------------------------------------------------------------------ közös elemek
    def text(self, parent, value="", font="body", color=INK, **kw) -> ctk.CTkLabel:
        kw.setdefault("width", 1)    # a címke csak akkora, amekkora a szöveg
        kw.setdefault("height", 1)
        return ctk.CTkLabel(parent, text=value, font=self.f[font], text_color=color,
                            anchor="w", justify="left", fg_color="transparent", **kw)

    def primary(self, parent, value, command, width=0) -> ctk.CTkButton:
        return ctk.CTkButton(parent, text=value, command=command, font=self.f["body_b"],
                             fg_color=INK, hover_color=INK_HOVER, text_color="#FFFFFF",
                             corner_radius=6, height=38, width=width or 140)

    def secondary(self, parent, value, command, width=0) -> ctk.CTkButton:
        return ctk.CTkButton(parent, text=value, command=command, font=self.f["body"],
                             fg_color="transparent", hover_color="#E4E9E6", text_color=INK,
                             border_color=EDGE, border_width=1, corner_radius=6, height=38,
                             width=width or 110)

    def quiet(self, parent, value, command) -> ctk.CTkButton:
        """Keret nélküli szöveggomb (pl. Mutasd, Törlés)."""
        return ctk.CTkButton(parent, text=value, command=command, font=self.f["body"],
                             fg_color="transparent", hover_color="#E4E9E6", text_color=TEXT_2,
                             corner_radius=6, height=34, width=10)

    def rule(self, parent, **pack) -> None:
        ctk.CTkFrame(parent, height=1, fg_color=RULE, corner_radius=0).pack(fill="x", **pack)

    def checkbox(self, parent, value, variable, command=None) -> ctk.CTkCheckBox:
        return ctk.CTkCheckBox(parent, text=value, variable=variable, command=command,
                               font=self.f["body"], text_color=INK, fg_color=INK,
                               hover_color=INK_HOVER, border_color=EDGE, border_width=2,
                               checkbox_width=18, checkbox_height=18, corner_radius=4)

    def meter(self, parent) -> ctk.CTkProgressBar:
        bar = ctk.CTkProgressBar(parent, height=6, corner_radius=3, fg_color=TRACK,
                                 progress_color=TRACK, border_width=0)
        bar.set(0)
        return bar

    # ------------------------------------------------------------------ fejléc
    def _build_header(self) -> None:
        head = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        head.pack(fill="x", padx=40, pady=(22, 0))
        self.text(head, "Jelszóerősség", "app").pack(side="left")

        nav = ctk.CTkFrame(head, fg_color="transparent")
        nav.pack(side="left", padx=(56, 0))
        self.nav_items = {}
        for key, label in (("check", "Vizsgálat"), ("gen", "Generátor"), ("models", "Modellek")):
            cell = ctk.CTkFrame(nav, fg_color="transparent")
            cell.pack(side="left", padx=(0, 28))
            lab = self.text(cell, label, "nav", TEXT_3, cursor="hand2")
            lab.pack()
            bar = ctk.CTkFrame(cell, width=1, height=2, corner_radius=0, fg_color=BG)
            bar.pack(fill="x", pady=(2, 0))
            lab.bind("<Button-1>", lambda e, k=key: self.show_page(k))
            self.nav_items[key] = (lab, bar)

        self.privacy = self.text(head, "A beírt jelszót a program nem menti és nem küldi el.", "small", TEXT_3)
        self.privacy.pack(side="right")
        self.rule(self, padx=0, pady=(12, 0))

    def show_page(self, key: str) -> None:
        for k, page in self.pages.items():
            page.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        for k, (lab, bar) in self.nav_items.items():
            active = k == key
            lab.configure(text_color=INK if active else TEXT_3, font=self.f["nav_b" if active else "nav"])
            bar.configure(fg_color=INK if active else BG)
        if key == "check":
            self.entry.focus_set()

    def _page(self, key: str, scroll: bool = True):
        if scroll:
            page = ctk.CTkScrollableFrame(self.body, fg_color=BG, corner_radius=0,
                                          scrollbar_button_color="#CDD4D0",
                                          scrollbar_button_hover_color="#B5BEB9")
        else:
            page = ctk.CTkFrame(self.body, fg_color=BG, corner_radius=0)
        self.pages[key] = page
        inner = ctk.CTkFrame(page, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=40, pady=(28, 28))
        return inner

    # ------------------------------------------------------------------ Vizsgálat
    def _build_check_page(self) -> None:
        p = self._page("check")

        self.text(p, "Írd be a jelszót", "body_b").pack(anchor="w")
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x", pady=(8, 0))
        self.pw_var = tk.StringVar()
        self.pw_var.trace_add("write", lambda *_: self._schedule_analyze())
        self.entry = ctk.CTkEntry(row, textvariable=self.pw_var, show="•", font=self.f["pw"],
                                  height=52, corner_radius=6, border_width=1, border_color=EDGE,
                                  fg_color=FIELD, text_color=INK)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<FocusIn>", lambda e: self.entry.configure(border_color=EDGE_FOCUS))
        self.entry.bind("<FocusOut>", lambda e: self.entry.configure(border_color=EDGE))
        self.show_btn = self.quiet(row, "Mutasd", self._toggle_show)
        self.show_btn.pack(side="left", padx=(10, 0))
        self.quiet(row, "Törlés", lambda: self.pw_var.set("")).pack(side="left", padx=(2, 0))

        ex = ctk.CTkFrame(p, fg_color="transparent")
        ex.pack(fill="x", pady=(8, 0))
        self.text(ex, "Próbáld ki:", "small", TEXT_3).pack(side="left", padx=(0, 6))
        for sample in EXAMPLES:
            b = ctk.CTkButton(ex, text=sample, font=self.f["mono_s"], fg_color="transparent",
                              hover_color="#E4E9E6", text_color=TEXT_2, corner_radius=4,
                              height=24, width=10, command=lambda s=sample: self._use_example(s))
            b.pack(side="left", padx=(0, 2))

        self.breakdown = Breakdown(p, self.mono_family, self.ui_family)
        self.breakdown.pack(fill="x", pady=(18, 0))

        self.main_meter = self.meter(p)
        self.main_meter.pack(fill="x", pady=(6, 0))

        verdict = ctk.CTkFrame(p, fg_color="transparent")
        verdict.pack(fill="x", pady=(14, 0))
        self.level_lab = self.text(verdict, "", "level", TEXT_3)
        self.level_lab.pack(anchor="w")
        self.crack_lab = self.text(verdict, "", "body", TEXT_2, wraplength=760)
        self.crack_lab.pack(anchor="w", pady=(2, 0))

        self.rule(p, pady=(24, 22))

        cols = ctk.CTkFrame(p, fg_color="transparent")
        cols.pack(fill="both", expand=True)
        cols.grid_columnconfigure(0, weight=3, uniform="c")
        cols.grid_columnconfigure(1, minsize=48)
        cols.grid_columnconfigure(2, weight=2, uniform="c")

        # bal oszlop: mi gyengíti, javaslatok, ellenőrzőlista
        left = ctk.CTkFrame(cols, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew")
        self.text(left, "Mi gyengíti?", "h").pack(anchor="w")
        self.warn_box = ctk.CTkFrame(left, fg_color="transparent")
        self.warn_box.pack(fill="x", pady=(6, 18))
        self.text(left, "Javaslatok", "h").pack(anchor="w")
        self.tip_box = ctk.CTkFrame(left, fg_color="transparent")
        self.tip_box.pack(fill="x", pady=(6, 18))
        self.text(left, "Ellenőrzőlista", "h").pack(anchor="w")
        self.check_box = ctk.CTkFrame(left, fg_color="transparent")
        self.check_box.pack(fill="x", pady=(8, 0))
        self.check_box.grid_columnconfigure((0, 1), weight=1, uniform="k")

        # jobb oszlop: gépi tanulás, részletek
        right = ctk.CTkFrame(cols, fg_color="transparent")
        right.grid(row=0, column=2, sticky="nsew")
        self.text(right, "Gépi tanulás", "h").pack(anchor="w")
        self.ml_verdict = self.text(right, "", "body", INK)
        self.ml_verdict.pack(anchor="w", pady=(6, 8))
        probs = ctk.CTkFrame(right, fg_color="transparent")
        probs.pack(fill="x")
        probs.grid_columnconfigure(1, weight=1)
        self.proba = []
        for i in range(3):
            self.text(probs, LEVEL_NAMES[i], "small", TEXT_2, width=70).grid(row=i, column=0, sticky="w")
            bar = self.meter(probs)
            bar.grid(row=i, column=1, sticky="ew", padx=(6, 10), pady=5)
            pct = self.text(probs, "", "small", TEXT_2, width=40)
            pct.grid(row=i, column=2, sticky="e")
            self.proba.append((bar, pct))
        self.ml_agree = self.text(right, "", "body", TEXT_2, wraplength=360)
        self.ml_agree.pack(anchor="w", pady=(8, 2))
        self.ml_model = self.text(right, "", "small", TEXT_3, wraplength=360)
        self.ml_model.pack(anchor="w")

        self.text(right, "Részletek", "h").pack(anchor="w", pady=(22, 6))
        facts = ctk.CTkFrame(right, fg_color="transparent")
        facts.pack(fill="x")
        facts.grid_columnconfigure(1, weight=1)
        self.facts = {}
        for i, key in enumerate(("Effektív entrópia", "Naiv entrópia", "Karakterkészlet", "Hossz", "Pontszám")):
            self.text(facts, key, "body", TEXT_2).grid(row=i, column=0, sticky="w", pady=2)
            v = self.text(facts, "", "body", INK)
            v.grid(row=i, column=1, sticky="e", pady=2)
            self.facts[key] = v

    # ------------------------------------------------------------------ Generátor
    def _build_gen_page(self) -> None:
        p = self._page("gen", scroll=False)
        self.text(p, "Új jelszó", "body_b").pack(anchor="w")

        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x", pady=(8, 0))
        self.gen_var = tk.StringVar()
        out = ctk.CTkEntry(row, textvariable=self.gen_var, font=self.f["pw"], height=52,
                           corner_radius=6, border_width=1, border_color=EDGE, fg_color=FIELD,
                           text_color=INK, state="readonly")
        out.pack(side="left", fill="x", expand=True)
        self.copy_btn = self.secondary(row, "Másolás", self._copy_generated)
        self.copy_btn.pack(side="left", padx=(10, 0))

        self.gen_meter = self.meter(p)
        self.gen_meter.pack(fill="x", pady=(12, 0))
        self.gen_info = self.text(p, "", "body", TEXT_2)
        self.gen_info.pack(anchor="w", pady=(8, 0))

        self.rule(p, pady=(24, 22))

        form = ctk.CTkFrame(p, fg_color="transparent")
        form.pack(fill="x")
        form.grid_columnconfigure(1, weight=1)

        self.text(form, "Típus", "body", TEXT_2, width=140).grid(row=0, column=0, sticky="w", pady=8)
        self.gen_type = tk.StringVar(value="Jelszó")
        toggle = ctk.CTkFrame(form, fg_color="#E3E8E5", corner_radius=8)
        toggle.grid(row=0, column=1, sticky="w", pady=8)
        self.type_btns = {}
        for value in ("Jelszó", "Jelmondat"):
            b = ctk.CTkButton(toggle, text=value, font=self.f["body"], corner_radius=6, height=30,
                              width=100, command=lambda v=value: self._set_type(v))
            b.pack(side="left", padx=2, pady=2)
            self.type_btns[value] = b

        self.len_row = ctk.CTkFrame(form, fg_color="transparent")
        self.len_label = self.text(form, "Hossz", "body", TEXT_2, width=140)
        self.len_var = tk.IntVar(value=16)
        self.len_slider = ctk.CTkSlider(self.len_row, from_=8, to=40, number_of_steps=32,
                                        command=self._on_length, width=360, height=16,
                                        progress_color=INK, button_color=INK, button_hover_color=INK_HOVER,
                                        fg_color=TRACK)
        self.len_slider.set(16)
        self.len_slider.pack(side="left")
        self.len_value = self.text(self.len_row, "16 karakter", "body", INK)
        self.len_value.pack(side="left", padx=(14, 0))

        self.words_row = ctk.CTkFrame(form, fg_color="transparent")
        self.words_label = self.text(form, "Szavak száma", "body", TEXT_2, width=140)
        self.words_var = tk.IntVar(value=6)
        self.words_slider = ctk.CTkSlider(self.words_row, from_=4, to=10, number_of_steps=6,
                                          command=self._on_words, width=200, height=16,
                                          progress_color=INK, button_color=INK, button_hover_color=INK_HOVER,
                                          fg_color=TRACK)
        self.words_slider.set(6)
        self.words_slider.pack(side="left")
        self.words_value = self.text(self.words_row, "6 szó", "body", INK)
        self.words_value.pack(side="left", padx=(14, 0))

        self.opts_label = self.text(form, "Karakterek", "body", TEXT_2, width=140)
        self.opts_row = ctk.CTkFrame(form, fg_color="transparent")
        self.sym_var = tk.BooleanVar(value=True)
        self.amb_var = tk.BooleanVar(value=True)
        self.checkbox(self.opts_row, "Speciális karakterek", self.sym_var, self._generate).pack(side="left")
        self.checkbox(self.opts_row, "Összetéveszthetők nélkül (I, l, 1, O, 0)", self.amb_var,
                      self._generate).pack(side="left", padx=(24, 0))

        actions = ctk.CTkFrame(p, fg_color="transparent")
        actions.pack(fill="x", pady=(26, 0))
        self.primary(actions, "Új jelszó", self._generate).pack(side="left")
        self.secondary(actions, "Vizsgálat ezzel", self._check_generated, width=150).pack(side="left", padx=(10, 0))
        self.text(p, "A generátor a Python secrets modulját használja, amely kriptográfiai célra alkalmas.",
                  "small", TEXT_3).pack(anchor="w", pady=(18, 0))
        self._on_type()

    # ------------------------------------------------------------------ Modellek
    def _build_models_page(self) -> None:
        p = self._page("models")
        self.text(p, "Modellek összehasonlítása", "h").pack(anchor="w")
        self.data_info = self.text(p, "", "body", TEXT_2, wraplength=900)
        self.data_info.pack(anchor="w", pady=(4, 14))

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("M.Treeview", background=BG, fieldbackground=BG, foreground=INK,
                        borderwidth=0, rowheight=30, font=(self.ui_family, 12))
        style.configure("M.Treeview.Heading", background=BG, foreground=TEXT_2, relief="flat",
                        borderwidth=0, font=(self.ui_family, 12, "bold"))
        style.map("M.Treeview.Heading", background=[("active", BG)])
        style.map("M.Treeview", background=[("selected", "#E1E7E4")], foreground=[("selected", INK)])
        style.layout("M.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        cols = ("acc", "prec", "rec", "f1")
        self.tree = ttk.Treeview(p, columns=cols, height=6, style="M.Treeview", selectmode="none")
        self.tree.heading("#0", text="Modell", anchor="w")
        self.tree.column("#0", width=380, anchor="w")
        for col, title in zip(cols, ("Pontosság", "Precision", "Recall", "F1 (makro)")):
            self.tree.heading(col, text=title, anchor="e")
            self.tree.column(col, width=120, anchor="e")
        self.tree.pack(fill="x")
        self.tree.tag_configure("best", font=(self.ui_family, 12, "bold"))
        self.tree.tag_configure("ref", foreground=TEXT_2)
        self.rule(p, pady=(4, 0))

        btns = ctk.CTkFrame(p, fg_color="transparent")
        btns.pack(fill="x", pady=(16, 0))
        self.btn_csv = self.primary(btns, "Tanítás CSV-ből…", self._train_from_csv, width=170)
        self.btn_csv.pack(side="left")
        self.btn_fb = self.secondary(btns, "Tanítás beépített adattal", self._train_fallback, width=200)
        self.btn_fb.pack(side="left", padx=(10, 0))
        self.progress = ctk.CTkProgressBar(btns, mode="indeterminate", width=160, height=6,
                                           progress_color=INK, fg_color=TRACK)

        lower = ctk.CTkFrame(p, fg_color="transparent")
        lower.pack(fill="both", expand=True, pady=(26, 0))
        lower.grid_columnconfigure(0, weight=3, uniform="l")
        lower.grid_columnconfigure(1, minsize=40)
        lower.grid_columnconfigure(2, weight=2, uniform="l")

        plot_col = ctk.CTkFrame(lower, fg_color="transparent")
        plot_col.grid(row=0, column=0, sticky="nsew")
        self.plot_choice = tk.StringVar(value=next(iter(PLOTS)))
        ctk.CTkOptionMenu(plot_col, values=list(PLOTS), variable=self.plot_choice,
                          command=lambda v: self._show_plot(), font=self.f["body"],
                          dropdown_font=self.f["body"], fg_color="#E3E8E5", button_color="#D6DDD9",
                          button_hover_color="#C9D1CD", text_color=INK, dropdown_fg_color=FIELD,
                          dropdown_text_color=INK, dropdown_hover_color="#E8ECEA",
                          corner_radius=6, width=260, height=34).pack(anchor="w")
        self.plot_frame = ctk.CTkFrame(plot_col, fg_color="transparent")
        self.plot_frame.pack(fill="both", expand=True, pady=(12, 0))
        self.plot_label = self.text(self.plot_frame, "", "body", TEXT_3)
        self.plot_label.pack(anchor="nw")

        log_col = ctk.CTkFrame(lower, fg_color="transparent")
        log_col.grid(row=0, column=2, sticky="nsew")
        self.text(log_col, "Tanítási napló", "body_b").pack(anchor="w")
        self.log = ctk.CTkTextbox(log_col, height=300, font=self.f["mono_s"], fg_color=FIELD,
                                  text_color=INK, border_color=RULE, border_width=1, corner_radius=6,
                                  wrap="word")
        self.log.pack(fill="both", expand=True, pady=(8, 0))
        self.log.insert("end", "A tanítás menete itt jelenik meg.\n\nA Kaggle data.csv a data mappába "
                               "másolva vagy a „Tanítás CSV-ből…” gombbal tölthető be.\n")
        self.log.configure(state="disabled")

    # ------------------------------------------------------------------ Vizsgálat: logika
    def _toggle_show(self) -> None:
        self._hidden = not self._hidden
        self.entry.configure(show="•" if self._hidden else "")
        self.show_btn.configure(text="Mutasd" if self._hidden else "Elrejt")
        self.analyze()

    def _use_example(self, sample: str) -> None:
        self.pw_var.set(sample)
        self.entry.focus_set()
        self.entry.icursor("end")

    def _schedule_analyze(self) -> None:
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(100, self.analyze)

    def _fill(self, box, lines: list[str], color: str, empty: str) -> None:
        for w in box.winfo_children():
            w.destroy()
        if not lines:
            self.text(box, empty, "body", TEXT_3).pack(anchor="w")
            return
        for line in lines:
            r = ctk.CTkFrame(box, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkFrame(r, width=3, height=18, corner_radius=1, fg_color=color).pack(side="left", anchor="n", pady=(2, 0))
            self.text(r, line, "body", INK, wraplength=520).pack(side="left", padx=(10, 0))

    def analyze(self) -> None:
        pw = self.pw_var.get()
        r = evaluate(pw)
        d = display_level(r)
        name, color = LEVELS[d]

        self.breakdown.set(pw, r.matches if pw else [], self._hidden, color)
        if pw:
            self.main_meter.configure(progress_color=color)
            self.main_meter.set(max(0.04, r.score / 100))
            self.level_lab.configure(text=name, text_color=color)
            self.crack_lab.configure(text=crack_sentence(r))
        else:
            self.main_meter.configure(progress_color=TRACK)
            self.main_meter.set(0)
            self.level_lab.configure(text="Még nincs mit értékelni", text_color=TEXT_3)
            self.crack_lab.configure(text="Gépelés közben itt látod, mennyi idő alatt lehetne kitalálni.")

        warnings = r.warnings
        tips = [s for s in r.suggestions if not s.startswith("Írj be")]
        self._fill(self.warn_box, warnings if pw else [], color,
                   "Nem talált kitalálható mintát." if pw else "Itt jelennek meg a talált gyengeségek.")
        self._fill(self.tip_box, tips if pw else [], EDGE, "A javaslatok a beírt jelszóhoz igazodnak.")

        for w in self.check_box.winfo_children():
            w.destroy()
        half = (len(r.checks) + 1) // 2
        for i, chk in enumerate(r.checks):
            ok = chk.passed and bool(pw)
            cell = ctk.CTkFrame(self.check_box, fg_color="transparent")
            cell.grid(row=i % half, column=i // half, sticky="w", pady=3)
            ctk.CTkFrame(cell, width=10, height=10, corner_radius=2,
                         fg_color=INK if ok else BG, border_color=INK if ok else EDGE,
                         border_width=0 if ok else 2).pack(side="left")
            self.text(cell, chk.label, "body", INK if ok else TEXT_2).pack(side="left", padx=(10, 0))

        self.facts["Effektív entrópia"].configure(text=f"{hu_num(r.entropy_bits)} bit")
        self.facts["Naiv entrópia"].configure(text=f"{hu_num(r.naive_entropy_bits)} bit")
        self.facts["Karakterkészlet"].configure(text=f"{r.pool_size} féle karakter")
        self.facts["Hossz"].configure(text=f"{r.password_length} karakter")
        self.facts["Pontszám"].configure(text=f"{r.score} / 100")

        # gépi tanulás
        if self.model:
            m = self.model["metrics"]
            src = Path(str(self.model.get("data_source", ""))).name or "ismeretlen adat"
            self.ml_model.configure(text=f"{self.model['name']}, teszt F1 = {hu_num(m['f1'], 3)}, "
                                         f"tanítóadat: {src}")
        else:
            self.ml_model.configure(text="Nincs betanított modell. A Modellek oldalon tanítható.")
        if self.model and pw:
            try:
                label, proba = predict(self.model, pw)
                self.ml_verdict.configure(text=f"A modell szerint {LEVEL_NAMES[label].lower()}.")
                for i, (bar, pct) in enumerate(self.proba):
                    bar.configure(progress_color=ML_COLORS[i])
                    bar.set(proba[i])
                    pct.configure(text=f"{proba[i]:.0%}")
                if label == r.level:
                    self.ml_agree.configure(text="Egyezik a szabályalapú értékeléssel.", text_color=TEXT_2)
                else:
                    self.ml_agree.configure(
                        text=f"Eltér: a szabályok szerint {r.level_name.lower()}. "
                             "A modell címkéi csak a hosszt veszik figyelembe.",
                        text_color=LEVELS[1][1])
            except Exception as exc:
                self.ml_verdict.configure(text=f"Az előrejelzés nem sikerült: {exc}")
        else:
            self.ml_verdict.configure(text="A modell ítélete itt jelenik meg." if self.model else "")
            for bar, pct in self.proba:
                bar.configure(progress_color=TRACK)
                bar.set(0)
                pct.configure(text="")
            self.ml_agree.configure(text="")

    # ------------------------------------------------------------------ Generátor: logika
    def _set_type(self, value: str) -> None:
        self.gen_type.set(value)
        self._on_type()

    def _on_type(self) -> None:
        for value, b in self.type_btns.items():
            active = value == self.gen_type.get()
            b.configure(fg_color=INK if active else "transparent",
                        hover_color=INK_HOVER if active else "#D6DDD9",
                        text_color="#FFFFFF" if active else INK)
        is_phrase = self.gen_type.get() == "Jelmondat"
        for w in (self.len_label, self.len_row, self.opts_label, self.opts_row,
                  self.words_label, self.words_row):
            w.grid_forget()
        if is_phrase:
            self.words_label.grid(row=1, column=0, sticky="w", pady=8)
            self.words_row.grid(row=1, column=1, sticky="w", pady=8)
        else:
            self.len_label.grid(row=1, column=0, sticky="w", pady=8)
            self.len_row.grid(row=1, column=1, sticky="w", pady=8)
            self.opts_label.grid(row=2, column=0, sticky="w", pady=8)
            self.opts_row.grid(row=2, column=1, sticky="w", pady=8)
        self._generate()

    def _generate(self) -> None:
        if self.gen_type.get() == "Jelmondat":
            pw = generate_passphrase(int(self.words_var.get()))
        else:
            pw = generate_password(int(self.len_var.get()), self.sym_var.get(), self.amb_var.get())
        self.gen_var.set(pw)
        self.copy_btn.configure(text="Másolás")
        r = evaluate(pw)
        name, color = LEVELS[display_level(r)]
        self.gen_meter.configure(progress_color=color)
        self.gen_meter.set(max(0.04, r.score / 100))
        self.gen_info.configure(text=f"{name}, {hu_num(r.entropy_bits)} bit. {crack_sentence(r)}")

    def _on_length(self, value) -> None:
        n = int(round(float(value)))
        if n != self.len_var.get():
            self.len_var.set(n)
            self.len_value.configure(text=f"{n} karakter")
            self._generate()

    def _on_words(self, value) -> None:
        n = int(round(float(value)))
        if n != self.words_var.get():
            self.words_var.set(n)
            self.words_value.configure(text=f"{n} szó")
            self._generate()

    def _copy_generated(self) -> None:
        if self.gen_var.get():
            self.clipboard_clear()
            self.clipboard_append(self.gen_var.get())
            self.copy_btn.configure(text="Másolva")

    def _check_generated(self) -> None:
        if self.gen_var.get():
            self.pw_var.set(self.gen_var.get())
            self.show_page("check")

    # ------------------------------------------------------------------ Modellek: logika
    def _log(self, line: str, clear: bool = False) -> None:
        self.log.configure(state="normal")
        if clear:
            self.log.delete("1.0", "end")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _refresh_metrics(self) -> None:
        self.tree.delete(*self.tree.get_children())
        metrics = load_metrics()
        if not metrics:
            self.data_info.configure(text="Még nincs tanítási eredmény. Indíts egy tanítást lent.")
            self._show_plot()
            return
        when = metrics["trained_at"].replace("T", " ")[:16]
        self.data_info.configure(
            text=f"{metrics['n_samples']:,} jelszón tanítva ({Path(metrics['data_source']).name}), "
                 f"{when}. A legjobb modell a {metrics['best_model']}; ez értékel a Vizsgálat oldalon."
                 .replace(",", " ", 1))
        for m in metrics["models"] + [metrics["rule_based"]]:
            if m["name"] == metrics["best_model"]:
                tags = ("best",)
            elif m["name"].startswith(("Alapmodell", "Szabályalapú")):
                tags = ("ref",)
            else:
                tags = ()
            self.tree.insert("", "end", text=m["name"], tags=tags, values=tuple(
                hu_num(m[k], 4) for k in ("accuracy", "precision", "recall", "f1")))
        self._show_plot()

    def _show_plot(self) -> None:
        path = REPORTS_DIR / PLOTS[self.plot_choice.get()]
        if not path.exists():
            self.plot_label.configure(image=None, text="Nincs még ábra. Tanítsd be a modelleket.")
            return
        try:
            from PIL import Image
            img = Image.open(path)
            self.update_idletasks()
            max_w = max(self.plot_frame.winfo_width(), 520)
            max_h = 360
            scale = min(max_w / img.width, max_h / img.height, 1.0)
            size = (int(img.width * scale), int(img.height * scale))
            self._plot_image = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            self.plot_label.configure(image=self._plot_image, text="")
        except Exception as exc:
            self.plot_label.configure(image=None, text=f"Az ábra nem tölthető be: {exc}")

    def _train_from_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="Kaggle data.csv kiválasztása", initialdir=str(PROJECT_ROOT / "data"),
            filetypes=[("CSV fájl", "*.csv"), ("Minden fájl", "*.*")])
        if path:
            self._start_training(path)

    def _train_fallback(self) -> None:
        self._start_training(None)

    def _start_training(self, csv_path: str | None) -> None:
        for b in (self.btn_csv, self.btn_fb):
            b.configure(state="disabled")
        self.progress.pack(side="left", padx=16)
        self.progress.start()
        self._log("Tanítás folyamatban. Nagy adathalmaznál néhány percig tart.", clear=True)

        def worker():
            try:
                from .data import generate_fallback_dataset, load_kaggle_csv
                if csv_path:
                    self._train_queue.put(("log", f"Beolvasás: {csv_path}"))
                    df = load_kaggle_csv(csv_path, max_rows=200_000)
                    self._train_queue.put(("log", f"{len(df)} egyedi jelszó"))
                else:
                    df = generate_fallback_dataset()
                summary = train_and_compare(df, progress=lambda m: self._train_queue.put(("log", m)))
                self._train_queue.put(("done", summary))
            except Exception as exc:  # pragma: no cover - GUI hibaút
                self._train_queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        self.after(100, self._poll_training)

    def _poll_training(self) -> None:
        try:
            while True:
                kind, payload = self._train_queue.get_nowait()
                if kind == "log":
                    self._log(payload)
                    continue
                self.progress.stop()
                self.progress.pack_forget()
                for b in (self.btn_csv, self.btn_fb):
                    b.configure(state="normal")
                if kind == "done":
                    self.model = load_model(DEFAULT_MODEL_PATH)
                    self._refresh_metrics()
                    self.analyze()
                    self._log(f"\nKész. Legjobb modell: {payload['best_model']}")
                else:
                    self._log(f"\nA tanítás leállt: {payload}")
                    messagebox.showerror("A tanítás leállt", payload)
                return
        except queue.Empty:
            pass
        self.after(100, self._poll_training)


def run() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run()
