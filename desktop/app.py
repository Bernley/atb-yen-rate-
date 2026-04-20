import tkinter as tk
from tkinter import font as tkfont
import httpx
from bs4 import BeautifulSoup
import threading

ATB_URL = "https://atb.su/services/exchange/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}


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


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Курс иены — АТБ")
        self.geometry("360x480")
        self.resizable(False, False)
        self.configure(bg="#f0f2f5")

        self.rate = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Bank name
        tk.Label(self, text="АТБ БАНК", bg="#f0f2f5", fg="#888888",
                 font=("Helvetica", 10, "normal"), letter_spacing=2).pack(pady=(40, 4))

        tk.Label(self, text="Курс покупки иены", bg="#f0f2f5", fg="#333333",
                 font=("Helvetica", 16, "bold")).pack(pady=(0, 6))

        tk.Label(self, text="JPY → RUB", bg="#f0f2f5", fg="#aaaaaa",
                 font=("Helvetica", 11)).pack()

        self.rate_label = tk.Label(self, text="...", bg="#f0f2f5", fg="#1a1a1a",
                                   font=("Helvetica", 56, "bold"))
        self.rate_label.pack(pady=(4, 0))

        tk.Label(self, text="рублей за 100 ¥", bg="#f0f2f5", fg="#555555",
                 font=("Helvetica", 13)).pack(pady=(0, 12))

        self.status_label = tk.Label(self, text="Загрузка...", bg="#f0f2f5", fg="#aaaaaa",
                                     font=("Helvetica", 10))
        self.status_label.pack()

        # Divider
        tk.Frame(self, bg="#e0e0e0", height=1).pack(fill="x", padx=30, pady=16)

        # Converter
        tk.Label(self, text="КОНВЕРТЕР", bg="#f0f2f5", fg="#aaaaaa",
                 font=("Helvetica", 9)).pack()

        frame = tk.Frame(self, bg="#f0f2f5")
        frame.pack(pady=8, padx=30, fill="x")

        self.yen_var = tk.StringVar()
        self.yen_var.trace("w", self.on_yen_change)
        yen_entry = tk.Entry(frame, textvariable=self.yen_var, font=("Helvetica", 18, "bold"),
                             bd=1, relief="solid", fg="#1a1a1a", justify="right")
        yen_entry.pack(fill="x", ipady=8)

        tk.Label(self, text="¥  →", bg="#f0f2f5", fg="#aaaaaa",
                 font=("Helvetica", 12)).pack()

        self.rub_label = tk.Label(self, text="— ₽", bg="#1a1a1a", fg="white",
                                   font=("Helvetica", 22, "bold"), pady=10, padx=20)
        self.rub_label.pack(padx=30, fill="x")

        # Refresh button
        self.refresh_btn = tk.Button(self, text="↻  Обновить курс", command=self.refresh,
                                     bg="white", fg="#555555", font=("Helvetica", 12),
                                     bd=1, relief="solid", cursor="hand2", pady=8)
        self.refresh_btn.pack(padx=30, pady=16, fill="x")

    def on_yen_change(self, *_):
        if self.rate is None:
            return
        try:
            yen = float(self.yen_var.get().replace(" ", "").replace(",", ".") or 0)
            rub = yen * self.rate / 100
            self.rub_label.config(text=f"{rub:,.2f} ₽".replace(",", " "))
        except ValueError:
            self.rub_label.config(text="— ₽")

    def refresh(self):
        self.refresh_btn.config(state="disabled", text="Загрузка...")
        self.status_label.config(text="Обновление...")
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            rate = get_jpy_rate()
            self.after(0, self._update_rate, rate)
        except Exception as e:
            self.after(0, self._show_error, str(e))

    def _update_rate(self, rate):
        self.rate = rate
        self.rate_label.config(text=f"{rate:.2f}")
        self.status_label.config(text="● Актуально", fg="#2e7d32")
        self.refresh_btn.config(state="normal", text="↻  Обновить курс")
        self.on_yen_change()

    def _show_error(self, msg):
        self.rate_label.config(text="—")
        self.status_label.config(text="Не удалось получить курс", fg="#e65100")
        self.refresh_btn.config(state="normal", text="↻  Обновить курс")


if __name__ == "__main__":
    App().mainloop()
