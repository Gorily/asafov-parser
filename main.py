import dataclasses
import re
import csv

import requests
from lxml import etree

html_parser = etree.HTMLParser()


@dataclasses.dataclass
class Candidate:
    name: str
    area: str
    political_party: str


def extract_candidates(link):
    area_tree = etree.fromstring(requests.get(link).text, html_parser)
    area_name = area_tree.xpath('//h1/span')[0].text
    candidates = area_tree.xpath('//div[contains(@class,"td-module-container")]')

    results = []
    for candidate in candidates:
        name = candidate.xpath('.//h3//a')[0].text
        political_party = candidate.xpath('.//div[contains(@class,"td-post-content")]/a/text()')[0]
        results.append(Candidate(name=name, area=area_name, political_party=political_party))
    return results


def parse(main_page):
    main_source = requests.get(main_page).text
    main_tree = etree.fromstring(main_source, html_parser)

    links = []

    # Извлекаем все дочерние ссылки со страницы
    if not main_page.endswith('/'):
        main_page = main_page + '/'

    page_links = main_tree.xpath(f'//a[contains(@href, "{main_page}")]')
    links.extend([link.attrib['href'] for link in page_links])

    # Извлекаем из файла кеша ссылки на районы
    js_link = main_tree.xpath('//script[contains(@src, "ru_mow_newhtmlmap/static/cache/")]')
    js_source = requests.get(js_link[0].attrib['src']).text

    links.extend(re.findall(r'"link": "([^"]+)",', js_source))
    links = [link.replace("\\", "") for link in links]

    for link in links:
        if 'electoral_map' in link:
            continue

        for c in extract_candidates(link):
            yield c


if __name__ == '__main__':
    with open('results.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, dialect='excel')

        for row in parse("https://asafov.ru/edg2022/municipal"):
            writer.writerow([row.area, row.political_party, row.name])

