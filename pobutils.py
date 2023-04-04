import re
import json
import zlib
import base64
import logging
import binascii
import requests
import numpy as np
import pandas as pd
from typing import Optional
from dataclasses import dataclass
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

@dataclass
class UniqueItem:
    name: str

@dataclass
class ClusterJewel:
    size: str
    level: int
    num_passives: int
    small_passives: str


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

    return [UniqueItem(
            name=unique_match.group('item_name')
        )
        for item in items_xml if item.tag == 'Item' and (unique_match := unique.match(item.text.strip()))]


def get_clusters_from_xml(root: ET.Element) -> list:
    items_xml = root.find('Items')
    if not items_xml:
        return []
    cluster = re.compile(r'^Rarity: \w+\s+[\w ]+\s+(?P<size>[\w ]+)\s+(Unique ID: [\w\d]+\s+)?Item Level: (?P<item_level>\d+)\s+LevelReq: \d+\s+Implicits: \d\s+{crafted}Adds (?P<num_passives>\d) Passive Skills\s+{crafted}[\w\d ]+\s+{crafted}(?P<small_passives>(Added Small Passive Skills grant: [\w% \d]+\n)+)')

    return [ClusterJewel(
            size=cluster_match.group('size'),
            num_passives=int(cluster_match.group('num_passives')),
            level=int(cluster_match.group('item_level')),
            small_passives=cluster_match.group('small_passives').strip().replace('\n', ', ').replace('Added Small Passive Skills grant: ', '')
        )
        for item in items_xml if item.tag == 'Item' and (cluster_match := cluster.match(item.text.strip()))]


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


def process_cluster_ids(url: str):
    # https://poe.ninja/api/data/itemoverview?league=Kalandra&type=ClusterJewel&language=en
    # try:
    #     with open(file_name, 'r', encoding='utf-8') as cluster_info_file:
    #         cluster_info_dict = json.loads(cluster_info_file.read())
    # except IOError as ioe:
    #     logging.error("Could not read file '%s'", file_name)
    #     return {}
    # except json.JSONDecodeError as jde:
    #     logging.error("Could not decode JSON at '%s'", file_name)

    resp = requests.get(url)

    if resp.status_code != 200:
        logging.error("Failed to fetch URL '%s'", url)
        return
    
    try:
        cluster_info_dict = json.loads(resp.text)
    except json.JSONDecodeError as jde:
        logging.error("Could not decode JSON from API request")
    
    cluster_id_df = pd.DataFrame([(cluster.get('id'), cluster.get('levelRequired')) for cluster in cluster_info_dict['lines']], columns=['Id', 'ItemLevel'])

    cluster_id_df.to_csv('data/Kalandra/Kalandra.clusterjewels.ids.csv', index=False)


if __name__ == '__main__':
    # pob_xml = read_pob_to_xml(get_pob_code_from_url('https://pastebin.com/FEG9g37F'))
    pob_xml = read_pob_to_xml(get_pob_code_from_url('https://pobb.in/BL70qYjBEzI8'))
    # print(get_stats_from_xml(pob_xml))
    print(get_clusters_from_xml(pob_xml))
    # print(pob_xml)
    # process_cluster_ids('https://poe.ninja/api/data/itemoverview?league=Kalandra&type=ClusterJewel&language=en')
