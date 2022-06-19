# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem

WEEKDAYS = {
    "Mo": "Mo",
    "Di": "Tu",
    "Mi": "We",
    "Do": "Th",
    "Fr": "Fr",
    "Sa": "Sa",
    "So": "Su",
}


class AldiLUSpider(scrapy.Spider):
    name = "aldi_lu"
    item_attributes = {"brand": "Aldi"}
    allowed_domains = ["de.aldi.lu"]
    start_urls = ("https://de.aldi.lu/filialen/index/page-1",)

    def parse(self, response):
        stores = response.css(".filtable isloop")
        next = response.css(".filiale .main .row3 a::attr(href)")
        for store in stores:
            data = store.css("tr .td1 .box1")
            website = (
                "https://de.aldi.lu" + data.css("a::attr(href)").extract_first()[1:]
            )
            ref = website.split("/")[-2]
            data = data.css("::text").extract()
            name = data[1]
            street = data[2]
            zipcode, city = re.search(r"(\d+) (.*)", data[3]).groups()
            hours_data = store.css(".openhrs")[0]

            properties = {
                "ref": ref,
                "name": name.strip(),
                "website": website,
                "street": street.strip(),
                "city": city.strip(),
                "postcode": zipcode.strip(),
                "opening_hours": self.hours(hours_data),
            }

            yield GeojsonPointItem(**properties)

        if next:
            yield scrapy.Request(
                "https://de.aldi.lu" + next.extract_first()[1:], callback=self.parse
            )

    def hours(self, data):
        opening_hours = ""
        for item in data.css("tr"):
            item_data = item.css("td::text").extract()
            opening_hours = opening_hours + "{} {}; ".format(
                WEEKDAYS[item_data[0][:2]], item_data[1]
            )

        return opening_hours
