import sys
import os
import tkinter as tk
import threading
import httpx
from bs4 import BeautifulSoup
from PIL import Image, ImageTk

ATB_URL = "https://atb.su/services/exchange/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

W, H = 800, 520
CARD_W, CARD_H = 340, 480
CARD_X = (W - CARD_W) // 2
CARD_Y = (H - CARD_H) // 2
CARD_R = 16  # border radius approximation


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


def build_bg(w, h, cx, cy, cw, ch):
    src = Image.open(resource_path("bg.jpg")).convert("RGB")
    scale = max(w / src.width, h / src.height)
    nw, nh = int(src.width * scale), int(src.height * scale)
    src = src.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    bg = src.crop((left, top, left + w, top + h))
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    card = Image.new("RGBA", (cw, ch), (255, 255, 255, 140))
    overlay.paste(card, (cx, cy))
    result = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    return ImageTk.PhotoImage(result)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Курс иены — АТБ")
        self.geometry(f"{W}x{H}")
        self.resizable(False, False)
        self.rate = None
        self._updating = False

        self.canvas = tk.Canvas(self, width=W, height=H, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        try:
            self._photo = build_bg(W, H, CARD_X, CARD_Y, CARD_W, CARD_H)
            self.canvas.create_image(0, 0, anchor="nw", image=self._photo)
        except Exception as e:
            print(f"bg error: {e}")
            self.canvas.configure(bg="#f0f2f5")

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        mid = W // 2
        y = CARD_Y + 24

        # Bank name
        self.canvas.create_text(mid, y, text="АТБ БАНК",
                                font=("Helvetica", 10), fill="#888888", anchor="n")
        y += 26

        # Title
        self.canvas.create_text(mid, y, text="Курс покупки иены",
                                font=("Helvetica", 15, "bold"), fill="#1a1a1a", anchor="n")
        y += 30

        # Currency pair
        self.canvas.create_text(mid, y, text="JPY → RUB",
                                font=("Helvetica", 11), fill="#aaaaaa", anchor="n")
        y += 26

        # Rate
        self._rate_t = self.canvas.create_text(mid, y, text="...",
                                               font=("Helvetica", 52, "bold"),
                                               fill="#1a1a1a", anchor="n")
        y += 72

        # Unit
        self.canvas.create_text(mid, y, text="рублей за 100 ¥",
                                font=("Helvetica", 13), fill="#555555", anchor="n")
        y += 24

        # Status
        self._status_t = self.canvas.create_text(mid, y, text="Загрузка...",
                                                  font=("Helvetica", 10),
                                                  fill="#aaaaaa", anchor="n")
        y += 24

        # Divider
        self.canvas.create_line(CARD_X + 20, y, CARD_X + CARD_W - 20, y,
                                fill="#dddddd", width=1)
        y += 14

        # Converter label
        self.canvas.create_text(mid, y, text="КОНВЕРТЕР",
                                font=("Helvetica", 9), fill="#aaaaaa", anchor="n")
        y += 18

        # Yen entry
        self.yen_var = tk.StringVar()
        self.yen_var.trace("w", self.on_yen_change)
        self._yen_entry = tk.Entry(self.canvas, textvariable=self.yen_var,
                                   font=("Helvetica", 18, "bold"),
                                   bd=1, relief="solid", fg="#1a1a1a",
                                   justify="right", bg="white")
        self.canvas.create_window(mid, y + 20, window=self._yen_entry,
                                  width=CARD_W - 30, height=42)
        self.canvas.create_text(CARD_X + CARD_W - 24, y + 20, text="¥",
                                font=("Helvetica", 14), fill="#aaaaaa", anchor="center")
        y += 54

        # Result box
        self.canvas.create_rectangle(CARD_X + 15, y, CARD_X + CARD_W - 15, y + 46,
                                     fill="#1a1a1a", outline="", )
        self.canvas.create_text(CARD_X + 30, y + 23, text="Рублей",
                                font=("Helvetica", 11), fill="#888888", anchor="w")
        self._rub_t = self.canvas.create_text(CARD_X + CARD_W - 26, y + 23,
                                               text="— ₽",
                                               font=("Helvetica", 18, "bold"),
                                               fill="white", anchor="e")
        y += 58

        # Refresh button
        self.refresh_btn = tk.Button(self.canvas, text="↻  Обновить курс",
                                     command=self.refresh, bg="white", fg="#555555",
                                     font=("Helvetica", 11), bd=1, relief="solid",
                                     cursor="hand2", activebackground="#f0f0f0")
        self.canvas.create_window(mid, y + 18, window=self.refresh_btn,
                                  width=CARD_W - 30, height=38)

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
            self.canvas.itemconfig(self._rub_t, text=f"{rub:,.2f} ₽".replace(",", " "))
        else:
            self.canvas.itemconfig(self._rub_t, text="— ₽")

    def refresh(self):
        self.refresh_btn.config(state="disabled", text="Загрузка...")
        self.canvas.itemconfig(self._status_t, text="Обновление...", fill="#aaaaaa")
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            rate = get_jpy_rate()
            self.after(0, self._update_rate, rate)
        except Exception:
            self.after(0, self._show_error)

    def _update_rate(self, rate):
        self.rate = rate
        self.canvas.itemconfig(self._rate_t, text=f"{rate:.2f}")
        self.canvas.itemconfig(self._status_t, text="● Актуально", fill="#2e7d32")
        self.refresh_btn.config(state="normal", text="↻  Обновить курс")
        self.on_yen_change()

    def _show_error(self):
        self.canvas.itemconfig(self._rate_t, text="—")
        self.canvas.itemconfig(self._status_t,
                               text="Не удалось получить курс", fill="#e65100")
        self.refresh_btn.config(state="normal", text="↻  Обновить курс")


if __name__ == "__main__":
    App().mainloop()
