from unittest.mock import patch, MagicMock
import pytest
from parser import get_jpy_buy_rate

# The real ATB site uses div-based layout (not a <table>).
# Structure per currency row:
#   <div class="currency-table__tr">
#     <div class="currency-table__td currency-table__td--tr-name">
#       <div class="currency-table__head">валюта</div>
#       <div class="currency-table__content">
#         <div class="currency-table__val">JPY</div>
#         <span class="currency-table__label">за 100¥</span>
#       </div>
#     </div>
#     <div class="currency-table__td">
#       <div class="currency-table__head">покупка</div>
#       46.22          ← direct text node (buy rate per 100 yen)
#     </div>
#     <div class="currency-table__td">
#       <div class="currency-table__head">продажа</div>
#       51.5
#     </div>
#   </div>
#
# get_jpy_buy_rate() returns the buy rate as a float (RUB per 100 JPY).

FAKE_HTML = """
<html><body>
<div class="currency-table__tr">
  <div class="currency-table__td currency-table__td--tr-name">
    <div class="currency-table__head">валюта</div>
    <div class="currency-table__content">
      <div class="currency-table__val">USD</div>
      <span class="currency-table__label">за 1$</span>
    </div>
  </div>
  <div class="currency-table__td">
    <div class="currency-table__head">покупка</div>
    85.50
  </div>
  <div class="currency-table__td">
    <div class="currency-table__head">продажа</div>
    87.00
  </div>
</div>
<div class="currency-table__tr">
  <div class="currency-table__td currency-table__td--tr-name">
    <div class="currency-table__head">валюта</div>
    <div class="currency-table__content">
      <div class="currency-table__val">JPY</div>
      <span class="currency-table__label">за 100¥</span>
    </div>
  </div>
  <div class="currency-table__td">
    <div class="currency-table__head">покупка</div>
    46.22
  </div>
  <div class="currency-table__td">
    <div class="currency-table__head">продажа</div>
    51.5
  </div>
</div>
<div class="currency-table__tr">
  <div class="currency-table__td currency-table__td--tr-name">
    <div class="currency-table__head">валюта</div>
    <div class="currency-table__content">
      <div class="currency-table__val">EUR</div>
      <span class="currency-table__label">за 1€</span>
    </div>
  </div>
  <div class="currency-table__td">
    <div class="currency-table__head">покупка</div>
    92.10
  </div>
  <div class="currency-table__td">
    <div class="currency-table__head">продажа</div>
    94.00
  </div>
</div>
</body></html>
"""


def test_get_jpy_buy_rate_returns_float():
    with patch("parser.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = FAKE_HTML
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        rate = get_jpy_buy_rate()
    assert isinstance(rate, float)
    assert rate == 46.22


def test_get_jpy_buy_rate_raises_if_not_found():
    with patch("parser.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "<html><body><div>no currency data here</div></body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        with pytest.raises(ValueError, match="JPY rate not found"):
            get_jpy_buy_rate()
