from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees).
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers.
    return c * r

# This dictionary maps our triage categories to a Doctor's 'specialty'
# This is the core of our "find specialist" logic.
TRIAGE_TO_SPECIALTY = {
    'CHEST_PAIN': 'Cardiology',
    'BREATHING': 'Pulmonology',
    'INJURY': 'Orthopedics',
    'BLEEDING': 'General Surgery',
    'OTHER': 'General Physician',
}