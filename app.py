import os # OS Module
import psycopg2 # PostgreSQL Connector
from datetime import datetime, timezone # Datetime Module
from dotenv import load_dotenv # .env file reader
from flask import Flask, request, render_template # Flask Web Framework

# PostgreSQL Queries

CREATE_PRODUCTS_TABLE = ("CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, name TEXT);")

INSERT_PRODUCT_RETURN_ID = ("INSERT INTO products (name) VALUES (%s) RETURNING id;")

CREATE_REVIEWS_TABLE = ("CREATE TABLE IF NOT EXISTS reviews (product_id INTEGER, rating REAL, date TIMESTAMP, FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE, feedback TEXT);")

INSERT_REVIEWS = ("INSERT INTO reviews (product_id, rating, date, feedback) VALUES (%s, %s, %s, %s);")

GLOBAL_NUMBER_OF_REVIEWS = ("SELECT COUNT(*) FROM reviews;")

PRODUCT_NAME = ("SELECT name FROM products WHERE id = (%s);")
PRODUCT_NUMBER_OF_REVIEWS = ("SELECT COUNT(*) FROM reviews WHERE product_id = (%s);")
PRODUCT_AVERAGE_RATING = ("SELECT AVG(rating) as average FROM reviews WHERE product_id = (%s);")


DELETE_PRODUCT = ("DELETE FROM products WHERE id = (%s);")

# USE --> ALTER SEQUENCE produtos_id_seq RESTART WITH 1; <-- TO RESET SERIAL ID

# Load .env file
load_dotenv()

# PostgreSQL Connection
url = os.environ.get('DATABASE_URL') 
connection = psycopg2.connect(url)
app = Flask(__name__)

# Home Page
@app.route("/")
def home():
    return "<h3>This api receives JSON product reviews and ratings, and stores them in a PostgreSQL database.<h3>"

# Add Product
# JSON Example: {"name": "Product Name"}
@app.post("/api/products")
def create_product():
    data = request.get_json()
    name = data["name"]
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_PRODUCTS_TABLE)
            cursor.execute(INSERT_PRODUCT_RETURN_ID, (name,))
            product_id = cursor.fetchone()[0]
    return {"id": product_id, "message": f"Product: {name} added to list."}, 201

# Add Review
# JSON Example: {"product": 1, "rating": 4.5, "date": "01-01-2021 00:00:00", "feedback": "This is a review."} *date is optional
@app.post("/api/reviews")
def add_temp():
    data = request.get_json()
    rating = data["rating"]
    product_id = data["product"]
    feedback = data["feedback"]

    # Optional Date
    try:
        date = datetime.strptime(data["date"], "%d-%m-%Y %H:%M:%S")
    except KeyError:
        date = datetime.now(timezone.utc)
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_REVIEWS_TABLE)
            cursor.execute(INSERT_REVIEWS, (product_id, rating, date, feedback))
    return {"message": "Your review was successfully submited"}, 201

# Get Total Reviews
@app.get("/api/total-reviews")
def get_total_reviews():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(GLOBAL_NUMBER_OF_REVIEWS)
            total_reviews = cursor.fetchone()[0]
    return {"total_reviews": total_reviews}, 200

# Get Product Info
@app.get("/api/product/<int:product_id>")
def get_product_info(product_id):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(PRODUCT_NAME, (product_id,))
            product_name = cursor.fetchone()[0]
            cursor.execute(PRODUCT_NUMBER_OF_REVIEWS, (product_id,))
            number_of_reviews = cursor.fetchone()[0]
            cursor.execute(PRODUCT_AVERAGE_RATING, (product_id,))
            average_rating = cursor.fetchone()[0]
    return {"product_name": product_name, "number_of_reviews": number_of_reviews, "average_rating": average_rating}, 200

# Delete Product
@app.delete("/api/product/<int:product_id>")
def delete_product(product_id):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(PRODUCT_NAME, (product_id,))
            name = cursor.fetchone()[0]
            cursor.execute(DELETE_PRODUCT, (product_id,))
    return {"message": f"Product named {name} with id: {product_id} was deleted."}, 200

# Get Products List
@app.get("/api/products")
def get_products():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM products;")
            products = cursor.fetchall()
            products_names = ["joao", "jose", "maria"]
    # cria uma lista com os nomes joao jose e maria
#    return {"products": products}, 200
    return render_template("index.html", products=products_names)






# Rename Product
# JSON Example: {"name": "New Product Name"}
@app.put("/api/product/<int:product_id>")
def rename_product(product_id):
    data = request.get_json()
    name = data["name"]
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(PRODUCT_NAME, (product_id,))
            old_name = cursor.fetchone()[0]
            cursor.execute("UPDATE products SET name = (%s) WHERE id = (%s);", (name, product_id))
    return {"message": f"Product named {old_name} with id: {product_id} was renamed to {name}."}, 200

# Get Product Reviews List
@app.get("/api/reviews/<int:product_id>")
def get_reviews(product_id):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM reviews WHERE product_id = (%s);", (product_id,))
            reviews = cursor.fetchall()
    return {"reviews": reviews}, 200

## next steps would be to add a user table and column to authenticate the reviews
## and add more info to products themselves, like price, description, etc.
## another nice step is to add a frontend to the api, using flask_bootstratp for example
