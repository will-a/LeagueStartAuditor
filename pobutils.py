import re
import zlib
import base64
import logging
import requests
from typing import Optional
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
BUILD_CODE_PATHS = {
    'pobb.in': 'https://pobb.in/:id:/raw',
    'pastebin.com': 'https://pastebin.com/raw/:id:'
}


def get_pob_code_from_url(url: str) -> Optional[str]:
    url_r = re.compile(r'(http(s)?:\/\/)?(www.)?(?P<url_base>\w+\.\w+)\/(?P<paste_id>\w+)')
    if not (url and (url_match := url_r.search(url))):
        return None
    url = BUILD_CODE_PATHS.get(url_match.group('url_base'), '').replace(':id:', url_match.group('paste_id'))
    if not url:
        return None
    resp = requests.get(url)
    if resp.status_code != 200:
        return None
    return resp.text


def read_pob_to_xml(pob_code: str) -> ET.Element:
    decoded = base64.urlsafe_b64decode(pob_code)
    decompressed = zlib.decompress(decoded)
    return ET.fromstring(decompressed)


def get_uniques_from_xml(root: ET.Element) -> list:
    items_xml = root.find('Items')
    unique = re.compile(r'^Rarity: UNIQUE\n(?P<item_name>[\w ]+)\n')
    
    return [unique_match.group('item_name') for item in items_xml if item.tag == 'Item' and (unique_match := unique.match(item.text.strip()))]


def get_uniques_from_pob_code(pob_code: str) -> list:
    pob_xml = read_pob_to_xml(pob_code)
    return get_uniques_from_xml(pob_xml)


# print(get_uniques_from_xml(read_pob_to_xml(get_pob_code_from_url('https://pobb.in/BL70qYjBEzI8'))))
