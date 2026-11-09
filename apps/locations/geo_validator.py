from decimal import Decimal
from django.core.exceptions import ValidationError

# Authoritative Bounding Box for Tamil Nadu, India
TN_LAT_MIN = Decimal('8.0700')
TN_LAT_MAX = Decimal('13.5500')
TN_LNG_MIN = Decimal('76.2400')
TN_LNG_MAX = Decimal('80.3500')

TAMIL_NADU_DISTRICTS = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
    "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kancheepuram",
    "Kanniyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
    "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
    "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi",
    "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
    "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur",
    "Vellore", "Viluppuram", "Virudhunagar"
]

TAMIL_NADU_DISTRICTS_LOWER = {d.lower() for d in TAMIL_NADU_DISTRICTS}

def is_point_within_tamilnadu(lat, lng):
    """
    Validates if a coordinate pair falls strictly within Tamil Nadu boundaries.
    """
    if lat is None or lng is None:
        return False
    lat_dec = Decimal(str(lat))
    lng_dec = Decimal(str(lng))
    return (TN_LAT_MIN <= lat_dec <= TN_LAT_MAX) and (TN_LNG_MIN <= lng_dec <= TN_LNG_MAX)

TN_CITY_ALIASES = {
    'trichy': 'Tiruchirappalli',
    'tiruchi': 'Tiruchirappalli',
    'ooty': 'Nilgiris',
    'udhagamandalam': 'Nilgiris',
    'kovai': 'Coimbatore',
    'tanjore': 'Thanjavur',
    'tuticorin': 'Thoothukudi',
    'nellai': 'Tirunelveli',
    'kanchi': 'Kancheepuram',
    'kanchipuram': 'Kancheepuram',
    'hosur': 'Krishnagiri',
    'karaikudi': 'Sivaganga',
    'kumbakonam': 'Thanjavur',
    'pondy': 'Viluppuram',
    'vellore': 'Vellore',
    'salem': 'Salem',
    'madurai': 'Madurai',
    'chennai': 'Chennai',
    'coimbatore': 'Coimbatore',
}

def is_valid_tamilnadu_district(district_name):
    """
    Validates district against the 38 official administrative districts of Tamil Nadu.
    """
    if not district_name:
        return False
    d = district_name.strip().lower()
    if d in TAMIL_NADU_DISTRICTS_LOWER:
        return True
    if d in TN_CITY_ALIASES:
        return True
    return False

def validate_tamilnadu_route(origin_city, destination_city, stops=None):
    """
    Enforces that all origins, destinations, and intermediate stops are strictly within Tamil Nadu.
    """
    if origin_city.name.strip().lower() == destination_city.name.strip().lower():
        raise ValidationError("Origin and destination cities cannot be identical.")

    if not is_valid_tamilnadu_district(origin_city.district):
        raise ValidationError(f"Origin city '{origin_city.name}' is outside Tamil Nadu.")

    if not is_valid_tamilnadu_district(destination_city.district):
        raise ValidationError(f"Destination city '{destination_city.name}' is outside Tamil Nadu.")

    if origin_city.latitude and origin_city.longitude:
        if not is_point_within_tamilnadu(origin_city.latitude, origin_city.longitude):
            raise ValidationError(f"Origin coordinates for '{origin_city.name}' fall outside Tamil Nadu.")

    if destination_city.latitude and destination_city.longitude:
        if not is_point_within_tamilnadu(destination_city.latitude, destination_city.longitude):
            raise ValidationError(f"Destination coordinates for '{destination_city.name}' fall outside Tamil Nadu.")

    if stops:
        for stop in stops:
            if not is_valid_tamilnadu_district(stop.district):
                raise ValidationError(f"Intermediate stop '{stop.name}' is outside Tamil Nadu.")
    return True
