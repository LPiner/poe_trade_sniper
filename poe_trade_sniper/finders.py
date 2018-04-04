import requests

from poe_trade_sniper.db import add_watched_item, delete_all_watched_items


def get_possible_items(min_chaos_value: str=10, min_count: str=20):
    items = []
    uris = [
        "http://poe.ninja/api/Data/GetMapOverview?league=Bestiary",
        "http://poe.ninja/api/Data/GetDivinationCardsOverview?league=Bestiary",
        "http://poe.ninja/api/Data/GetProphecyOverview?league=Bestiary",
        "http://poe.ninja/api/Data/GetRareBeastOverview?league=Bestiary",
        "http://poe.ninja/api/Data/GetUniqueBeastOverview?league=Bestiary",
        "http://poe.ninja/api/Data/GetUniqueMapOverview?league=Bestiary",
        "http://poe.ninja/api/Data/GetUniqueJewelOverview?league=Bestiary",
        "http://poe.ninja/api/Data/GetUniqueFlaskOverview?league=Bestiary",
        "http://poe.ninja/api/Data/GetUniqueWeaponOverview?league=Bestiary",
        "http://poe.ninja/api/Data/GetUniqueArmourOverview?league=Bestiary",
        "http://poe.ninja/api/Data/GetUniqueAccessoryOverview?league=Bestiary",
    ]
    delete_all_watched_items()

    for uri in uris:
        data = requests.get(uri)
        data = data.json()
        for item in data['lines']:
            if item['chaosValue'] >= min_chaos_value and item['count'] >= min_count:
                if not item.get('baseType', None):
                    # Cards have no base type
                    name = item['name']
                elif item['name'] == item['baseType']:
                    # maps
                    # 'name': Lair of the Hydra Map
                    # 'baseType': Lair of the Hydra Map
                    name = item['name']
                else:
                    name = "%s %s" % (item['name'], item['baseType'])
                add_watched_item(name, item['chaosValue'])

