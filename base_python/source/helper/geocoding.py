from geopy.geocoders import Nominatim

def get_coordinates(input_string=''):
    geolocator = Nominatim(user_agent="SomeName")
    return geolocator.geocode(input_string)

def get_city_name(lat, lon):
    my_coordinates = str(lat) + ', ' + str(lon)
    geolocator = Nominatim(user_agent="SomeName")
    location_data = geolocator.reverse(my_coordinates)
    if 'city' in location_data.raw['address']:
        return location_data.raw['address']['city']
    elif 'town' in location_data.raw['address']:
        return location_data.raw['address']['town']
    else:
        return 'No Settlement Found Nearby'

if __name__ == '__main__':
    string = 'Leipzig'
    location = get_coordinates(input_string=string)
    print(location.latitude, location.longitude)

    longitude = -5.4913
    latitude  = 38.7997
    city_name = get_city_name(lat=latitude, lon=longitude)
    print(city_name)
