import streamlit as st
import json
import requests
import pandas as pd
from pyproj import Proj, transform
import geopandas as gpd
import shapely
import haversine as hs
from haversine import Unit
import joblib
import folium
from folium import Marker
from streamlit_folium import st_folium


# Cache the data fetching function
@st.cache_data
def fetch_data():


    # Request all restaurants, cafes,  in the Kanton of Zurich, Switzerland
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json];
    area["ISO3166-1"="CH"][admin_level=2]->.a;
    (node["amenity"="restaurant"](area.a);
    node["amenity"="cafe"](area.a););
    out center;
    """


    # Server response
    response = requests.get(overpass_url, params={'data': overpass_query})

    data = response.json()

    # Extract relevant data from the JSON response
    places = []
    for element in data['elements']:
        if 'tags' in element:
            place_type = element['tags'].get('amenity') or element['tags'].get('shop')
            places.append({
                'id': element['id'],
                'type': place_type,
                'lat': element['lat'],
                'lon': element['lon'],
                'name': element['tags'].get('name', ''),
                'brand': element['tags'].get('brand', ''),
                'address_city': element['tags'].get('addr:city', ''),
                'address_zip': element['tags'].get('addr:postcode', ''),
                'address_street': element['tags'].get('addr:street', ''),
                'address_number': element['tags'].get('addr:housenumber', ''),
                

            })

    # Convert the list of dictionaries to a pandas DataFrame
    foodandbeverage_df = pd.DataFrame(places)



    # Request all restaurants, cafes,  in the Kanton of Zurich, Switzerland
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json];
    area["ISO3166-1"="CH"][admin_level=2]->.a;
    (node["shop"="supermarket"](area.a););
    out center;
    """


    # Server response
    response = requests.get(overpass_url, params={'data': overpass_query})

    data = response.json()

    # Extract relevant data from the JSON response
    places = []
    for element in data['elements']:
        if 'tags' in element:
            place_type = element['tags'].get('amenity') or element['tags'].get('shop')
            places.append({
                'id': element['id'],
                'type': place_type,
                'lat': element['lat'],
                'lon': element['lon'],
                'name': element['tags'].get('name', ''),
                'brand': element['tags'].get('brand', ''),
                'address_city': element['tags'].get('addr:city', ''),
                'address_zip': element['tags'].get('addr:postcode', ''),
                'address_street': element['tags'].get('addr:street', ''),
                'address_number': element['tags'].get('addr:housenumber', ''),
                

            })

    # Convert the list of dictionaries to a pandas DataFrame
    supermarket_df = pd.DataFrame(places)


    

    filepath = 'dataenriching/public_transport.csv'
    relevant_columns = ['Name','Betriebspunkttyp_Bezeichnung','Verkehrsmittel_Bezeichnung','E','N']

    df_transport = pd.read_csv(filepath, sep=",", encoding='latin1')[relevant_columns]

    lv95 = Proj(init='epsg:2056')  # LV95 projection
    wgs84 = Proj(init='epsg:4326')  # WGS84 projection

    # Convert LV95 coordinates to WGS84 (latitude and longitude)
    df_transport['Longitude'], df_transport['Latitude'] = transform(lv95, wgs84, df_transport['E'].values, df_transport['N'].values)
    df_transport.drop(['E', 'N'], axis=1, inplace=True)
    relevant_stops = ['Haltestelle', 'Haltestelle und Bedienpunkt']

    #filter for only relevant stops
    df_transport = df_transport[df_transport['Betriebspunkttyp_Bezeichnung'].isin(relevant_stops)]

    #taxes
    columns_taxes = ['Kantons-Id','Kanton','BfS-Id','Gemeinde','Einkommenssteuer_Kanton','Einkommenssteuer_Gemeinde','Vermögenssteuer_Kanton','Vermögenssteuer_Gemeinde']
    df_taxes = pd.read_csv('dataenriching/estv_income_rates.csv', encoding='utf-8')[columns_taxes]
    

    # Polygonmap als .shp file
    
    columns_polys = ['BFS_NUMMER', 'NAME', 'geometry']
    polys = gpd.read_file("dataenriching/swissBOUNDARIES3D_1_5_TLM_HOHEITSGEBIET.shp")[columns_polys]

    # Make a copy of the original GeoDataFrame
    polys_2d = polys.copy()

    # Define a function to remove the Z coordinate from a geometry
    def remove_z_coordinate(geom):
        return shapely.ops.transform(lambda x, y, z: (x, y), geom)

    # Apply the function to the 'geometry' column
    polys_2d['geometry'] = polys_2d['geometry'].apply(remove_z_coordinate)

    #convert LG95 coordinates to WGS84 coordinates
    wgs84_crs ="EPSG:4326"
    polys_2d.crs = "EPSG:2056"
    polys_2d = polys_2d.to_crs(wgs84_crs)
    
    #population density
    filepath = 'dataenriching/population_switzerland.csv'
    df_population = pd.read_csv(filepath)
    
    return foodandbeverage_df, supermarket_df, df_transport, df_taxes, polys_2d, df_population

