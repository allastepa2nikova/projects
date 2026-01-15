#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import csv
import json
import time
import urllib.parse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


DEFAULT_FIELDS = ["name", "price", "stock"]


def build_search_url(query: str, page: int) -> str:
    params = {
        "text": query,
        "page": page,
    }
    return f"https://www.ozon.ru/search/?{urllib.parse.urlencode(params)}"


def extract_items(data):
    if not isinstance(data, dict):
        return []
    if isinstance(data.get("items"), list):
        return data["items"]
    if isinstance(data.get("items"), dict) and isinstance(data["items"].get("items"), list):
        return data["items"]["items"]
    return []


def extract_price(item):
    price = item.get("price")
    if isinstance(price, dict):
        for key in ("current", "price", "value"):
            if price.get(key):
                return price[key]
    if price:
        return price
    for key in ("discountPrice", "finalPrice", "cardPrice"):
        if item.get(key):
            return item[key]
    return None


def extract_stock(item):
    for key in ("stock", "availability", "available", "inStock", "stockCount", "qty"):
        if key in item:
            return item[key]
    return None


def parse_search_results(driver, query: str, page_limit: int, wait_seconds: int):
    results = []
    for page in range(1, page_limit + 1):
        url = build_search_url(query, page)
        driver.get(url)
        WebDriverWait(driver, wait_seconds).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-widget="searchResultsV2"]'))
        )
        containers = driver.find_elements(By.CSS_SELECTOR, '[data-widget="searchResultsV2"]')
        page_items = []
        for container in containers:
            data_state = container.get_attribute("data-state")
            if not data_state:
                continue
            try:
                data = json.loads(data_state)
            except json.JSONDecodeError:
                continue
            page_items.extend(extract_items(data))
        if not page_items:
            break
        for item in page_items:
            results.append(
                {
                    "name": item.get("name") or item.get("title"),
                    "price": extract_price(item),
                    "stock": extract_stock(item),
                }
            )
        time.sleep(1)
    return results


def write_csv(output_path: str, rows, fields):
    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def parse_fields(value: str):
    fields = [field.strip() for field in value.split(",") if field.strip()]
    invalid = [field for field in fields if field not in DEFAULT_FIELDS]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"Unknown fields: {', '.join(invalid)}. Allowed: {', '.join(DEFAULT_FIELDS)}"
        )
    return fields


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Ozon search parser. Example: python ozon_parser.py --query 'ноутбук' "
            "--fields name,price --output results.csv"
        )
    )
    parser.add_argument("--query", required=True, help="Search query for ozon.ru")
    parser.add_argument(
        "--page-limit",
        type=int,
        default=1,
        help="How many result pages to parse",
    )
    parser.add_argument(
        "--fields",
        type=parse_fields,
        default=DEFAULT_FIELDS,
        help="Comma-separated fields to export (name,price,stock)",
    )
    parser.add_argument(
        "--output",
        default="ozon_results.csv",
        help="Output CSV file",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=15,
        help="Seconds to wait for page data to load",
    )
    args = parser.parse_args()

    driver = webdriver.Chrome()
    try:
        rows = parse_search_results(driver, args.query, args.page_limit, args.wait_seconds)
        write_csv(args.output, rows, args.fields)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
