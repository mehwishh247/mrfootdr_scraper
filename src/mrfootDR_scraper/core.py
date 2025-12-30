import logging
import pprint
import asyncio
import re
import csv
from typing import Any

from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from datetime import datetime, timezone

from pydoll.browser import Chrome

BASE_URL = "https://www.myfootdr.com.au"

async def fetch_clinic_data(url: str, browser: Chrome) -> dict[str, str | None]:
    tab = await browser.new_tab()
    await tab.go_to(url)
    await asyncio.sleep(0.3)

    data = {}

    meta = await tab.find(
        tag_name="div",
        class_name="clinic-metabox",
        raise_exc=False
    )

    name = await meta.find(
        tag_name="img",
        raise_exc=False
    )
    data["Name of Clinic"] = name.get_attribute("title") if name else None

    phone = await meta.find(
        tag_name="a",
        raise_exc=False
    )

    data["Phone"] = (await phone.text).lstrip("Call ") if phone else None

    address = await meta.find(
        tag_name="div",
        class_name="address",
        raise_exc=False
    )
    data["Address"] = (await address.text).strip() if address else None

    raw_text = meta.inner_html()
    email = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', raw_text)
    data["Email"] = match.group(0) if email else None

    service_container = await tab.find(
        tag_name="div",
        class_name="clinic-2020-services"
    )

    services_list = await service_container.find(
        tag_name="img",
        find_all=True
    )
    services = []

    for service in services_list:
        services.append(await service.get_attribute("alt"))

    data["Services"] = str(services)[1:-1]

    return data


async def get_region_data(url: str, browser: Chrome) -> list[dict[str, str]]:
    data = []

    tab = await browser.new_tab()
    await tab.go_to(url)
    await asyncio.sleep(0.5)

    clinic_urls = await tab.find(
        tag_name="a",
        class_name="feature-button has-bg table-cell featured-post-content pos-relative",
        find_all=True,
        raise_exc=False
    )

    for clinic in clinic_urls:
        link = clinic.get_attribute("href")
        clinic_details = await fetch_clinic_data(url=link, browser=browser)
        data.append(clinic_details)

        print(clinic_details)

    return data

        
async def run_scraper():
    try:
        logging.info("Crawler starting.")

        chromium_options = ChromiumOptions()
        chromium_options.add_argument("--lang=en-US")
        chromium_options.add_argument("--accept-lang=en-US,en;q=0.9")
        chromium_options.binary_location = "/snap/bin/chromium"

        data = []

        async with Chrome(options=chromium_options) as browser:
            tab = await browser.start()
            await tab.go_to(f"{BASE_URL}/our-clinics")
            await asyncio.sleep(0.5)

            region_container = await tab.find(
                tag_name="div",
                class_name="featured-posts",
                raise_exc=False
            )

            if not region_container:
                logging.error("Cannot find region container")
                return
            
            regions = await region_container.find(
                tag_name="article",
                class_name="hentry",
                find_all=True,
                raise_exc=False
            )

            for region in regions:
                url = BASE_URL + region.get_attribute("data-href")
                region_data = await get_region_data(url, browser=browser)
                data.extend(region_data)

        fieldnames = ["Name of Clinic", "Address", "Email", "Phone", "Services"]
        with open("mr_foot_dr.csv", "w+") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(data)

    except Exception as e:
        logging.exception(e)
        raise

# asyncio.run(run_scraper())
