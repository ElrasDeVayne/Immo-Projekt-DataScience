"# Immo-Projekt-DataScience" 

23.03.2024 Erstellung MySQL-Datenbank auf Azure
23.03.2024 WebScraping erstellt und initiiert für Kanton Zürich. Push GitHub 
24.03.2024 bis 31.03.2024 Scraping aller weiteren Kantone. 
25.03.2024 Erstellung und Commit der Jupyter Notebooks für API Zugriff auf OpenStreetMap Daten (overpass API) und Steuerfüsse des Kantons Zürich (Opendata_Swiss)
01.04.2024 WebScraping abgeschlossen. Gescrapte Daten aus AzureCloud auf lokale Datenbank gespeichert und Azure Subscription gecancelled. Setup für lokale DB in Ordner setupDB beschrieben. Tables für lokale Datenbank sind in TablesDB. Aufbereitung Data Cleansing (Jupyter 20240401_DataCleansing.ipynb) und EDA (Jupyter 20240401_EDA.ipynb). 
02.04.2024 Aktualisierung Jupyter EDA+Data Cleansing mit Outliers und noisy data entfernen. 
05.04.2024 Neues Notebook für die Konvertierung der Adressdaten in Koordinaten hinzugefügt und das daraus resultierende .csv file "Location_v2.csv".
25.04.2024 Updated Location_v3, created Location_v3_enriched which adds # of restaurants and supermarkets in 500m radius
10.05.2024 Created a .csv of the cleaned data: filtered_property_location_clean.csv. Encoded the features in PropertyAdditionalFeatures.csv and saved to df_property_features_encoded.csv. Updated the Data Cleansing part and ran more analyses in 20240401_EDA.ipynb. Creating Heatmap.html.