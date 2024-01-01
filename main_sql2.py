import requests
import selectorlib
import smtplib, ssl
import os
import time
import psycopg2
from psycopg2 import sql

URL = "https://programmer100.pythonanywhere.com/tours/"

# Database connection parameter
db_params = {'dbname' : 'data',
             'user' : '',
             'password' : '',
             'host' : '',
             'port' : ''}

def connect_to_db():
    return psycopg2.connect(**db_params)

#create table if don't exist
def create_table(cursor):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS data (
    id SERIAL PRIMARY KEY,
    data_text TEXT NOT NULL
    );
    """

    cursor.execute(create_table_query)

def insert_into_db(cursor, extracted):
    insert_query = sql.SQL("INSERT INTO data (data_text) VALUES (%s);")
    cursor.execute(insert_query, (extracted,))


def scrape(url):
    """Scrape the page source from the URL"""
    response = requests.get(url)
    source = response.text
    return source


# Extract name of tours with id from web page
def extract(source):
    extractor = selectorlib.Extractor.from_yaml_file("extract.yaml")
    value = extractor.extract(source)["tours"] #tours is key dictionary of extract.yaml
    return value


# Send email if get the tours value
def send_email(message):
    host = "smtp.gmail.com"
    port = 465

    username = ""
    passw = ""

    receiver = ""
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(host, port, context=context) as server :
        server.login(username, passw)
        server.sendmail(username, receiver, message)
    print("Email was sent!")


# Store to data.txt
def store_in_file(extracted):
    with open("data.txt", "a") as file:
        file.write(extracted + "\n")

# Store to sql database
def store_in_db(extracted, cursor):
    insert_into_db(cursor, extracted)

# Read data.txt
def read():
    with open("data.txt", "r") as file:
        return file.read()

if __name__ == "__main__":
    #connect to database
    connection = connect_to_db()
    cursor = connection.cursor()

    #ensure the table exist
    create_table(cursor)

    #run program non stop
    while True:
        scraped = scrape(URL)
        extracted = extract(scraped)
        print(extracted)

        content = read()

        print(f"Content in file: {content}")
        if extracted != "No upcoming tours":
            if extracted not in content:
                print(f"Event found: {extracted}")
                # Store in db sql
                store_in_db(extracted, cursor)

                # Send email
                send_email(message=f"Hey, new event was found {content}!")
            else:
                print("Event already in content, skipping.")
        else:
            print("No upcoming tours.")

        # Commit changes to database and sleep
        connection.commit()
        time.sleep(2)

    # Close database connection when the script end
    cursor.close()
    connection.close()