from src import services


def test_profitable_categories():
    data = [
        {
            services.DATE_KEY: "2021-05-10",
            services.AMOUNT_KEY: -1000.0,
            services.CATEGORY_KEY: "Супермаркеты",
        },
        {
            services.DATE_KEY: "2021-05-15",
            services.AMOUNT_KEY: -500.0,
            services.CATEGORY_KEY: "Супермаркеты",
        },
        {
            services.DATE_KEY: "2021-06-01",
            services.AMOUNT_KEY: -100.0,
            services.CATEGORY_KEY: "Фастфуд",
        },
    ]
    result = services.profitable_categories(data, 2021, 5)
    assert "Супермаркеты" in result
    assert result["Супермаркеты"] == 75.0  # 5% от 1500


def test_investment_bank():
    tx = [
        {services.DATE_KEY: "2021-05-10", services.AMOUNT_KEY: -1712.0},
        {services.DATE_KEY: "2021-05-11", services.AMOUNT_KEY: -10.0},
        {services.DATE_KEY: "2021-06-01", services.AMOUNT_KEY: -100.0},
    ]
    saved = services.investment_bank("2021-05", tx, limit=50)
    assert saved == 38.0 + 40.0


def test_simple_search():
    tx = [
        {services.DESCRIPTION_KEY: "Покупка в Ленте", services.CATEGORY_KEY: "Супермаркеты"},
        {services.DESCRIPTION_KEY: "ЖКУ Квартира", services.CATEGORY_KEY: "ЖКХ"},
    ]
    result = services.simple_search(tx, "лент")
    assert len(result["results"]) == 1
    assert result["results"][0][services.CATEGORY_KEY] == "Супермаркеты"


def test_find_phone_transactions():
    tx = [
        {services.DESCRIPTION_KEY: "Я МТС +7 921 11-22-33"},
        {services.DESCRIPTION_KEY: "Без телефона"},
    ]
    result = services.find_phone_transactions(tx)
    assert len(result["results"]) == 1
    assert "+7 921" in result["results"][0][services.DESCRIPTION_KEY]


def test_find_person_transfers():
    tx = [
        {
            services.CATEGORY_KEY: "Переводы",
            services.DESCRIPTION_KEY: "Валерий А.",
        },
        {
            services.CATEGORY_KEY: "Супермаркеты",
            services.DESCRIPTION_KEY: "Иван И.",
        },
    ]
    result = services.find_person_transfers(tx)
    assert len(result["results"]) == 1
    assert result["results"][0][services.DESCRIPTION_KEY] == "Валерий А."
