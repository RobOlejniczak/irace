"""Constants in use by stats client."""


class Pages:
    """Pagination related constants."""

    ALL = -1
    # Entries per page. This is the amount set in iRacing site.
    # We shouldn't increase it.
    NUM_ENTRIES = 25


class Charts:
    """IRating chart types."""

    OVAL = 1
    ROAD = 2
    # XXX dirt oval/road as 3/4?


class RaceTypes:
    """Race types."""

    OVAL = 1
    ROAD = 2
    # XXX dirt oval/road as 3/4?


class LicenseClass:
    """License class constants."""

    ROOKIE = 1
    D = 2
    C = 3
    B = 4
    A = 5
    PRO = 6
    PRO_WC = 7

    ALL = (1, 2, 3, 4, 5, 6, 7)


class Sorting:
    """Result sorting constants."""

    IRATING = "irating"
    TIME = "start_time"
    POINTS = "points"
    DESC = "desc"
    ASC = "asc"


class Events:
    """Event type constants."""

    RACE = 1
    QUALIFY = 2
    PRACTICE = 3
    TIME_TRIAL = 4

    ALL = (1, 2, 3, 4)


class Official:
    """Event official vs unofficial classification."""

    OFFICIAL = 6
    UNOFFICIAL = 7

    ALL = (6, 7)


class URLs:
    """URLs used through the stats service."""

    BASE = "https://members.iracing.com/"

    # XXX get all these qsargs out of here...

    IRACING_LOGIN = "membersite/Login"
    IRACING_HOME = "membersite/member/Home.do"
    STATS_CHART = (
        "memberstats/member/GetChartData?custId=%s&catId=%s&chartType=1"
    )
    DRIVER_COUNTS = "membersite/member/GetDriverCounts"
    CAREER_STATS = "memberstats/member/GetCareerStats?custid=%s"
    YEARLY_STATS = "memberstats/member/GetYearlyStats?custid=%s"
    CARS_DRIVEN = "memberstats/member/GetCarsDriven?custid=%s"
    PERSONAL_BEST = "memberstats/member/GetPersonalBests?carid=%s&custid=%s"
    DRIVER_STATUS = "membersite/member/GetDriverStatus?%s"
    DRIVER_STATS = "memberstats/member/GetDriverStats"
    LAST_RACE_STATS = "memberstats/member/GetLastRacesStats?custid=%s"
    RESULTS_ARCHIVE = "memberstats/member/GetResults"
    SEASON_STANDINGS = "memberstats/member/GetSeasonStandings"
    SEASON_STANDINGS2 = "membersite/member/statsseries.jsp"
    HOSTED_RESULTS = "memberstats/member/GetPrivateSessionResults"
    SELECT_SERIES = (
        "membersite/member/SelectSeries.do?"
        "season=%s&view=undefined&nocache=%s"
    )
    SESSION_TIMES = "membersite/member/GetSessionTimes"  # T-m-d
    SERIES_RACE_RESULTS = "memberstats/member/GetSeriesRaceResults"
    EVENT_RESULTS = (
        "membersite/member/GetEventResultsAsCSV?"
        "subsessionid=%s&simsesnum=%s&includeSummary=1"
    )  # simsesnum 0 race, -1 qualy or practice, -2 practice

    @staticmethod
    def get(url: str) -> str:
        """Add the base URL to the slug."""

        return URLs.BASE + url


