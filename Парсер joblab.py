#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Скрипт для поиска вакансий на joblab.ru."""

from __future__ import annotations

import re
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

BASE_URL = "https://joblab.ru/search.php"
DEFAULT_EXCLUSIONS = (
    "гку фгу гб фб мбу мвд госу федера облас муп гау фау шве одежд продаж"
)
SEARCH_RESULTS_LINK = (
    "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/table[2]/tbody/tr/td[1]/p/span[5]/a"
)
RESULTS_CONTAINER_XPATH = (
    "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/table[4]/tbody/tr/td[1]/p"
)
FIRST_PAGE_NEXT_XPATH = (
    "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/table[4]/tbody/tr/td[1]/p/a"
)
OTHER_PAGE_NEXT_XPATH = (
    "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/table[4]/tbody/tr/td[1]/p/a[2]"
)
VACANCY_TITLE_XPATH = (
    "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/h1"
)
PHONE_REVEAL_XPATH = (
    "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/table[1]/tbody/tr[3]/td[2]/p/span/a"
)
EMAIL_REVEAL_XPATH = (
    "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/table[1]/tbody/tr[4]/td[2]/p/span/a"
)
DETAILS_TABLE_CLASS = "table-to-div"


@dataclass
class VacancyRecord:
    company: str
    contact_name: str
    phone: str
    email: str
    vacancy: str
    url: str
    city: str
    salary: str


@contextmanager
def create_driver() -> Iterable[webdriver.Chrome]:
    """Создает экземпляр ChromeDriver и корректно закрывает его."""

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        yield driver
    finally:
        driver.quit()


def load_input(path: Path) -> Sequence[tuple[str, str]]:
    """Считывает исходные данные из Excel."""

    frame = pd.read_excel(path, engine="openpyxl")
    return list(frame[["vacans", "zepe"]].itertuples(index=False, name=None))


def fill_search_form(
    driver: webdriver.Chrome,
    vacancy: str,
    salary: str,
    city: str | None,
    exclusions: str,
) -> None:
    """Заполняет форму поиска."""

    wait = WebDriverWait(driver, 10)
    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[2]/td[2]/p/input",
            )
        )
    )

    driver.find_element(
        By.XPATH,
        "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[2]/td[2]/p/input",
    ).clear()
    driver.find_element(
        By.XPATH,
        "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[2]/td[2]/p/input",
    ).send_keys(vacancy)

    exclusions_input = driver.find_element(
        By.XPATH,
        "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[4]/td[2]/p/input",
    )
    exclusions_input.clear()
    exclusions_input.send_keys(exclusions)

    salary_input = driver.find_element(
        By.XPATH,
        "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[11]/td[2]/p/input",
    )
    salary_input.clear()
    salary_input.send_keys(str(salary))

    if city:
        select = Select(
            driver.find_element(
                By.XPATH,
                "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[6]/td[2]/p/select",
            )
        )
        select.select_by_visible_text(city)

    for checkbox_xpath in (
        "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[16]/td[2]/p[1]/label/input",
        "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[16]/td[2]/p[3]/label/input",
        "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[16]/td[2]/p[2]/label/input",
    ):
        checkbox = driver.find_element(By.XPATH, checkbox_xpath)
        if not checkbox.is_selected():
            checkbox.click()

    driver.find_element(
        By.XPATH,
        "/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[19]/td[2]/p/input[3]",
    ).click()


def collect_search_urls(
    driver: webdriver.Chrome,
    vacancy: str,
    salary: str,
    city: str | None,
    exclusions: str,
) -> List[str]:
    """Возвращает список ссылок на вакансии для переданных параметров."""

    driver.get(BASE_URL)
    fill_search_form(driver, vacancy, salary, city, exclusions)

    wait = WebDriverWait(driver, 10)
    wait.until(EC.element_to_be_clickable((By.XPATH, SEARCH_RESULTS_LINK))).click()
    wait.until(EC.presence_of_element_located((By.XPATH, RESULTS_CONTAINER_XPATH)))

    urls: List[str] = []
    page = 1

    while True:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.find_all("p", class_="prof")
        for card in cards:
            anchor = card.find("a", target="_blank")
            if anchor and anchor.has_attr("href"):
                urls.append("https://joblab.ru" + anchor["href"])

        try:
            next_xpath = FIRST_PAGE_NEXT_XPATH if page == 1 else OTHER_PAGE_NEXT_XPATH
            next_button = driver.find_element(By.XPATH, next_xpath)
        except NoSuchElementException:
            break

        container = driver.find_element(By.XPATH, RESULTS_CONTAINER_XPATH)
        next_button.click()
        try:
            wait.until(EC.staleness_of(container))
        except TimeoutException:
            break
        wait.until(EC.presence_of_element_located((By.XPATH, RESULTS_CONTAINER_XPATH)))
        page += 1

    return urls


