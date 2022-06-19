# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem


class ElysiumHealthcareSpider(scrapy.Spider):
    name = "elysium_healthcare"
    item_attributes = {"brand": "Elysium Healthcare", "brand_wikidata": "Q39086513"}
    allowed_domains = ["www.elysiumhealthcare.co.uk"]
    start_urls = [
        "https://www.elysiumhealthcare.co.uk/locations/",
    ]
    download_delay = 0.3

    def parse(self, response):
        urls = response.xpath(
            '//li[@class="elementor-icon-list-item"]/a/@href'
        ).extract()

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_location)

    def parse_location(self, response):
        coming_soon = response.xpath(
            '//h1[@class="elementor-heading-title elementor-size-default"]/span/text()'
        ).extract_first()
        clutter = ["or", "or ", "Email us", "Email us ", "\xa0", "or\xa0"]

        if not coming_soon:  # Skip empty pages
            ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
            name = response.xpath(
                '(//h1[@class="elementor-heading-title elementor-size-default"]/text())[2]'
            ).extract_first()
            unit_addr = response.xpath(
                '//div[contains(@class, "contact-link-small")]/div/p[not(a) and not(strong) and not(contains(text(), "Tel:"))]//text()'
            ).extract()
            if unit_addr:  # Incorporate unit/building identifier
                addr_first_line = response.xpath(
                    '//div[contains(@class, "contact-link-small")]/div/div/p/text()'
                ).extract_first()
                if not addr_first_line:
                    addr_first_line = "".join(
                        [x for x in unit_addr if x not in clutter]
                    )
                    addr_first_line = addr_first_line.replace("or\xa0Email us \xa0", "")
            else:  # No unit_addr, just first_line
                addr_first_line = response.xpath(
                    '//div[contains(@class, "contact-link-small")]/div/div/p/text()'
                ).extract_first()
            addr_last_line = response.xpath(
                '(//div[contains(@class, "contact-link-small")]//p[not(a) and not(strong)]/text())[2]'
            ).extract_first()
            if addr_first_line and addr_last_line:  # Address in two parts
                # Check for formatting common on Welsh pages
                welsh_ll_addr = response.xpath(
                    '(//div[contains(@class, "contact-link-small")]//p[not(a) and not(strong) and not(contains(text(), "Tel:"))]/text())[3]'
                ).extract_first()
                if addr_last_line not in addr_first_line:  # Check for overlap
                    if welsh_ll_addr:
                        addr_full = (
                            addr_first_line
                            + " "
                            + addr_last_line
                            + welsh_ll_addr.rstrip("or ")
                        )
                    else:
                        addr_full = addr_first_line + " " + addr_last_line
                else:  # if there is first_line last_line overlap
                    if addr_last_line in "".join(unit_addr):
                        addr_full = "".join([x for x in unit_addr if x not in clutter])
                    else:
                        addr_full = "".join(unit_addr) + addr_last_line
            else:  # Handle single line formatting
                addr_full = response.xpath(
                    '(//div[contains(@class, "contact-link-small")]//p/text())'
                ).extract_first()
            map_settings = response.xpath(
                '//div[contains(@id, "wpgmza_map")]/@data-settings'
            ).extract_first()
            if map_settings:
                map_data = json.loads(map_settings)
                lat = map_data["map_start_lat"]
                lon = map_data["map_start_lng"]
            else:  # No map available
                lat = ""
                lon = ""
            telephone = response.xpath(
                '//div[@class="darkbglink"]/p/a/text()'
            ).extract_first()
            if telephone:
                telephone.replace("Email us", "")

            properties = {
                "ref": ref,
                "name": name,
                "addr_full": addr_full.strip(),
                "country": "GB",
                "lat": lat,
                "lon": lon,
                "phone": telephone,
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)
