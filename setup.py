from requests import get
from os.path import realpath, dirname, isdir
from zipfile import ZipFile
from io import BytesIO

from pobutils import process_cluster_ids
from main import LEAGUE

def main():
    print("Beginning setup")
    
    root_dir = dirname(realpath(__file__))
    
    if isdir(f"{root_dir}/data/{LEAGUE}"):
        print("Data already found, skipping...")
        return

    print(f"Retrieving economy data for {LEAGUE}...")
    resp = get(f"https://poe.ninja/api/data/getdump?name={LEAGUE}", stream=True)

    print("Decompressing data...")
    ZipFile(BytesIO(resp.content)).extractall(f"{root_dir}/data/{LEAGUE}")
    
    print("Processing cluster jewel data...")
    process_cluster_ids(f'https://poe.ninja/api/data/itemoverview?league={LEAGUE}&type=ClusterJewel&language=en')

    print("Complete")


if __name__ == '__main__':
    main()
