import requests
from bs4 import BeautifulSoup
from lxml import etree
from selenium import webdriver
import pyodbc
from datetime import datetime
import uuid

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=tcp:immozhaw.database.windows.net,1433;DATABASE=Immo;UID=immoadmin;PWD=zhaw$1234;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

canton = 'ge'  #always set the canton!
if True:
    for page in range(1, 30):  # has 50 pages
        response = requests.get("https://www.immoscout24.ch/de/immobilien/mieten/kanton-genf?pn="+str(page))
        print("Seite: "+str(page))
        soup = BeautifulSoup(response.content, 'html.parser')
        body = soup.find("body")
        listItem = 1  #max 20 per Page
        for title in soup.find_all( class_='ResultList_listItem_j5Td_'):  # Replace 'h2' and 'class_' with the correct tag and class
            if listItem < 21:
                print("Item: " + str(listItem))
                listingid = title.find('a').attrs['href'].split("/")[2]
                url = 'https://www.immoscout24.ch'+title.find('a').attrs['href']  # Replace with the specific page you're interested in
                #from urllib3 import urlopen
                # Chrome Option
                options = webdriver.ChromeOptions()
                print(url)
                # Add option
                options.add_argument('user-agent={0}'.format(user_agent))
                # Initial browser
                browser = webdriver.Chrome(options=options)
                # Get page content
                browser.get(url)
                # Get html page source
                html = browser.page_source
                # Initial BeautifulSoup
                soup = BeautifulSoup(html, 'lxml')
                body = soup.find("body")

                ########### DOM ELEMENTS
                rooms = None
                squaremeter = None
                price = None
                floor = None
                availability = None
                objecttyp = None
                yearbuilt = None
                locationzip = None
                street = None
                zip = None
                location = None
                netprice = None
                additionalcost = None
                propertydescription = None
                propertyList = None
                vendor = None

                try:
                    rooms = soup.find("div", {"class": "SpotlightAttributesNumberOfRooms_value_TUMrd"}).text
                except Exception as e:
                    print("no rooms")
                try:
                    squaremeter = soup.find("div", {"class": "SpotlightAttributesUsableSpace_value_cpfrh"}).text
                    squaremeter = squaremeter.replace("m2","").strip()
                except Exception as e:
                    print("no squaremeter")

                try:
                    price = soup.find("div", {"class": "SpotlightAttributesPrice_value_TqKGz"}).text
                    price = ''.join([char for char in price if char.isdigit()])
                except Exception as e:
                    print("no price")

                try:
                    street = soup.find("address", {"class": "AddressDetails_address_i3koO"}).next.string.rstrip(', ')

                except Exception as e:
                    print("no street")
                try:
                    locationzip =  soup.find("address", {"class": "AddressDetails_address_i3koO"}).next.next_sibling.text
                    zip = locationzip[0:4]
                    location = locationzip[5:]
                except Exception as e:
                    print("no street")

                try:
                    priceproperties = soup.find("div", {"data-test": "costs"})
                    for items in priceproperties:
                        for item in items:
                            if item.name == 'dt':
                                if item.string == 'Nettomiete:':
                                    netprice = item.next_sibling.text
                                    netprice = ''.join([char for char in netprice if char.isdigit()])
                                if item.string == 'Nebenkosten:':
                                    additionalcost = item.next_sibling.text
                                    additionalcost = ''.join([char for char in additionalcost if char.isdigit()])
                except Exception as e:
                    print("no priceproperties")

                try:
                    propertyproperties = soup.find("ul", {"class": "FeaturesFurnishings_list_S54KV"})
                    propertyList = []
                    for items in propertyproperties:
                        for item in items:
                            if item.next_sibling is not None:
                                propertyList.append(item.next_sibling.string)

                except Exception as e:
                    print("no propertyproperties")

                try:
                    propertydescription = soup.find("div", {"class": "Description_descriptionBody_AYyuy"}).text
                except Exception as e:
                    print("no propertydescription")

                try:
                    #code anpassen
                    mainproperties = soup.find("div", {"class": "CoreAttributes_coreAttributes_e2NAm"})
                    for items in mainproperties:
                        for item in items:
                            if item.name == 'dt':
                                if item.string== 'Verfügbarkeit:':
                                    availability = item.next_sibling.string
                                if item.string== 'Objekttyp:':
                                    objecttyp = item.next_sibling.string
                                if item.string== 'Etage:':
                                    floor = item.next_sibling.text.strip()
                                if item.string == 'Baujahr:':
                                    yearbuilt = item.next_sibling.text
                                # ausbauen falls nötig
                except Exception as e:
                    print("no mainprops")

                try:
                    vendor = soup.find("div", {"class": "ListingDetails_column_Nd5tM"}).find("address").next.string.strip()
                except Exception as e:
                    print("no vendor")

                ###########! DOM ELEMENTS

                print(url, rooms, squaremeter, price,availability, objecttyp, floor, yearbuilt, street, zip, location, netprice,additionalcost,vendor, propertyList,propertydescription )

                ########### store values here in DB.

                try:
                    # Establish a connection to the database
                    # Write to Property Table
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()
                    insert_query = "INSERT INTO  [dbo].[Property] (ListingId,Timestamp, Rooms,SquareMeter,Floor,Availability,Objecttype,YearBuilt,Price,AdditionalCost,NetPrice,LocationId,PropertyAdditionalFeaturesId,PropertyDescription,Vendor, Canton) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
                    current_timestamp = datetime.now()
                    timestamp = current_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    locationId =str(uuid.uuid4())
                    PropertyAdditionalFeaturesId =str(uuid.uuid4())
                    # Data to insert
                    data_to_insert = (listingid,timestamp, rooms,squaremeter,floor,availability,objecttyp,yearbuilt,price,additionalcost,netprice,locationId,PropertyAdditionalFeaturesId,propertydescription,vendor, canton)  # Tuple containing the data to insert
                    # Execute the insert query
                    cursor.execute(insert_query, data_to_insert)
                    # Commit the transaction
                    conn.commit()

                    # Write to Location Table
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()
                    insert_query = "INSERT INTO  [dbo].[Location] (LocationId,Street,ZIP) VALUES (?,?,?)"
                    # Data to insert
                    data_to_insert = (locationId,street, zip)  # Tuple containing the data to insert
                    # Execute the insert query
                    cursor.execute(insert_query, data_to_insert)
                    # Commit the transaction
                    conn.commit()

                    # Write to PropertyAdditionalFeatures Table
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()
                    for feature in propertyList:
                        insert_query = "INSERT INTO  [dbo].[PropertyAdditionalFeatures] (ListingId,Feature) VALUES (?,?)"
                        # Data to insert
                        data_to_insert = (locationId,feature)  # Tuple containing the data to insert
                        # Execute the insert query
                        cursor.execute(insert_query, data_to_insert)
                        # Commit the transaction
                        conn.commit()

                # Write to Property Table
                except Exception as e:
                    print(e)
                # Close the connection
                cursor.close()
                conn.close()

                ###########!

                # Quit browser
                browser.quit()
                listItem = listItem + 1