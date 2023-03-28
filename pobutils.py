import re
import zlib
import base64
import logging
import binascii
import requests
from typing import Optional
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
BUILD_CODE_PATHS = {
    'pobb.in': 'https://pobb.in/:id:/raw',
    'pastebin.com': 'https://pastebin.com/raw/:id:'
}
DISPLAY_STATS = [
    'AverageHit',
    'AverageDamage',
    'Speed',
    'CritChance',
    'CritMultiplier',
    'CombinedDPS',
    'Dex',
    'Int',
    'Str',
    'PowerChargesMax',
    'FrenzyChargesMax',
    'EnduranceChargesMax',
    'TotalEHP',
    'Life',
    'Armour',
    'EnergyShield',
    'Evasion',
    'FireResist',
    'ColdResist',
    'LightningResist',
    'ChaosResist',
    'SpellSuppressionChance'
]

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
    if not pob_code:
        return None
    try:
        decoded = base64.urlsafe_b64decode(pob_code)
        decompressed = zlib.decompress(decoded)
    except zlib.error:
        return None
    except binascii.Error:
        return None
    else:
        return ET.fromstring(decompressed)


def get_uniques_from_xml(root: ET.Element) -> list:
    items_xml = root.find('Items')
    if not items_xml:
        return []
    unique = re.compile(r'^Rarity: UNIQUE\n(?P<item_name>[\w \']+)\n')

    return [unique_match.group('item_name') for item in items_xml if item.tag == 'Item' and (unique_match := unique.match(item.text.strip()))]


def get_stats_from_xml(root: ET.Element) -> tuple:
    stats_root = root.find('Build')
    if not stats_root:
        return {}, {}
    character = {
        'level': stats_root.attrib['level'],
        'class': stats_root.attrib.get('ascendClassName', stats_root.attrib['className'])
    }
    display_stats = {}
    for stat in stats_root:
        if stat.tag != 'PlayerStat':
            if stat.tag == 'FullDPSSkill':
                if 'FullDPSSkill' not in character:
                    character['FullDPSSkill'] = []
                character['FullDPSSkill'].append((stat.attrib['stat'], float(stat.attrib['value'])))
            continue
        stat_name = stat.attrib['stat']
        stat_value = stat.attrib['value']
        if stat_name in DISPLAY_STATS:
            display_stats[stat_name] = float(stat_value)
    return character, display_stats


if __name__ == '__main__':
    pob_xml = read_pob_to_xml(get_pob_code_from_url('https://pastebin.com/FEG9g37F'))
    print(get_stats_from_xml(pob_xml))
