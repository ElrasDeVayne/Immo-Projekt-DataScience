import csv
import pyodbc
import numpy as np
import pandas as pd
conn_str = 'DRIVER={SQL Server};SERVER=ANNINAYOGA\SQLEXPRESS;DATABASE=Immo;Trusted_Connection=yes;'



data = pd.read_csv (r'C:\Users\AnninaBerweger\datascience-immo\Immo-Projekt-DataScience\TablesDB\Location_v3_enriched_v6.csv',sep=',', encoding='utf-8')
df = pd.DataFrame(data)
print(df.shape)
df = df[df['zip']>0]
print(df.shape)
df['zip'] = df['zip'].astype("int64")
df['longitude'] = df['longitude'].astype("string")
df['latitude'] = df['latitude'].astype("string")
# Connect to SQL Server
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
df = df.replace({np.nan:None})


# Insert DataFrame to Table
#, [Street], [ZIP]
for row in df.itertuples():
    try:
        cursor.execute('''
                    INSERT INTO Location ([LocationId],[street],[zip],[longitude],[latitude],[bfs_number],[municipality],[incometax_canton],[incometax_municipality],[wealthtax_canton],[wealthtax_municipality],[population_density],[public_transport_count],[supermarket_count],[foodandbeverage_count])
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    row.LocationId,
                    row.street,
                    row.zip,
                    row.longitude,
                    row.latitude,
                    row.bfs_number,
                    row.municipality,
                    row.incometax_canton,
                    row.incometax_municipality,
                    row.wealthtax_canton,
                    row.wealthtax_municipality,
                    row.population_density,
                    row.public_transport_count,
                    row.supermarket_count,
                    row.foodandbeverage_count
                    )
        conn.commit()
    except Exception as e:
        print(e, row.LocationId)



