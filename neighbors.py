"""Land-border adjacency graph for computing 'conflict-ridden neighborhood'
indicator (PITF-style: count of bordering states with major armed conflict).

ISO-3166-1 alpha-3 codes. Only land borders counted (consistent with PITF).
"""

BORDERS: dict[str, list[str]] = {
    "USA": ["CAN", "MEX"],
    "CAN": ["USA"],
    "MEX": ["USA", "GTM", "BLZ"],
    "GBR": ["IRL"],
    "IRL": ["GBR"],
    "FRA": ["BEL", "LUX", "DEU", "CHE", "ITA", "ESP", "AND", "MCO"],
    "DEU": ["DNK", "POL", "CZE", "AUT", "CHE", "FRA", "LUX", "BEL", "NLD"],
    "ITA": ["FRA", "CHE", "AUT", "SVN"],
    "ESP": ["FRA", "PRT", "AND"],
    "PRT": ["ESP"],
    "NLD": ["BEL", "DEU"],
    "BEL": ["FRA", "NLD", "DEU", "LUX"],
    "AUT": ["DEU", "CZE", "SVK", "HUN", "SVN", "ITA", "CHE", "LIE"],
    "CHE": ["DEU", "FRA", "ITA", "AUT", "LIE"],
    "SWE": ["NOR", "FIN"],
    "NOR": ["SWE", "FIN", "RUS"],
    "DNK": ["DEU"],
    "POL": ["DEU", "CZE", "SVK", "UKR", "BLR", "LTU", "RUS"],
    "CZE": ["DEU", "POL", "SVK", "AUT"],
    "HUN": ["AUT", "SVK", "UKR", "ROU", "SRB", "HRV", "SVN"],
    "GRC": ["ALB", "MKD", "BGR", "TUR"],
    "TUR": ["GRC", "BGR", "GEO", "ARM", "AZE", "IRN", "IRQ", "SYR"],
    "BRA": ["ARG", "URY", "PRY", "BOL", "PER", "COL", "VEN", "GUY", "SUR", "GUF"],
    "ARG": ["CHL", "BOL", "PRY", "BRA", "URY"],
    "CHL": ["ARG", "BOL", "PER"],
    "COL": ["VEN", "BRA", "PER", "ECU", "PAN"],
    "PER": ["ECU", "COL", "BRA", "BOL", "CHL"],
    "URY": ["ARG", "BRA"],
    "CRI": ["NIC", "PAN"],
    "JAM": [],
    "TTO": [],
    "IND": ["PAK", "CHN", "NPL", "BTN", "BGD", "MMR"],
    "KOR": ["PRK"],
    "JPN": [],
    "IDN": ["MYS", "PNG", "TLS"],
    "PHL": [],
    "THA": ["MMR", "LAO", "KHM", "MYS"],
    "MYS": ["THA", "IDN", "BRN"],
    "ZAF": ["NAM", "BWA", "ZWE", "MOZ", "SWZ", "LSO"],
    "NGA": ["BEN", "NER", "TCD", "CMR"],
    "KEN": ["ETH", "SOM", "SSD", "UGA", "TZA"],
    "GHA": ["CIV", "TGO", "BFA"],
    "SEN": ["MRT", "MLI", "GIN", "GNB", "GMB"],
    "BWA": ["ZAF", "NAM", "ZWE", "ZMB"],
    "MUS": [],
    "ISR": ["LBN", "SYR", "JOR", "EGY", "PSE"],
    "AUS": [],
    "NZL": [],
    # MENA
    "TUN": ["DZA", "LBY"],
    "MAR": ["DZA", "MRT"],
    "IRN": ["IRQ", "TUR", "AFG", "PAK", "TKM", "ARM", "AZE"],
    "IRQ": ["IRN", "TUR", "SYR", "JOR", "SAU", "KWT"],
    "LBN": ["SYR", "ISR"],
    "JOR": ["ISR", "IRQ", "SYR", "SAU", "PSE"],
    "EGY": ["LBY", "SDN", "ISR", "PSE"],
    # Latin America additions
    "VEN": ["COL", "BRA", "GUY"],
    "NIC": ["HND", "CRI"],
    "ECU": ["COL", "PER"],
    "BOL": ["BRA", "PRY", "ARG", "CHL", "PER"],
    "PRY": ["BRA", "ARG", "BOL"],
    "PAN": ["CRI", "COL"],
    "DOM": ["HTI"],
    "SLV": ["GTM", "HND"],
    "GTM": ["MEX", "BLZ", "SLV", "HND"],
    "HND": ["GTM", "SLV", "NIC"],
}

CONFLICT_COUNTRIES_BY_YEAR: dict[int, set[str]] = {}
_PERSISTENT_CONFLICTS = {
    "AFG": range(1978, 2025),
    "IRQ": list(range(1980, 1989)) + list(range(1990, 1992)) + list(range(2003, 2018)),
    "SYR": range(2011, 2025),
    "SOM": range(1991, 2025),
    "SSD": range(2013, 2025),
    "SDN": list(range(1983, 2005)) + list(range(2023, 2025)),
    "COD": list(range(1996, 2004)) + list(range(2012, 2025)),
    "MMR": list(range(1988, 2025)),
    "COL": range(1964, 2017),
    "ETH": list(range(1974, 1992)) + list(range(1998, 2001)) + list(range(2020, 2023)),
    "YEM": list(range(2014, 2025)),
    "LBY": range(2011, 2025),
    "UKR": range(2014, 2025),
    "PAK": range(2004, 2025),
    "NGA": list(range(2009, 2025)),
    "MLI": range(2012, 2025),
    "BFA": range(2015, 2025),
    "NER": range(2015, 2025),
    "TCD": list(range(2005, 2010)) + list(range(2020, 2025)),
    "CMR": range(2016, 2025),
    "MOZ": range(2017, 2024),
    "RUS": list(range(1994, 1997)) + list(range(1999, 2001)) + list(range(2022, 2025)),
    "GEO": [2008],
    "SRB": list(range(1991, 2000)),
    "HRV": list(range(1991, 1996)),
    "BIH": list(range(1992, 1996)),
    "LBN": list(range(1975, 1990)) + [2006] + list(range(2023, 2025)),
    "SLV": range(1979, 1993),
    "GTM": range(1960, 1997),
    "NIC": range(1979, 1990),
    "PRK": [1950, 1951, 1952, 1953],
    "LKA": range(1983, 2010),
    "NPL": range(1996, 2007),
    "RWA": list(range(1990, 1995)),
    "SLE": range(1991, 2003),
    "LBR": list(range(1989, 1997)) + list(range(1999, 2004)),
    "CIV": list(range(2002, 2008)) + [2010, 2011],
    "ERI": list(range(1998, 2001)),
    "IRN": list(range(1980, 1989)),
    "PSE": list(range(2000, 2025)),
}

for country, years in _PERSISTENT_CONFLICTS.items():
    for yr in years:
        if yr not in CONFLICT_COUNTRIES_BY_YEAR:
            CONFLICT_COUNTRIES_BY_YEAR[yr] = set()
        CONFLICT_COUNTRIES_BY_YEAR[yr].add(country)


def neighbors_in_conflict(country: str, year: int) -> int:
    """Count how many of a country's land neighbors had major armed conflict."""
    nbrs = BORDERS.get(country, [])
    if not nbrs:
        return 0
    active = CONFLICT_COUNTRIES_BY_YEAR.get(year, set())
    return sum(1 for n in nbrs if n in active)
