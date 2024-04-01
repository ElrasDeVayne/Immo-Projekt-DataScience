import csv
import pyodbc
import numpy as np
import pandas as pd
conn_str = 'DRIVER={SQL Server};SERVER=ANNINAYOGA\SQLEXPRESS;DATABASE=Immo;Trusted_Connection=yes;'



data = pd.read_csv (r'Location.csv',sep=';')
df = pd.DataFrame(data)
print(df.shape)
df = df[df['ZIP']>0]
print(df.shape)
df['ZIP'] = df['ZIP'].astype("int64")
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
                    INSERT INTO Location ([LocationId],[Street], [ZIP])
                    VALUES (?,?,?)''',
                    row.LocationId,
                    row.Street,
                    row.ZIP
                    )
        conn.commit()
    except Exception as e:
        print(e, row.LocationId)



