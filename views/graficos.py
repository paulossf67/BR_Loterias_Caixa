"""Gráficos de barras desenhados em tk.Canvas (sem dependências extras)."""
import tkinter as tk
from typing import List, Optional, Sequence

import customtkinter as ctk


def _tema():
    escuro = ctk.get_appearance_mode() == "Dark"
    return {"bg": "#2b2b2b" if escuro else "#ffffff",
            "fg": "#dddddd" if escuro else "#333333",
            "grade": "#444444" if escuro else "#e6e6e6"}


class GraficoBarras(tk.Canvas):
    """Barras agrupadas. series: [(nome, cor, [valores...])]; rotulos: um por grupo.

    Com uma única série, `destaques` ({índice: cor}) permite colorir barras individuais.
    """

    MARGEM_E, MARGEM_D, MARGEM_T, MARGEM_B = 48, 12, 14, 32

    def __init__(self, parent, rotulos: Sequence[str], series: List[tuple],
                 altura: int = 220, destaques: Optional[dict] = None,
                 formato=lambda v: f"{v:,.0f}"):
        self.t = _tema()
        super().__init__(parent, height=altura, bg=self.t["bg"], highlightthickness=0)
        self.rotulos, self.series = list(rotulos), series
        self.altura, self.destaques, self.formato = altura, destaques or {}, formato
        self._barras = []
        self.bind("<Configure>", lambda e: self._desenhar())
        self.bind("<Motion>", self._mover)
        self.bind("<Leave>", lambda e: self.delete("dica"))

    def _desenhar(self):
        self.delete("all")
        self._barras = []
        if not self.rotulos:
            self.create_text(10, 10, anchor="nw", fill=self.t["fg"], text="Sem dados.")
            return
        w = max(self.winfo_width(), 200)
        area_w = w - self.MARGEM_E - self.MARGEM_D
        area_h = self.altura - self.MARGEM_T - self.MARGEM_B
        maximo = max((v for _, _, vals in self.series for v in vals), default=0) or 1
        base = self.altura - self.MARGEM_B
        for i in range(5):
            y = base - area_h * i / 4
            self.create_line(self.MARGEM_E, y, w - self.MARGEM_D, y, fill=self.t["grade"])
            self.create_text(self.MARGEM_E - 5, y, anchor="e", fill=self.t["fg"],
                             font=("Arial", 8), text=self.formato(maximo * i / 4))
        n, ns = len(self.rotulos), len(self.series)
        slot = area_w / n
        larg = max(slot * 0.8 / ns, 1)
        passo = max(1, int(28 / slot) + 1)  # evita rótulos sobrepostos
        for g in range(n):
            x0 = self.MARGEM_E + g * slot + slot * 0.1
            for s, (nome, cor, vals) in enumerate(self.series):
                v = vals[g]
                cor_barra = self.destaques.get(g, cor) if ns == 1 else cor
                h = area_h * v / maximo
                x = x0 + s * larg
                self.create_rectangle(x, base - h, x + larg, base, fill=cor_barra, outline="")
                self._barras.append((x, x + larg, f"{nome}: {self.formato(v)} ({self.rotulos[g]})"))
            if g % passo == 0:
                self.create_text(self.MARGEM_E + g * slot + slot / 2, base + 4, anchor="n",
                                 fill=self.t["fg"], font=("Arial", 8), text=self.rotulos[g])

    def _mover(self, e):
        self.delete("dica")
        for x0, x1, txt in self._barras:
            if x0 <= e.x <= x1:
                x = min(e.x + 8, max(self.winfo_width() - 200, 0))
                y = max(e.y - 22, 0)
                self.create_rectangle(x, y, x + 195, y + 18, fill="#333333", outline="", tags="dica")
                self.create_text(x + 4, y + 9, anchor="w", fill="white",
                                 font=("Arial", 8), text=txt, tags="dica")
                return


def legenda(parent, itens: Sequence[tuple]):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    for nome, cor in itens:
        ctk.CTkLabel(f, text="■", text_color=cor, font=("Arial", 14)).pack(side="left")
        ctk.CTkLabel(f, text=nome, font=("Arial", 11)).pack(side="left", padx=(2, 12))
    return f