class Locations:
    """Locations, in case you need this for reasons."""

    ALL = "null"
    AFGHANISTAN = "AF"
    ALAND_ISLANDS = "AX"
    ALBANIA = "AL"
    ALGERIA = "DZ"
    AMERICAN_SAMOA = "AS"
    ANDORRA = "AD"
    ANGOLA = "AO"
    ANGUILLA = "AI"
    ANTARCTICA = "AQ"
    ANTIGUA_AND_BARBUDA = "AG"
    ARGENTINA = "AR"
    ARMENIA = "AM"
    ARUBA = "AW"
    AUSTRALIA = "AU"
    AUSTRIA = "AT"
    AZERBAIJAN = "AZ"
    BAHAMAS = "BS"
    BAHRAIN = "BH"
    BANGLADESH = "BD"
    BARBADOS = "BB"
    BELARUS = "BY"
    BELGIUM = "BE"
    BELIZE = "BZ"
    BENIN = "BJ"
    BERMUDA = "BM"
    BHUTAN = "BT"
    BOLIVIA_PLURINATIONAL_STATE_OF = "BO"
    BOSNIA_AND_HERZEGOVINA = "BA"
    BOTSWANA = "BW"
    BOUVET_ISLAND = "BV"
    BRAZIL = "BR"
    BRITISH_INDIAN_OCEAN_TERRITORY = "IO"
    BRUNEI_DARUSSALAM = "BN"
    BULGARIA = "BG"
    BURKINA_FASO = "BF"
    BURUNDI = "BI"
    CAMBODIA = "KH"
    CAMEROON = "CM"
    CANADA = "CA"
    CAPE_VERDE = "CV"
    CAYMAN_ISLANDS = "KY"
    CENTRAL_AFRICAN_REPUBLIC = "CF"
    CHAD = "TD"
    CHILE = "CL"
    CHINA = "CN"
    CHRISTMAS_ISLAND = "CX"
    COCOS_KEELING_ISLANDS = "CC"
    COLOMBIA = "CO"
    COMOROS = "KM"
    CONGO = "CG"
    CONGO_THE_DEMOCRATIC_REPUBLIC_OF_THE = "CD"
    COOK_ISLANDS = "CK"
    COSTA_RICA = "CR"
    COTE_DIVOIRE = "CI"
    CROATIA = "HR"
    CUBA = "CU"
    CYPRUS = "CY"
    CZECH_REPUBLIC = "CZ"
    DENMARK = "DK"
    DJIBOUTI = "DJ"
    DOMINICA = "DM"
    DOMINICAN_REPUBLIC = "DO"
    ECUADOR = "EC"
    EGYPT = "EG"
    EL_SALVADOR = "SV"
    EQUATORIAL_GUINEA = "GQ"
    ERITREA = "ER"
    ESTONIA = "EE"
    ETHIOPIA = "ET"
    FALKLAND_ISLANDS_MALVINAS = "FK"
    FAROE_ISLANDS = "FO"
    FIJI = "FJ"
    FINLAND = "FI"
    FRANCE = "FR"
    FRENCH_GUIANA = "GF"
    FRENCH_POLYNESIA = "PF"
    FRENCH_SOUTHERN_TERRITORIES = "TF"
    GABON = "GA"
    GAMBIA = "GM"
    GEORGIA = "GE"
    GERMANY = "DE"
    GHANA = "GH"
    GIBRALTAR = "GI"
    GREECE = "GR"
    GREENLAND = "GL"
    GRENADA = "GD"
    GUADELOUPE = "GP"
    GUAM = "GU"
    GUATEMALA = "GT"
    GUERNSEY = "GG"
    GUINEA = "GN"
    GUINEA_BISSAU = "GW"
    GUYANA = "GY"
    HAITI = "HT"
    HEARD_ISLAND_AND_MCDONALD_ISLANDS = "HM"
    HOLY_SEE_VATICAN_CITY_STATE = "VA"
    HONDURAS = "HN"
    HONG_KONG = "HK"
    HUNGARY = "HU"
    ICELAND = "IS"
    INDIA = "IN"
    INDONESIA = "ID"
    IRAN_ISLAMIC_REPUBLIC_OF = "IR"
    IRAQ = "IQ"
    IRELAND = "IE"
    ISLE_OF_MAN = "IM"
    ISRAEL = "IL"
    ITALY = "IT"
    JAMAICA = "JM"
    JAPAN = "JP"
    JERSEY = "JE"
    JORDAN = "JO"
    KAZAKHSTAN = "KZ"
    KENYA = "KE"
    KIRIBATI = "KI"
    KOREA_DEMOCRATIC_PEOPLES_REPUBLIC_OF = "KP"
    KOREA_REPUBLIC_OF = "KR"
    KUWAIT = "KW"
    KYRGYZSTAN = "KG"
    LAO_PEOPLES_DEMOCRATIC_REPUBLIC = "LA"
    LATVIA = "LV"
    LEBANON = "LB"
    LESOTHO = "LS"
    LIBERIA = "LR"
    LIBYAN_ARAB_JAMAHIRIYA = "LY"
    LIECHTENSTEIN = "LI"
    LITHUANIA = "LT"
    LUXEMBOURG = "LU"
    MACAO = "MO"
    MACEDONIA_THE_FORMER_YUGOSLAV_REPUBLIC_OF = "MK"
    MADAGASCAR = "MG"
    MALAWI = "MW"
    MALAYSIA = "MY"
    MALDIVES = "MV"
    MALI = "ML"
    MALTA = "MT"
    MARSHALL_ISLANDS = "MH"
    MARTINIQUE = "MQ"
    MAURITANIA = "MR"
    MAURITIUS = "MU"
    MAYOTTE = "YT"
    MEXICO = "MX"
    MICRONESIA_FEDERATED_STATES_OF = "FM"
    MOLDOVA_REPUBLIC_OF = "MD"
    MONACO = "MC"
    MONGOLIA = "MN"
    MONTENEGRO = "ME"
    MONTSERRAT = "MS"
    MOROCCO = "MA"
    MOZAMBIQUE = "MZ"
    MYANMAR = "MM"
    NAMIBIA = "NA"
    NAURU = "NR"
    NEPAL = "NP"
    NETHERLANDS = "NL"
    NETHERLANDS_ANTILLES = "AN"
    NEW_CALEDONIA = "NC"
    NEW_ZEALAND = "NZ"
    NICARAGUA = "NI"
    NIGER = "NE"
    NIGERIA = "NG"
    NIUE = "NU"
    NORFOLK_ISLAND = "NF"
    NORTHERN_MARIANA_ISLANDS = "MP"
    NORWAY = "NO"
    OMAN = "OM"
    PAKISTAN = "PK"
    PALAU = "PW"
    PALESTINIAN_TERRITORY_OCCUPIED = "PS"
    PANAMA = "PA"
    PAPUA_NEW_GUINEA = "PG"
    PARAGUAY = "PY"
    PERU = "PE"
    PHILIPPINES = "PH"
    PITCAIRN = "PN"
    POLAND = "PL"
    PORTUGAL = "PT"
    PUERTO_RICO = "PR"
    QATAR = "QA"
    REUNION = "RE"
    ROMANIA = "RO"
    RUSSIAN_FEDERATION = "RU"
    RWANDA = "RW"
    SAINT_BARTHELEMY = "BL"
    SAINT_HELENA_ASCENSION_AND_TRISTAN_DA_CUNHA = "SH"
    SAINT_KITTS_AND_NEVIS = "KN"
    SAINT_LUCIA = "LC"
    SAINT_MARTIN_FRENCH_PART = "MF"
    SAINT_PIERRE_AND_MIQUELON = "PM"
    SAINT_VINCENT_AND_THE_GRENADINES = "VC"
    SAMOA = "WS"
    SAN_MARINO = "SM"
    SAO_TOME_AND_PRINCIPE = "ST"
    SAUDI_ARABIA = "SA"
    SENEGAL = "SN"
    SERBIA = "RS"
    SEYCHELLES = "SC"
    SIERRA_LEONE = "SL"
    SINGAPORE = "SG"
    SLOVAKIA = "SK"
    SLOVENIA = "SI"
    SOLOMON_ISLANDS = "SB"
    SOMALIA = "SO"
    SOUTH_AFRICA = "ZA"
    SOUTH_GEORGIA_AND_THE_SOUTH_SANDWICH_ISLANDS = "GS"
    SPAIN = "ES"
    SRI_LANKA = "LK"
    SUDAN = "SD"
    SURINAME = "SR"
    SVALBARD_AND_JAN_MAYEN = "SJ"
    SWAZILAND = "SZ"
    SWEDEN = "SE"
    SWITZERLAND = "CH"
    SYRIAN_ARAB_REPUBLIC = "SY"
    TAIWAN_PROVINCE_OF_CHINA = "TW"
    TAJIKISTAN = "TJ"
    TANZANIA_UNITED_REPUBLIC_OF = "TZ"
    THAILAND = "TH"
    TIMOR_LESTE = "TL"
    TOGO = "TG"
    TOKELAU = "TK"
    TONGA = "TO"
    TRINIDAD_AND_TOBAGO = "TT"
    TUNISIA = "TN"
    TURKEY = "TR"
    TURKMENISTAN = "TM"
    TURKS_AND_CAICOS_ISLANDS = "TC"
    TUVALU = "TV"
    UGANDA = "UG"
    UKRAINE = "UA"
    UNITED_ARAB_EMIRATES = "AE"
    UNITED_KINGDOM = "GB"
    UNITED_STATES = "US"
    UNITED_STATES_MINOR_OUTLYING_ISLANDS = "UM"
    URUGUAY = "UY"
    UZBEKISTAN = "UZ"
    VANUATU = "VU"
    VENEZUELA_BOLIVARIAN_REPUBLIC_OF = "VE"
    VIET_NAM = "VN"
    VIRGIN_ISLANDS_BRITISH = "VG"
    VIRGIN_ISLANDS_US = "VI"
    WALLIS_AND_FUTUNA = "WF"
    WESTERN_SAHARA = "EH"
    YEMEN = "YE"
    ZAMBIA = "ZM"
    ZIMBABWE = "ZW"
