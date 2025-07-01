import pandas as pd
from pymongo import MongoClient

# Load Excel file
excel_file = 'library_project/bookreport_copy_with_barcodes.xlsx'
df = pd.read_excel(excel_file)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['library_db']
books_collection = db['books']

# Insert each row as a document
for _, row in df.iterrows():
    books_collection.update_one(
        {'barcode': row['barcode_value']},
        {'$set': {
            'accession_number': row['accession number'],
            'title': row['title'],
            'department': row['department'],
            'author': row['author'],
            'department_code': row['department_codes'],
            'barcode': row['barcode_value']
        }},
        upsert=True
    )
print('Data imported successfully.') 