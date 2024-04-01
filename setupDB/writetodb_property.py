import csv
import pyodbc
import numpy as np
import pandas as pd
conn_str = 'DRIVER={SQL Server};SERVER=ANNINAYOGA\SQLEXPRESS;DATABASE=Immo;Trusted_Connection=yes;'



data = pd.read_csv (r'Property.csv',sep=';')
df = pd.DataFrame(data)
print(df.shape)
#df = df[df['ZIP']>0]
#print(df.shape)
#df['ZIP'] = df['ZIP'].astype("int64")

# Connect to SQL Server
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
df = df.replace({np.nan:None})


# Insert DataFrame to Table
#, [Street], [ZIP]
for row in df.itertuples():
    try:
        cursor.execute('''
                    INSERT INTO Property ([ListingId],[Timestamp],[Rooms],[SquareMeter],[Floor],[Availability],[ObjectType],[YearBuilt],[Price],[AdditionalCost],[NetPrice],[LocationId],[PropertyAdditionalFeaturesId],[PropertyDescription],[Vendor],[Canton])
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    row.ListingId,
                    row.Timestamp,
                    row.Rooms,
                    row.SquareMeter,
                    row.Floor,
                    row.Availability,
                    row.ObjectType,
                    row.YearBuilt,
                    row.Price,
                    row.AdditionalCost,
                    row.NetPrice,
                    row.LocationId,
                    row.PropertyAdditionalFeaturesId,
                    row.PropertyDescription,
                    row.Vendor,
                    row.Canton
                    )
        conn.commit()
    except Exception as e:
        print(e, row.ListingId)



