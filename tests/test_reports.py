import pandas as pd

from src import reports, utils


def test_spending_by_category(tmp_path, monkeypatch):
    df = pd.DataFrame(
        {
            utils.DATE_COLUMN: pd.to_datetime(["2021-03-01", "2021-04-01", "2021-05-01"]),
            utils.AMOUNT_COLUMN: [-100.0, -200.0, 300.0],
            utils.CATEGORY_COLUMN: ["Супермаркеты", "Супермаркеты", "Супермаркеты"],
        }
    )

    # Переопределяем каталог для отчётов, чтобы не писать в реальный
    monkeypatch.setattr(reports, "REPORTS_DIR", tmp_path)

    result = reports.spending_by_category(df, "Супермаркеты", date="2021-05-15")

    # Должны попасть только операции за последние 3 месяца до 15.05.2021
    assert len(result) == 3


def test_spending_by_weekday(tmp_path, monkeypatch):
    df = pd.DataFrame(
        {
            utils.DATE_COLUMN: pd.to_datetime(["2021-05-03", "2021-05-04"]),  # пн, вт
            utils.AMOUNT_COLUMN: [-100.0, -200.0],
        }
    )

    monkeypatch.setattr(reports, "REPORTS_DIR", tmp_path)

    result = reports.spending_by_weekday(df, date="2021-05-10")

    assert not result.empty
    assert "weekday" in result.columns
    assert "average_spent" in result.columns


def test_spending_by_workday(tmp_path, monkeypatch):
    df = pd.DataFrame(
        {
            utils.DATE_COLUMN: pd.to_datetime(["2021-05-03", "2021-05-08"]),  # пн (рабочий), сб (выходной)
            utils.AMOUNT_COLUMN: [-100.0, -200.0],
        }
    )

    monkeypatch.setattr(reports, "REPORTS_DIR", tmp_path)

    result = reports.spending_by_workday(df, date="2021-05-10")

    assert not result.empty
    assert "is_workday" in result.columns
    assert set(result["is_workday"].unique()) == {True, False}
