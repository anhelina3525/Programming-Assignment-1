"""
This module takes 4 arguments as input (namely: year,\
latitude of a location, longitude of a location and a path\
to a dataset containing information about movies and addresses\
where they were filmed) from the user and returns an html file (a map\
with tags).
"""
import argparse
import math
from folium import FeatureGroup, Marker, LayerControl, Map, Icon
from geopy.geocoders import Nominatim, ArcGIS

def main():
    """
    This main function contains functions
    for calculating haversine, parsing arguments,
    choosing the films of the user-given year etc.
    """
    def parser():
        """
        Parses the arguments entered by the user.
        """
        our_parser = argparse.ArgumentParser()
        our_parser.add_argument('year', type=str,
                                help='The year when the films were shot')
        our_parser.add_argument('latitude', type=str,
                                help='The latitude of the place as given by the user')
        our_parser.add_argument('longitude', type=str,
                                help='The longitude of the place as given by the user')
        our_parser.add_argument('path_to_dataset', type=str,
                                help='Path to the document containing information\
    about films')
        args = our_parser.parse_args()
        return args

    def haversine(first_location, second_location):
        """
        (tuple(float, float), tuple(float, float)) -> float
        Calculates and returns the distance between\
        two locations using the haversine function.\
        Takes the tuples in the form of ((latitude_1, longitude_1),
        (latitude_2, longitude_2)).
        >>> haversine((41.0096334, 28.9651646), (50.4444878, 30.5454331))
        1056.1874949974992
        >>> haversine((36.2348434, -71.0298488), (50.4444878, 30.5454331))
        7711.2855475010965
        """
        lat_1 = first_location[0]
        lat_2 = second_location[0]
        lon_1 = first_location[1]
        lon_2 = second_location[1]
        lon_1, lat_1, lon_2, lat_2 = \
            map(math.radians, [lon_1, lat_1, lon_2, lat_2])
        radius = 6371
        distance = 2*radius*(math.asin(math.sqrt(math.sin((lat_2-lat_1)/2)**2
                                                 + (math.cos(lat_1))*(math.cos(lat_2))*
                                                 (math.sin((lon_2-lon_1)/2))**2)))
        return distance

    def find_films_of_the_given_year(year, path):
        """
        str, str -> dict
        Takes the path to the file, reads it line by line,\
        choosing only the films of the year that the user has given,
        and returns a dictionary with the name of\
        the film as key (with an added '>>>' symbol in order to take\
        into account the films that have many locations but one and\
        the same name wihtout the names of the episodes) and location as value.
        >>> find_films_of_the_given_year('2006', 'locations_list_example.txt')
        {'"#1 Single" >>> 0': 'Los Angeles, California, USA',\
 '"#1 Single" >>> 1': 'New York City, New York, USA'}
        >>> find_films_of_the_given_year('2014, 'locations_list_example.txt)
        {'"#ATown" >>> 0': 'Spiderhouse Cafe, Austin, Texas, USA',\
 '"#ATown" >>> 1': 'Love Balls, Austin, Texas, USA',\
 '"#ATown" >>> 2': "Jo's Cafe, San Marcos, Texas, USA"}
        """
        dictionary = {}
        films = []
        with open(path, 'r', encoding='utf-8', errors='ignore') as file:
            for i in file.readlines()[14:-1]:
                if '('+year+')' in i:
                    films.append(i)
        for j in range(len(films)):
            if '}' in films[j]:
                dictionary[(films[j][:films[j].index('}')+1] +
                            ' >>> '+str(j)).strip()]\
                    = films[j][films[j].index('}')+1:].strip('\t\n')
            else:
                if films[j].index(')') == films[j].index('(')+5:
                    bracket_index = films[j].index(')')
                dictionary[(films[j][:bracket_index-6] +
                            ' >>> '+str(j)).strip()]\
                    = films[j][films[j].index('\t')+1:].strip(' \t\n')
        return dictionary

    def find_latitude_and_longitude(dictionary_with_film_locations):
        """
        dict -> dict
        Takes a dictionary with the name of the movie\
        as key and the location where it was filmed as value,\
        finds latitude and longitude of that location and returns\
        a dictionary where the key is the name of the film and the\
        value is a tuple of (latitude, longitude).
        >>> find_latitude_and_longitude({'"#1 Single" >>> 0':\
 'Los Angeles, California, USA',\
        '"#1 Single" >>> 1': 'New York City, New York, USA'})
 {'"#1 Single" >>> 0': (34.0536909, -118.242766), '"#1 Single" >>> 1':\
 (40.7127281, -74.0060152)}
        >>> find_latitude_and_longitude({'"#ATown" >>> 0':\
 'Spiderhouse Cafe, Austin, Texas, USA',\
 '"#ATown" >>> 1': 'Love Balls, Austin, Texas, USA',\
 '"#ATown" >>> 2': "Jo's Cafe, San Marcos, Texas, USA"})
        {'"#ATown" >>> 0': (30.29550500000005, -97.74175799999995),\
 '"#ATown" >>> 1': (30.26759000000004, -97.74298999999996),\
 '"#ATown" >>> 2': (29.88423000000006, -97.94614199999995)}
        """
        geolocator_nom = Nominatim(user_agent="my_app")
        geolocator_arc = ArcGIS(user_agent="my_app")
        dictionary = {}
        for key, value in dictionary_with_film_locations.items():
            if len(value) > 200:
                value = ','.join(value.split(',')[2:]).strip()
            location = geolocator_nom.geocode(value)
            if location is None:
                location = geolocator_arc.geocode(value)
            if location is None:
                value = ','.join(value.split(',')[1:]).strip()
                location = geolocator_arc.geocode(value)
            dictionary[key] = (location.latitude, location.longitude)
        return dictionary

    def find_distances(dictionary_with_coordinates):
        """
        dict -> dict
        This function takes a dictionary with the name of
        the film as key and the (latitude, longitude) as value
        and returns a dictionary where the key is a tuple
        (name_of_the_film, (latitude, longitude)) and value is
        the distance calculated using the haversine function.
        (parser().latitude and parser().longitude are called in the function)
        """
        dictionary = {}
        for key, value in dictionary_with_coordinates.items():
            dictionary[(key, value)] = \
                haversine((float(parser().latitude),
                           float(parser().longitude)), (float(value[0]),
                                                        float(value[1])))
        return dictionary

    def sort_the_dictionary(dictionary_with_distances):
        """
        dict -> list
        Sorts the dictionary items by value.
        >>> sort_the_dictionary({('"#ATown" >>> 0', (30.29550500000005, -97.74175799999995)):\
 9420.611027943263, ('"#ATown" >>> 1', (30.26759000000004, -97.74298999999996)):\
 9423.266955261182, ('"#ATown" >>> 2', (29.88423000000006, -97.94614199999995)):\
 9469.619703577415})
        [(('"#ATown" >>> 0', (30.29550500000005, -97.74175799999995)),\
 9420.611027943263), (('"#ATown" >>> 1', (30.26759000000004, -97.74298999999996)),\
 9423.266955261182), (('"#ATown" >>> 2', (29.88423000000006, -97.94614199999995)),\
 9469.619703577415)]
        """
        sorted_list = sorted(dictionary_with_distances.items(),
                             key=lambda x: x[1])
        return sorted_list

    def show_locations_on_a_map(list_with_distances_and_coordinates):
        """
        Returns an html file with the locations from the list
        with distances and coordinates.
        """
        my_map = Map(zoom_start=5)
        feature_group_1 = FeatureGroup(name='The nearest film locations')
        feature_group_2 = FeatureGroup(
            name='Some other movies filmed that year')
        for i in range(len(list_with_distances_and_coordinates)):
            if i < 10:
                feature_group = feature_group_1
                icon_color = 'lightred'
            else:
                feature_group = feature_group_2
                icon_color = 'beige'
            if '{' in list_with_distances_and_coordinates[i][0][0]:
                Marker(location=[int(list_with_distances_and_coordinates[i][0][1][0]),
                                 int(list_with_distances_and_coordinates[i][0][1][1])],
                       popup=list_with_distances_and_coordinates[i][0][0]
                       [:list_with_distances_and_coordinates[i][0][0].index('{')-8],
                       icon=Icon(color=icon_color)).add_to(feature_group)
            else:
                Marker(location=[int(list_with_distances_and_coordinates[i][0][1][0]),
                                 int(list_with_distances_and_coordinates[i][0][1][1])],
                       popup=list_with_distances_and_coordinates[i][0][0]
                       [:list_with_distances_and_coordinates[i][0][0].index('>>>')-1],
                       icon=Icon(color=icon_color)).add_to(feature_group)
        feature_group_1.add_to(my_map)
        feature_group_2.add_to(my_map)
        LayerControl().add_to(my_map)
        my_map.save('locations.html')
        return my_map

    show_locations_on_a_map(sort_the_dictionary(
        find_distances(find_latitude_and_longitude(
            find_films_of_the_given_year(parser().year,
                                         parser().path_to_dataset)))))


if __name__ == "__main__":
    main()
