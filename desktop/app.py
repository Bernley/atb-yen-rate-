import sys
import os
import platform
import tkinter as tk
import threading
import httpx
from bs4 import BeautifulSoup
from PIL import Image, ImageTk

USE_BG = platform.system() == "Windows"

ATB_URL = "https://atb.su/services/exchange/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

W, H = 400, 600


def resource_path(name):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, name)


def get_jpy_rate():
    response = httpx.get(ATB_URL, timeout=10, headers=HEADERS, follow_redirects=True)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for name_td in soup.find_all("div", class_="currency-table__td--tr-name"):
        val_div = name_td.find("div", class_="currency-table__val")
        if val_div and val_div.get_text(strip=True).upper() == "JPY":
            row = name_td.parent
            tds = row.find_all("div", class_="currency-table__td")
            if len(tds) >= 3:
                sell_td = tds[2]
                raw = sell_td.get_text(strip=True)
                head = sell_td.find("div", class_="currency-table__head")
                if head:
                    raw = raw.replace(head.get_text(strip=True), "").strip()
                return float(raw.replace(",", ".").replace("\xa0", "").strip())
    raise ValueError("JPY rate not found")


def build_background(w, h):
    bg = Image.open(resource_path("bg.jpg")).convert("RGB").resize((w, h), Image.LANCZOS)
    # Semi-transparent white card area
    card_w, card_h = 340, 520
    cx = (w - card_w) // 2
    cy = (h - card_h) // 2
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    card = Image.new("RGBA", (card_w, card_h), (255, 255, 255, 128))
    overlay.paste(card, (cx, cy))
    result = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    return result, cx, cy, card_w, card_h


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Курс иены — АТБ")
        self.geometry(f"{W}x{H}")
        self.resizable(False, False)
        self.rate = None
        self._updating = False

        cx, cy, cw, ch = 30, 40, 340, 520
        if USE_BG:
            try:
                composite, cx, cy, cw, ch = build_background(W, H)
                self._bg_photo = ImageTk.PhotoImage(composite)
                bg_label = tk.Label(self, image=self._bg_photo, bd=0)
                bg_label.place(x=0, y=0, width=W, height=H)
            except Exception as e:
                print(f"bg error: {e}")
                self.configure(bg="#f0f2f5")
        else:
            self.configure(bg="#f0f2f5")

        self._build_ui(cx, cy, cw, ch)
        self.refresh()

    def _lbl(self, text, font, fg, bg="#ffffff"):
        return tk.Label(self, text=text, font=font, fg=fg, bg=bg, bd=0)

    def _build_ui(self, cx, cy, cw, ch):
        mid = cx + cw // 2
        top = cy + 20

        # Bank name
        tk.Label(self, text="АТБ БАНК", font=("Helvetica", 10),
                 fg="#888888", bg="#f0f2f5", bd=0).place(x=mid, y=top, anchor="n")

        # Title
        tk.Label(self, text="Курс покупки иены", font=("Helvetica", 15, "bold"),
                 fg="#333333", bg="#f0f2f5", bd=0).place(x=mid, y=top+24, anchor="n")

        # Currency pair
        tk.Label(self, text="JPY → RUB", font=("Helvetica", 11),
                 fg="#aaaaaa", bg="#f0f2f5", bd=0).place(x=mid, y=top+52, anchor="n")

        # Rate
        self.rate_lbl = tk.Label(self, text="...", font=("Helvetica", 52, "bold"),
                                  fg="#1a1a1a", bg="#f0f2f5", bd=0)
        self.rate_lbl.place(x=mid, y=top+80, anchor="n")

        # Unit
        tk.Label(self, text="рублей за 100 ¥", font=("Helvetica", 13),
                 fg="#555555", bg="#f0f2f5", bd=0).place(x=mid, y=top+148, anchor="n")

        # Status
        self.status_lbl = tk.Label(self, text="Загрузка...", font=("Helvetica", 10),
                                    fg="#aaaaaa", bg="#f0f2f5", bd=0)
        self.status_lbl.place(x=mid, y=top+172, anchor="n")

        # Divider
        tk.Frame(self, bg="#e0e0e0", height=1).place(x=cx+20, y=top+200, width=cw-40)

        # Converter label
        tk.Label(self, text="КОНВЕРТЕР", font=("Helvetica", 9),
                 fg="#aaaaaa", bg="#f0f2f5", bd=0).place(x=mid, y=top+215, anchor="n")

        # Yen input
        self.yen_var = tk.StringVar()
        self.yen_var.trace("w", self.on_yen_change)
        self._yen_entry = tk.Entry(self, textvariable=self.yen_var,
                                   font=("Helvetica", 20, "bold"),
                                   bd=1, relief="solid", fg="#1a1a1a",
                                   justify="right", bg="white")
        self._yen_entry.place(x=cx+20, y=top+240, width=cw-40, height=46)

        # Yen symbol label beside entry
        tk.Label(self, text="¥", font=("Helvetica", 16),
                 fg="#aaaaaa", bg="white").place(x=cx+cw-36, y=top+254, anchor="center")

        # Result box
        result_y = top + 305
        result_frame = tk.Frame(self, bg="#1a1a1a")
        result_frame.place(x=cx+20, y=result_y, width=cw-40, height=50)
        tk.Label(result_frame, text="Рублей", font=("Helvetica", 12),
                 fg="#888888", bg="#1a1a1a").place(x=12, y=14)
        self.rub_lbl = tk.Label(result_frame, text="— ₽", font=("Helvetica", 20, "bold"),
                                 fg="white", bg="#1a1a1a")
        self.rub_lbl.place(x=cw-60, y=10, anchor="ne")

        # Refresh button
        self.refresh_btn = tk.Button(self, text="↻  Обновить курс",
                                     command=self.refresh,
                                     bg="white", fg="#555555",
                                     font=("Helvetica", 12),
                                     bd=1, relief="solid", cursor="hand2")
        self.refresh_btn.place(x=cx+20, y=result_y+68, width=cw-40, height=44)

    def on_yen_change(self, *_):
        if self._updating:
            return
        raw = "".join(c for c in self.yen_var.get() if c.isdigit())
        formatted = f"{int(raw):,}".replace(",", " ") if raw else ""
        if formatted != self.yen_var.get():
            self._updating = True
            pos = self._yen_entry.index(tk.INSERT)
            self.yen_var.set(formatted)
            self._yen_entry.icursor(min(pos, len(formatted)))
            self._updating = False
        if self.rate and raw:
            rub = int(raw) * self.rate / 100
            self.rub_lbl.config(text=f"{rub:,.2f} ₽".replace(",", " "))
        else:
            self.rub_lbl.config(text="— ₽")

    def refresh(self):
        self.refresh_btn.config(state="disabled", text="Загрузка...")
        self.status_lbl.config(text="Обновление...", fg="#aaaaaa")
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            rate = get_jpy_rate()
            self.after(0, self._update_rate, rate)
        except Exception:
            self.after(0, self._show_error)

    def _update_rate(self, rate):
        self.rate = rate
        self.rate_lbl.config(text=f"{rate:.2f}")
        self.status_lbl.config(text="● Актуально", fg="#2e7d32")
        self.refresh_btn.config(state="normal", text="↻  Обновить курс")
        self.on_yen_change()

    def _show_error(self):
        self.rate_lbl.config(text="—")
        self.status_lbl.config(text="Не удалось получить курс", fg="#e65100")
        self.refresh_btn.config(state="normal", text="↻  Обновить курс")


if __name__ == "__main__":
    App().mainloop()
