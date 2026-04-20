import httpx
from bs4 import BeautifulSoup

ATB_URL = "https://atb.su/services/exchange/"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def get_jpy_buy_rate() -> float:
    """Return the JPY buy rate (покупка) from ATB Bank in RUB per 100 JPY."""
    response = httpx.get(ATB_URL, timeout=10, headers=_HEADERS, follow_redirects=True)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # The site uses a div-based layout (no <table>). Each currency row is:
    #   <div class="currency-table__tr">
    #     <div class="currency-table__td currency-table__td--tr-name">
    #       ...
    #       <div class="currency-table__val">JPY</div>
    #       ...
    #     </div>
    #     <div class="currency-table__td">       ← покупка (buy rate)
    #       <div class="currency-table__head">покупка</div>
    #       46.22                                ← direct text node
    #     </div>
    #     <div class="currency-table__td">       ← продажа (sell rate)
    #       ...
    #     </div>
    #   </div>

    for name_td in soup.find_all("div", class_="currency-table__td--tr-name"):
        val_div = name_td.find("div", class_="currency-table__val")
        if val_div and val_div.get_text(strip=True).upper() == "JPY":
            # Found the JPY row — its parent is currency-table__tr
            row = name_td.parent
            tds = row.find_all("div", class_="currency-table__td")
            # tds[0] = currency name, tds[1] = покупка (bank buys), tds[2] = продажа (bank sells = we buy)
            if len(tds) >= 3:
                sell_td = tds[2]
                # The rate is a direct text node (not inside a child element)
                raw = sell_td.get_text(strip=True)
                # Remove the header text "продажа" from the beginning
                head = sell_td.find("div", class_="currency-table__head")
                if head:
                    raw = raw.replace(head.get_text(strip=True), "").strip()
                raw = raw.replace(",", ".").replace("\xa0", "").strip()
                return float(raw)

    raise ValueError("JPY rate not found")
