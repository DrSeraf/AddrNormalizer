from __future__ import annotations
from typing import Dict, List, Optional

# какие метки считать "улицей"
ROAD_KEYS = [
    "road","pedestrian","footway","path","residential","highway","street","street_name",
    "route","cycleway","service","unclassified","primary","secondary","tertiary","living_street"
]
# для locality в порядке приоритета
CITY_KEYS = ["city","town","village","suburb","hamlet","city_district","neighbourhood","municipality"]
# для региона
STATE_KEYS = ["state","state_district","province","region","island"]

def _first_component(parsed: List[Dict[str,str]], keys: List[str]) -> Optional[str]:
    for k in keys:
        for comp in parsed:
            if comp.get("label") == k and comp.get("value"):
                return str(comp["value"]).strip()
    return None

def pick_street(parsed: List[Dict[str,str]]) -> Optional[str]:
    road = _first_component(parsed, ROAD_KEYS)
    housenumber = _first_component(parsed, ["house_number","house"])
    if road and housenumber:
        return f"{road} {housenumber}".strip()
    return road or None

def pick_locality(parsed: List[Dict[str,str]]) -> Optional[str]:
    return _first_component(parsed, CITY_KEYS)

def pick_region(parsed: List[Dict[str,str]]) -> Optional[str]:
    return _first_component(parsed, STATE_KEYS)

def pick_postcode(parsed: List[Dict[str,str]]) -> Optional[str]:
    return _first_component(parsed, ["postcode","postal_code","zip"])

def pick_country(parsed: List[Dict[str,str]]) -> Optional[str]:
    return _first_component(parsed, ["country","country_name","country_code"])
