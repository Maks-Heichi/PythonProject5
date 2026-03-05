from datetime import datetime

import pandas as pd
import pytest

from src import utils


@pytest.mark.parametrize(
    "hour, expected",
    [
        (8, "Доброе утро"),
        (13, "Добрый день"),
        (19, "Добрый вечер"),
        (2, "Доброй ночи"),
    ],
)
def test_get_greeting_variants(hour, expected):
    dt = datetime(2021, 1, 1, hour, 0, 0)
    assert utils.get_greeting(dt) == expected


@pytest.fixture
def df_for_period() -> pd.DataFrame:
    dates = pd.to_datetime(
        [
            "2021-05-01",
            "2021-05-15",
            "2021-05-31",
            "2021-06-01",
        ]
    )
    return pd.DataFrame({utils.DATE_COLUMN: dates, utils.AMOUNT_COLUMN: [1, 2, 3, 4]})


def test_filter_by_period_month(df_for_period: pd.DataFrame) -> None:
    end = datetime(2021, 5, 20)
    result = utils.filter_by_period(df_for_period, end, "M")
    assert result[utils.DATE_COLUMN].min() == datetime(2021, 5, 1)
    assert result[utils.DATE_COLUMN].max() == datetime(2021, 5, 20)


def test_filter_by_period_all(df_for_period: pd.DataFrame) -> None:
    end = datetime(2021, 5, 20)
    result = utils.filter_by_period(df_for_period, end, "ALL")
    assert len(result) == 3  # до 20 мая включительно


def test_summarize_cards() -> None:
    df = pd.DataFrame(
        {
            utils.CARD_COLUMN: ["1111222233334444", "5555666677778888"],
            utils.AMOUNT_COLUMN: [-100.0, -200.0],
        }
    )
    cards = utils.summarize_cards(df)
    assert len(cards) == 2
    last_digits = {c["last_digits"] for c in cards}
    assert last_digits == {"4444", "8888"}


def test_top_transactions() -> None:
    df = pd.DataFrame(
        {
            utils.DATE_COLUMN: pd.to_datetime(["2021-01-01", "2021-01-02"]),
            utils.AMOUNT_COLUMN: [10.0, -50.0],
            utils.CATEGORY_COLUMN: ["A", "B"],
            utils.DESCRIPTION_COLUMN: ["desc1", "desc2"],
        }
    )
    top = utils.top_transactions(df, n=1)
    assert len(top) == 1
    assert top[0]["amount"] == -50.0
    assert top[0]["category"] == "B"
