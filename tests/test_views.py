from unittest import mock

import pandas as pd

from src import utils, views


class DummySettings:
    def __init__(self, currencies, stocks):
        self.currencies = currencies
        self.stocks = stocks


def test_build_main_page_context(monkeypatch):
    df = pd.DataFrame(
        {
            utils.DATE_COLUMN: pd.to_datetime(["2021-12-10"]),
            utils.AMOUNT_COLUMN: [-100.0],
            utils.CARD_COLUMN: ["1111222233334444"],
            utils.CATEGORY_COLUMN: ["Супермаркеты"],
            utils.DESCRIPTION_COLUMN: ["Покупка"],
        }
    )

    def fake_load_ops():
        return df

    def fake_filter(df_arg, dt, period="M"):
        return df_arg

    def fake_load_settings():
        return DummySettings(["USD"], ["AAPL"])

    monkeypatch.setattr(utils, "load_operations", fake_load_ops)
    monkeypatch.setattr(utils, "filter_by_period", fake_filter)
    monkeypatch.setattr(utils, "load_user_settings", fake_load_settings)

    with mock.patch("src.utils.get_currency_rates", return_value=[{"currency": "USD", "rate": 70.0}]):
        with mock.patch("src.utils.get_stock_prices", return_value=[{"stock": "AAPL", "price": 150.0}]):
            context = views.build_main_page_context("2021-12-15 12:00:00")

    assert context["greeting"] == "Добрый день"
    assert len(context["cards"]) == 1
    assert len(context["top_transactions"]) == 1
    assert context["currency_rates"][0]["currency"] == "USD"
    assert context["stock_prices"][0]["stock"] == "AAPL"


def test_build_events_page_context(monkeypatch):
    df = pd.DataFrame(
        {
            utils.DATE_COLUMN: pd.to_datetime(["2021-12-10", "2021-12-11"]),
            utils.AMOUNT_COLUMN: [-100.0, 200.0],
            utils.CATEGORY_COLUMN: ["Супермаркеты", "Пополнение_BANK007"],
            utils.DESCRIPTION_COLUMN: ["Покупка", "Пополнение"],
        }
    )

    def fake_load_ops():
        return df

    def fake_filter(df_arg, dt, period="M"):
        return df_arg

    def fake_load_settings():
        return DummySettings(["USD"], ["AAPL"])

    monkeypatch.setattr(utils, "load_operations", fake_load_ops)
    monkeypatch.setattr(utils, "filter_by_period", fake_filter)
    monkeypatch.setattr(utils, "load_user_settings", fake_load_settings)

    with mock.patch("src.utils.get_currency_rates", return_value=[{"currency": "USD", "rate": 70.0}]):
        with mock.patch("src.utils.get_stock_prices", return_value=[{"stock": "AAPL", "price": 150.0}]):
            context = views.build_events_page_context("2021-12-15", period="M")

    assert "expenses" in context
    assert "income" in context
    assert context["expenses"]["total_amount"] == 100
    assert context["income"]["total_amount"] == 200
    assert context["currency_rates"][0]["currency"] == "USD"
    assert context["stock_prices"][0]["stock"] == "AAPL"