################################################

def get_geolocation(address, api_key):
    params = {'key': api_key, 'address': address}
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json?'
    response = requests.get(base_url, params=params)
    data = response.json()
    if data['status'] == 'OK':
        location = data['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        return None, None
    
####################################################




def predict_rent(street_name, street_number, zip, squaremeters, rooms, country):
    #call Google geocoding API to get coordindates from address input

    api_key = 'YOUR API KEY'

    address = f"{street_name} {street_number}, {int(zip)}, {country}"
    latitude, longitude = get_geolocation(address, api_key)



    #########################################################

    def count_nearby_poi(apartment, poi, radius):
        count = 0
        for index, point in poi.iterrows():
            # Calculate distance between apartment and point of interest
            distance = hs.haversine((apartment[0], apartment[1]), 
                                    (point['lat'], point['lon']), 
                                    unit=Unit.METERS)
            if distance <= radius:
                count += 1
        return count

    # Assuming location_lat and location_lon are the latitude and longitude of the location
    # and supermarket_df is your DataFrame containing points of interest

    # Define the radius for nearby points of interest
    radius = 500  # 500 meters

    apartment = [latitude, longitude]

    # Count nearby points of interest for the location
    count_supermarket = count_nearby_poi(apartment, supermarket_df, radius)
    count_foodandbeverage = count_nearby_poi(apartment, foodandbeverage_df, radius)

    

    def find_nearby_poi(location_lat, location_lon, poi, radius):
        nearby_poi = pd.DataFrame(columns=poi.columns)  # Initialize an empty DataFrame to store nearby points of interest
        for index, point in poi.iterrows():
            # Calculate distance between location and point of interest
            distance = hs.haversine((location_lat, location_lon), 
                                    (point['lat'], point['lon']), 
                                    unit=Unit.METERS)
            if distance <= radius:
                # Add the point of interest to the nearby_poi DataFrame
                nearby_poi.loc[len(nearby_poi)] = point
        return nearby_poi

    def show_nearby_poi(location_lat, location_lon, poi, radius):
        nearby_poi = find_nearby_poi(location_lat, location_lon, poi, radius)
        return nearby_poi

    show_nearby_supermarkets = show_nearby_poi(apartment[0], apartment[1], supermarket_df, radius)
    show_nearby_foodandbeverage = show_nearby_poi(apartment[0], apartment[1], foodandbeverage_df, radius)

    ###############################################################

    def find_nearby_poi(location_lat, location_lon, poi, radius):
        nearby_poi = pd.DataFrame(columns=poi.columns)  # Initialize an empty DataFrame to store nearby points of interest
        for index, point in poi.iterrows():
            # Calculate distance between location and point of interest
            distance = hs.haversine((location_lat, location_lon), 
                                    (point['Latitude'], point['Longitude']), 
                                    unit=Unit.METERS)
            if distance <= radius:
                # Add the point of interest to the nearby_poi DataFrame
                nearby_poi.loc[len(nearby_poi)] = point
        return nearby_poi

    def count_nearby_poi(location_lat, location_lon, poi, radius):
        nearby_poi = find_nearby_poi(location_lat, location_lon, poi, radius)
        count = len(nearby_poi)
        return count, nearby_poi

    # Assuming location_lat and location_lon are the latitude and longitude of the location
    # and supermarket_df is your DataFrame containing points of interest

    # Define the radius for nearby points of interest
    radius = 500  # 500 meters

    apartment = [latitude, longitude]

    # Count nearby points of interest for the location
    poi_count, nearby_poi_df = count_nearby_poi(apartment[0], apartment[1], df_transport, radius)

    
    ###################################################################
    # Create a DataFrame with the coordinates
    location_df = pd.DataFrame({'longitude': [apartment[1]], 'latitude': [apartment[0]]})

    # Create a GeoDataFrame with the point geometry
    point = gpd.GeoDataFrame(location_df, geometry=gpd.points_from_xy(location_df['longitude'], location_df['latitude']))

    point.crs = "EPSG:4326"

    ###################################################################

    # Merge spatial data
    data_merged = gpd.sjoin(point, polys_2d, how="inner", op='within')

    ###################################################################

    data_merged = pd.merge(data_merged, df_taxes, left_on='BFS_NUMMER', right_on='BfS-Id',how='left')

    columns_to_keep = ['longitude', 'latitude','BFS_NUMMER','Gemeinde','Kanton','Einkommenssteuer_Kanton','Einkommenssteuer_Gemeinde','Vermögenssteuer_Kanton','Vermögenssteuer_Gemeinde']
    data_merged = data_merged[columns_to_keep]

    ###################################################################

    data_merged = pd.merge(data_merged, df_population[['Gemeindecode','Bevölkerungs-dichte pro km²']], left_on='BFS_NUMMER', right_on='Gemeindecode',how='left')
    
    ###################################################################

    #rename columns
    column_names = {'Einkommenssteuer_Kanton':'incometax_canton',
                        'Einkommenssteuer_Gemeinde':'incometax_municipality',
                        'Vermögenssteuer_Kanton':'wealthtax_canton',
                        'Vermögenssteuer_Gemeinde':'wealthtax_municipality',
                        'Bevölkerungs-dichte pro km²':'population_density',
    }

    data_merged.rename(columns=column_names, inplace=True)

    #change data type of population density to float
    #data_merged['population_density'] = pd.to_numeric(data_merged['population_density'], errors='coerce')
    data_merged['population_density'] = (
        data_merged['population_density']
        .str.replace("'", "")  # Entferne das Apostroph aus jedem Eintrag
        .astype(float)         # Konvertiere den bereinigten String zu Float
        #.astype(str)           # Konvertiere den Float zurück zu String
    )
    
    ###################################################################

    #add manual inputs Square Meters, Rooms, Object type to the dataframe
    #add number of foodandbeverage, supermarkets, publictransport stops

    add_df = pd.DataFrame({
        'Rooms': [rooms],
        'SquareMeter': [squaremeters],
        'ObjectType': [objecttype],
        'public_transport_count': [poi_count],
        'supermarket_count': [count_supermarket],
        'foodandbeverage_count': [count_foodandbeverage]
    })

    final_df = pd.concat([data_merged, add_df], axis=1)

    #rearrange columns for consistency
    columns_rearrange = ['Rooms',
                        'SquareMeter',
                        'ObjectType',
                        'incometax_canton',
                        'incometax_municipality',
                        'wealthtax_canton',
                        'wealthtax_municipality',
                        'population_density',
                        'public_transport_count',
                        'supermarket_count',
                        'foodandbeverage_count']

    final_df = final_df[columns_rearrange]

    # # Ensure columns are of correct type
    # final_df['Rooms'] = final_df['Rooms'].astype(int)
    # final_df['SquareMeter'] = final_df['SquareMeter'].astype(float)
    # final_df['public_transport_count'] = final_df['public_transport_count'].astype(int)
    # final_df['supermarket_count'] = final_df['supermarket_count'].astype(int)
    # final_df['foodandbeverage_count'] = final_df['foodandbeverage_count'].astype(int)
    
    ###################################################################

    # Apply One-Hot-Encoding to the canton column
    df_objectType_encoded = pd.get_dummies(final_df['ObjectType'])

    # Explicitly convert the One-Hot-Encoding columns to int
    df_objectType_encoded = df_objectType_encoded.astype(int)

    # Concatenate the original DataFrame without the canton column and the result of the One-Hot-Encoding
    df_for_model = pd.concat([final_df.drop('ObjectType', axis=1), df_objectType_encoded], axis=1)

    ################################################################### 

    

    model, ref_cols, target = joblib.load('XGBoost_model.pkl')

    # Identify missing columns
    missing_cols = [col for col in ref_cols if col not in df_for_model.columns]

    for col in missing_cols:
        df_for_model[col] = 0

    # Ensure the DataFrame now has all the columns in ref_cols
    X_new = df_for_model[ref_cols]


    prediction = model.predict(X_new)

    return prediction[0], nearby_poi_df, show_nearby_foodandbeverage, show_nearby_supermarkets, latitude, longitude

############################################################################

def generate_map(latitude, longitude, street_name, street_number, rooms, squaremeters, show_nearby_foodandbeverage, show_nearby_supermarkets, nearby_poi_df):

    # Center the map at the apartment location
    map_center = [latitude, longitude]

    # Create a folium map
    m = folium.Map(location=map_center, zoom_start=15)

    popup = f"{street_name} {street_number}, {rooms} {'rooms'}, {squaremeters} {'sqm'}"
    folium.Marker(
        location=[latitude, longitude],
        popup=popup,
        icon=folium.Icon(color='blue', icon='home')
    ).add_to(m)

    # Create a feature group for the supermarkets
    supermarket_layer = folium.FeatureGroup(name='Supermarkets')
    for idx, row in show_nearby_supermarkets.iterrows():
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=row['name'],
            icon=folium.Icon(color='green', icon='shopping-cart')
        ).add_to(supermarket_layer)

    # Add the feature group for supermarkets to the map
    supermarket_layer.add_to(m)

    # Create a feature group for food and beverage
    food_beverage_layer = folium.FeatureGroup(name='Food & Beverage')
    for idx, row in show_nearby_foodandbeverage.iterrows():
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=row['name'],
            icon=folium.Icon(color='orange', icon='cutlery')
        ).add_to(food_beverage_layer)

    # Add the feature group for food and beverage to the map
    food_beverage_layer.add_to(m)

    # Function to select the appropriate icon based on the transport type
    def get_transport_icon(transport_type):
        if transport_type == 'Bus':
            return folium.Icon(color='gray', icon='bus', prefix='fa')  
        elif transport_type == 'Tram':
            return folium.Icon(color='gray', icon='train', prefix='fa')  
        elif transport_type == 'Zug':
            return folium.Icon(color='gray', icon='train', prefix='fa')  
        else:
            return folium.Icon(color='gray', icon='h-square', prefix='fa')

    # Create a feature group for public transport stops
    publictransport_layer = folium.FeatureGroup(name='Public Transport')
    for idx, row in nearby_poi_df.iterrows():
        icon = get_transport_icon(row['Verkehrsmittel_Bezeichnung'])
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=row['Name'],
            icon=icon
        ).add_to(publictransport_layer)

    # Add the feature group for public transport stops to the map
    publictransport_layer.add_to(m)

    folium.LayerControl().add_to(m)

    # Add a circle to the map representing a 500-meter radius
    folium.Circle(
        location=[latitude, longitude],
        radius=500,  # Radius in meters
        color='red',
        fill=True,
        fill_color='red',  # Red fill color
        fill_opacity=0.2  # High level of transparency
    ).add_to(m)

    return m