def format_phone_numbers(raw: str) -> str:
    """Форматирует телефоны к единому виду."""

    numbers: List[str] = []
    for part in raw.split(","):
        digits = re.sub(r"\D", "", part)
        if not digits:
            continue
        if digits.startswith("8"):
            digits = "7" + digits[1:]
        elif not digits.startswith("7"):
            digits = "7" + digits
        digits = "+" + digits
        if len(digits) >= 12:
            formatted = f"{digits[:2]}({digits[2:5]}){digits[5:8]}-{digits[8:10]}-{digits[10:12]}"
        else:
            formatted = digits
        numbers.append(formatted)
    return ", ".join(numbers) if numbers else "Нет инфо"


def parse_vacancy_page(html: str, url: str, vacancy_name: str) -> VacancyRecord:
    """Извлекает данные о вакансии из HTML."""

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_=DETAILS_TABLE_CLASS)
    data = {
        "company": "Нет инфо",
        "contact_name": "Нет инфо",
        "phone": "Нет инфо",
        "email": "Нет инфо",
        "city": "Нет инфо",
        "salary": "Нет инфо",
    }

    if table:
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(" ", strip=True)

            if "Прямой работодатель" in label:
                data["company"] = value.replace('"', "").strip()
            elif "Контактное лицо" in label:
                data["contact_name"] = value
            elif "Телефон" in label:
                data["phone"] = format_phone_numbers(value)
            elif "E-mail" in label:
                data["email"] = value or "Нет инфо"
            elif "Город" in label:
                data["city"] = value.replace("   –   на карте", "").split(",")[0]
            elif "Заработная плата" in label:
                data["salary"] = value.replace(" руб.", " RUR")

    return VacancyRecord(
        company=data["company"],
        contact_name=data["contact_name"],
        phone=data["phone"],
        email=data["email"],
        vacancy=vacancy_name,
        url=url,
        city=data["city"],
        salary=data["salary"],
    )


def fetch_vacancy_details(driver: webdriver.Chrome, url: str) -> VacancyRecord:
    """Переходит по ссылке и собирает информацию о вакансии."""

    wait = WebDriverWait(driver, 10)
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.XPATH, VACANCY_TITLE_XPATH)))
    vacancy_name = driver.find_element(By.XPATH, VACANCY_TITLE_XPATH).text

    for xpath in (PHONE_REVEAL_XPATH, EMAIL_REVEAL_XPATH):
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
        except (NoSuchElementException, TimeoutException):
            continue

    wait.until(EC.presence_of_element_located((By.CLASS_NAME, DETAILS_TABLE_CLASS)))
    return parse_vacancy_page(driver.page_source, url, vacancy_name)


def collect_vacancies(urls: Sequence[str]) -> List[VacancyRecord]:
    """Загружает страницы вакансий и собирает информацию по каждой из них."""

    records: List[VacancyRecord] = []
    with create_driver() as driver:
        for url in urls:
            try:
                records.append(fetch_vacancy_details(driver, url))
            except TimeoutException:
                continue
    return records


def write_to_excel(records: Sequence[VacancyRecord], output_path: Path) -> None:
    """Сохраняет собранные данные в Excel."""

    if not records:
        return

    df = pd.DataFrame([record.__dict__ for record in records])
    df.rename(
        columns={
            "company": "Компания",
            "contact_name": "ФИО",
            "phone": "Телефон",
            "email": "E-mail",
            "vacancy": "Вакансия",
            "url": "Ссылка",
            "city": "Город",
            "salary": "Заработная плата",
        },
        inplace=True,
    )

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Sheet", index=False)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    input_path = base_dir / "Poisk.xlsx"
    output_path = base_dir / "vac.xlsx"

    search_params = load_input(input_path)

    urls: List[str] = []
    with create_driver() as driver:
        for vacancy, salary in search_params:
            urls.extend(
                collect_search_urls(driver, vacancy, salary, city=None, exclusions=DEFAULT_EXCLUSIONS)
            )
            urls.extend(
                collect_search_urls(
                    driver,
                    vacancy,
                    salary,
                    city="Санкт-Петербург и область",
                    exclusions=DEFAULT_EXCLUSIONS,
                )
            )

    records = collect_vacancies(urls)
    write_to_excel(records, output_path)


if __name__ == "__main__":
    main()
