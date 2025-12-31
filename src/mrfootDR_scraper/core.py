import logging
import pprint
import asyncio
import re
import csv
import json
from urllib.parse import unquote

from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import By

from pydoll.browser import Chrome

BASE_URL = "https://web.archive.org/web/20250707233946/https://www.myfootdr.com.au"

async def fetch_clinic_data(url: str, browser: Chrome) -> dict[str, str | None]:
    tab = await browser.new_tab()
    await tab.go_to(url)
    await asyncio.sleep(0.3)
    data = {}

    json_lds = await tab.query("//script[@type='application/ld+json']", find_all=True)

    for json_ld in json_lds:
        tag = json_ld.tag_name
        if tag != "script":
            continue
            
        json_text = await json_ld.inner_html

        if f"LocalBusiness" not in json_text:
            continue

        clinic = json.loads(json_text.lstrip("<script type=\"application/ld+json\">\n").rstrip("\n</script>"))

        data["Name"] = clinic.get("name", "")
        data["Phone"] = clinic.get("telephone", "")
        data["Email"] = clinic.get("email", "")

        address = ""
        addr = clinic.get("address")
        if isinstance(addr, dict):
            address = ", ".join(filter(None, [
                addr.get("streetAddress"),
                addr.get("addressLocality"),
                addr.get("addressRegion"),
                addr.get("postalCode"),
                addr.get("addressCountry"),
            ]))

        data["Address"] = address

        service_list = []
        offers = clinic.get("makesOffer")

        if isinstance(offers, list):
            for offer in offers:
                url = (offer or {}).get("url", "")
                if not url:
                    continue

                # extract last path segment
                split_name = url.split("/")[-2]
                slug = unquote(split_name)

                if slug.lower() in {"resources"}:
                    continue

                title = slug.replace("-", " ").title()
                title = title.replace("Ndis", "NDIS").replace("Smos", "SMOs")
                service_list.append(title)

        data["Services"] = str(service_list)[1:-1].replace("'","") if service_list else ""

    await tab.close()

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
        if not clinic_details:
            continue

        data.append(clinic_details)

    await tab.close()

    return data

        
async def run_scraper():
    try:
        logging.info("Crawler starting.")

        chromium_options = ChromiumOptions()
        chromium_options.add_argument("--lang=en-US")
        chromium_options.add_argument("--accept-lang=en-US,en;q=0.9")
        chromium_options.headless = True
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

            await tab.close()

        fieldnames = ["Name of Clinic", "Address", "Email", "Phone", "Services"]
        with open("mrfoot_dr.json", "w+") as json_file:
            json.dump(data, json_file, indent=1)

    except Exception as e:
        logging.exception(e)
        raise

asyncio.run(run_scraper())