######################################################################

# Streamlit App
# Initialize session state variables
if 'predicted_rent' not in st.session_state:
    st.session_state['predicted_rent'] = None
if 'latitude' not in st.session_state:
    st.session_state['latitude'] = None
if 'longitude' not in st.session_state:
    st.session_state['longitude'] = None
if 'show_nearby_foodandbeverage' not in st.session_state:
    st.session_state['show_nearby_foodandbeverage'] = None
if 'show_nearby_supermarkets' not in st.session_state:
    st.session_state['show_nearby_supermarkets'] = None
if 'nearby_poi_df' not in st.session_state:
    st.session_state['nearby_poi_df'] = None

st.title('Rent Prediction')

# User input form
st.sidebar.header('Input Apartment Details')
user_rent = st.sidebar.number_input('Amount of rent (CHF)', min_value=0, value=1900)
street_name = st.sidebar.text_input('Street Name', value='Langgrütstrasse')
street_number = st.sidebar.text_input('Street Number', value='54')
zip = st.sidebar.text_input('ZIP Code', value='8047')
country = st.sidebar.text_input('Country', value='Switzerland')
squaremeters = st.sidebar.number_input('Size of the apartment (sqm)', min_value=0, value=56)
rooms = st.sidebar.number_input('Number of rooms', min_value=0, value=2)
objecttype = st.sidebar.text_input('Type of Object', value='Wohnung')

