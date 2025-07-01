from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import pandas as pd

# Initialize Flask app
app = Flask(__name__)

# Initialize MongoDB
client = MongoClient('mongodb://localhost:27017/')  # Change this if using MongoDB Atlas
db = client['library_db']
books_collection = db['books']

# Home route
@app.route('/')
def index():
    return redirect(url_for('view_books'))

# Route to add a book
@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        name = request.form['name']
        barcode = request.form['barcode']
        author = request.form['author']
        
        # Add book to MongoDB
        books_collection.insert_one({
            'name': name,
            'barcode': barcode,
            'author': author
        })
        return redirect(url_for('view_books'))
    return render_template('add_book.html')

# Route to view books
@app.route('/books', methods=['GET'])
def view_books():
    barcode = request.args.get('barcode')
    page = int(request.args.get('page', 1))
    per_page = 50
    barcode_result = None
    barcode_searched = None
    if barcode:
        barcode_result = books_collection.find_one({'barcode': barcode})
        if barcode_result:
            barcode_result['id'] = str(barcode_result['_id'])
        else:
            barcode_searched = barcode
    total_books = books_collection.count_documents({})
    books_cursor = books_collection.find().skip((page-1)*per_page).limit(per_page)
    books = list(books_cursor)
    for book in books:
        book['id'] = str(book['_id'])
    total_pages = (total_books + per_page - 1) // per_page
    return render_template('view_books.html', books=books, barcode_result=barcode_result, barcode_searched=barcode_searched, page=page, total_pages=total_pages)

# Route to delete a book
@app.route('/delete/<book_id>', methods=['POST'])
def delete_book(book_id):
    from bson.objectid import ObjectId
    books_collection.delete_one({'_id': ObjectId(book_id)})
    return redirect(url_for('view_books'))

# Route to edit a book
@app.route('/edit/<book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    from bson.objectid import ObjectId
    book_ref = books_collection.find_one({'_id': ObjectId(book_id)})
    if request.method == 'POST':
        name = request.form['name']
        barcode = request.form['barcode']
        author = request.form['author']
        
        # Update book in MongoDB
        books_collection.update_one(
            {'_id': ObjectId(book_id)},
            {'$set': {'name': name, 'barcode': barcode, 'author': author}}
        )
        return redirect(url_for('view_books'))
    
    book = book_ref
    book['id'] = str(book['_id'])
    return render_template('add_book.html', book=book)

# Route to import Excel data
@app.route('/import_excel', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    
    if file.filename == '':
        return "No file selected"
    
    try:
        # Read Excel file
        df = pd.read_excel(file)
        
        # Insert each row as a document
        for _, row in df.iterrows():
            books_collection.update_one(
                {'barcode': row['barcode_values']},
                {'$set': {
                    'accession_number': row['accession_number'],
                    'title': row['title'],
                    'department': row['department'],
                    'author': row['author'],
                    'department_code': row['department_code'],
                    'barcode': row['barcode_values']
                }},
                upsert=True
            )
        
        return "Data imported successfully."
    except Exception as e:
        return str(e)

# Route to lookup a book by barcode
@app.route('/lookup_barcode', methods=['GET'])
def lookup_barcode():
    barcode = request.args.get('barcode')
    if not barcode:
        return {"error": "No barcode provided"}, 400
    book = books_collection.find_one({'barcode': barcode})
    if not book:
        return {"error": "Book not found"}, 404
    book.pop('_id', None)  # Remove MongoDB's internal ID from the result
    return book

if __name__ == '__main__':
    app.run(debug=True)