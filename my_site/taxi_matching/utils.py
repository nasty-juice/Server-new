import math

TARGET_LOCATION = {
    "kihung_station": (37.275657, 127.115944),
    "mju": (37.224216, 127.187848)
}

RADIUS_LIMIT = 200  # meters

def check_user_location(starting_point, user_lat, user_lon):
    
    if starting_point not in TARGET_LOCATION:
        return False
    
    target_lat, target_lon = TARGET_LOCATION[starting_point]
    distance = calculate_distance(user_lat, user_lon, target_lat, target_lon)
    
    if distance <= RADIUS_LIMIT:
        return True
    else:
        return False
  
# 하버사인 공식을 사용하여 거리 계산
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # returns distance in meters