# Fetch data
foodandbeverage_df, supermarket_df, df_transport, df_taxes, polys_2d, df_population  = fetch_data()

# # Predict rent
# if st.sidebar.button('Predict Rent'):
#     predicted_rent, nearby_poi_df, show_nearby_foodandbeverage, show_nearby_supermarkets, latitude, longitude = predict_rent(
#     street_name, street_number, zip, squaremeters, rooms, country)
#     st.write(f'The predicted rent for the apartment is: CHF {predicted_rent:.0f}')
    
#     # Display map
#     st.write('Map of the area')
    
#     # Generate and display the map
#     folium_map = generate_map(latitude, longitude, street_name, street_number, rooms, squaremeters, show_nearby_foodandbeverage, show_nearby_supermarkets, nearby_poi_df)
#     st_folium(folium_map, width=700, height=500)

if st.sidebar.button('Predict Rent'):
    st.session_state['predicted_rent'], st.session_state['nearby_poi_df'], st.session_state['show_nearby_foodandbeverage'], st.session_state['show_nearby_supermarkets'], st.session_state['latitude'], st.session_state['longitude'] = predict_rent(
        street_name, street_number, zip, squaremeters, rooms, country)
    st.session_state['user_rent'] = user_rent

if st.session_state['predicted_rent'] is not None:
    #st.write(f'The predicted rent for the apartment is: CHF {st.session_state["predicted_rent"]:.0f}')

    user_rent = st.session_state['user_rent']
    predicted_rent = st.session_state['predicted_rent']
    
    # Compare rents and set color
    if predicted_rent < user_rent:
        rent_color = 'red'
    else:
        rent_color = 'green'

    # # Display rents
    # st.markdown(f"<h1 style='font-size:24px;'>Demanded Rent: <span style='color:{rent_color};'>CHF {user_rent:.0f}</span></h1>", unsafe_allow_html=True)
    # st.markdown(f"<h1 style='font-size:24px;'>Predicted Rent: <span style='color:black;'>CHF {predicted_rent:.0f}</span></h1>", unsafe_allow_html=True)
    
    sidebar_bg_color = "#f0f2f6"  # This is the typical sidebar background color

    st.markdown(f"""
    <div style='background-color:{sidebar_bg_color}; padding: 10px; width: 700px; margin: 0 auto;'>
        <h1 style='font-size:24px;'>Demanded Rent: <span style='color:{rent_color};'>CHF {user_rent:.0f}</span></h1>
        <h1 style='font-size:24px;'>Predicted Market Rent: <span style='color:black;'>CHF {predicted_rent:.0f}</span></h1>
    </div>
    """, unsafe_allow_html=True)


    
    #st.write('Map of the area')
    st.markdown("<h2 style='font-size:24px;'>Map of the Area</h2>", unsafe_allow_html=True)
    folium_map = generate_map(
        st.session_state['latitude'], 
        st.session_state['longitude'], 
        street_name, 
        street_number, 
        rooms, 
        squaremeters, 
        st.session_state['show_nearby_foodandbeverage'], 
        st.session_state['show_nearby_supermarkets'], 
        st.session_state['nearby_poi_df']
    )
    st_folium(folium_map, width=700, height=500)
    









    


