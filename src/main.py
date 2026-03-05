from __future__ import annotations

from pprint import pprint

from src import services, views


def demo_main_page() -> None:
    """Продемонстрировать JSON-ответ для страницы «Главная»."""
    context = views.build_main_page_context("2021-12-20 12:00:00")
    pprint(context)


def demo_events_page() -> None:
    """Продемонстрировать JSON-ответ для страницы «События»."""
    context = views.build_events_page_context("2021-12-20", period="M")
    pprint(context)


def demo_services() -> None:
    """Продемонстрировать работу сервисных функций на небольшом наборе данных."""
    sample_tx = [
        {
            services.DATE_KEY: "2021-12-10",
            services.AMOUNT_KEY: -1712.0,
            services.CATEGORY_KEY: "Супермаркеты",
            services.DESCRIPTION_KEY: "Покупка в супермаркете",
        },
        {
            services.DATE_KEY: "2021-12-11",
            services.AMOUNT_KEY: -200.0,
            services.CATEGORY_KEY: "Переводы",
            services.DESCRIPTION_KEY: "Валерий А.",
        },
    ]

    pprint(services.profitable_categories(sample_tx, 2021, 12))
    pprint(services.investment_bank("2021-12", sample_tx, limit=50))
    pprint(services.simple_search(sample_tx, "супермаркет"))
    pprint(services.find_phone_transactions(sample_tx))
    pprint(services.find_person_transfers(sample_tx))


if __name__ == "__main__":
    demo_main_page()
    demo_events_page()
    demo_services()
