import requests
import json
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling
import site_value_m
import traceback
import logging
from datetime import datetime
import time
import re
import sys
import xml.etree.ElementTree as ET
import random


system_prompt = '''you are an AI model tasked with categorizing products and extracting their brands based on product titles. Given a product title, you should output the main category, sub-category 1, and sub-category 2 in the following hierarchical format: main_category > sub_category_1 > sub_category_2. Additionally, extract the brand of the product.

Instructions:
Categorization:

Main Category: Identify the primary category of the product (e.g., Electronics, Clothing, Home & Kitchen).
Sub-Category 1: Identify the first sub-category within the main category.
Sub-Category 2: Identify the second sub-category within the first sub-category.
Brand Extraction:

Extract the brand from the product title. The brand is typically the first identifiable word or phrase that represents a known brand.
Output Format:

Structure the output in JSON format with the following fields:
main_category: The primary category of the product.
sub_category_1: The first sub-category within the main category.
sub_category_2: The second sub-category within the first sub-category.
brand: The brand of the product.
Examples:
Example 1:
Input: "Samsung Galaxy S21 Ultra 5G Smartphone"
Output:
{
  "main_category": "Electronics",
  "sub_category_1": "Mobile Phones",
  "sub_category_2": "Smartphones",
  "brand": "Samsung"
}
Example 2:
Input: "Nike Air Max 270 Running Shoes"
Output:
{
  "main_category": "Clothing",
  "sub_category_1": "Footwear",
  "sub_category_2": "Running Shoes",
  "brand": "Nike"
}
Example 3:
Input: "Apple MacBook Pro 16-inch Laptop"
Output:
{
  "main_category": "Electronics",
  "sub_category_1": "Computers",
  "sub_category_2": "Laptops",
  "brand": "Apple"
}
Edge Cases and Error Handling:
If a title contains multiple potential brands, choose the most prominent one based on common usage.
If a category or sub-category is unclear, use "Unknown" as a placeholder.
Ensure the JSON output is correctly formatted even if certain fields cannot be confidently identified. 
THINGS NOT TO INSERT - 
*NO OTHER WORDS JUST JSON FORMAT
*PROGRAMMING CODES
'''

OPENROUTER_API_KEY = 'your api address'
YOUR_SITE_URL = 'website'
YOUR_APP_NAME = 'name of the site'

db = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5, #Set the pool size to 20 according to your expected load
    host="ipaddress", #change to localhost when push to production only if you host on same vps
    user="admin",
    password="admin",
    database="admin"
)

def extract_product_sitemap(main_sitemap_url):
    try:
        # Fetch the sitemap
        main_sitemap_url = f"{main_sitemap_url}/sitemap.xml"
        response = requests.get(main_sitemap_url)
        response.raise_for_status()  # Raise an error if the request failed

        # Parse the sitemap XML
        root = ET.fromstring(response.content)

        # Namespace for parsing (defined in the XML)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Find all <loc> elements
        product_sitemaps = []
        for sitemap in root.findall('ns:sitemap', namespace):
            loc = sitemap.find('ns:loc', namespace).text
            if 'sitemap_products_' in loc:  # Check for product sitemap URLs
                product_sitemaps.append(loc)

        return product_sitemaps
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def send_message(prompt, system_prompt):
    max_tokens = 250
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": f"{YOUR_SITE_URL}",
            "X-Title": f"{YOUR_APP_NAME}",
        },
        data=json.dumps({
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "system", "content": system_prompt}
            ],
            "max_tokens": max_tokens
        })
    )

    if response.status_code == 200:
        try:
            response_data = response.json()
            return response_data["choices"][0]["message"]["content"]
        except Exception as e:
            tb = traceback.format_exc()
            error_message = f"An error occurred: {e}\nTraceback details:\n{tb}"
            return 'none'
    else:
        print(f"Error: {response.status_code}")
        return f"Error: {response.status_code}"



def fetch_product_data(api_url):
    try:
        # Fetch the JSON file from the API or link
        response = requests.get(api_url, timeout=10)  # Add a timeout to prevent hanging requests
        if response.status_code == 200:
            # Try to parse the JSON response
            try:
                return response.json()
            except requests.exceptions.JSONDecodeError:
                print(f"Error: Failed to parse JSON for URL: {api_url}")

                return None
        else:
            print(f"Failed to fetch data. Status code: {response.status_code} for URL: {api_url}")
            site_value_m.send_telegram_message(
                f"Failed to fetch data. Status code: {response.status_code} for URL: {api_url}")
            return None
    except requests.exceptions.RequestException as e:
        # Handle other exceptions like timeout
        print(f"Error: An exception occurred while fetching data from {api_url}. Details: {e}")
        site_value_m.send_telegram_message(f'Error: An exception occurred while fetching data from {api_url}. Details: {e}')
        return None

def product_data_conv(links, store , cursor ,connection , cursor_1):
    data = []
    today_date = datetime.today()
    end_date = datetime.strptime('2025-09-29', '%Y-%m-%d')  # Example end date
    random_int = random.randint(20, 30)
    try:
        for link in links:
            time.sleep(int(random_int))
            try:
                if 'cdn.shopify.com' in link or link is None:
                    continue
                # Check if the link already exists in the database
                cursor_1.execute("SELECT COUNT(*) FROM products WHERE link = %s", (link,))
                result = cursor_1.fetchone()
                if result[0] > 0:
                    print(f"Link already exists in the database: {link}, skipping.")
                    already = True
                else:
                    already = False

                link_1 = f'{link}.json'
                product_data = fetch_product_data(link_1)
                if product_data:
                    # Access specific details from the JSON
                    title = product_data["product"]["title"]
                    title = title.strip()
                    body_html = product_data["product"]["body_html"]
                    price = product_data["product"]["variants"][0]["price"]  # Assuming the first variant
                    try:
                        price_currency = product_data["product"]["variants"][1]["price_currency"]
                    except:
                        price_currency = product_data["product"]["variants"][0]["price_currency"]
                    if price_currency != 'LKR':
                        continue
                    image_src = product_data["product"]["image"]["src"]
                    body_html = body_html.encode("utf-8")
                    # Use BeautifulSoup to remove HTML tags
                    soup = BeautifulSoup(body_html, 'html.parser')
                    # Extract plain text from the HTML content
                    body_html = soup.get_text()
                    # Remove emojis and non-ASCII characters
                    # This regex removes characters outside the range of basic Latin and space
                    body_html = re.sub(r'[^\x00-\x7F]+', '', body_html)
                    # Print the extracted data
                    print("Title:", title)
                    print(f"Processing link: {title}")
                    if already:
                        category = 'other'
                        brand = 'other'
                        print('Dont adding category as it already check')
                    else:
                        output = send_message(title, system_prompt)
                        print(f"Output from send_message: {output}")
                        if output is None or output.lower() == 'none':
                            print("Output is None or 'none', skipping this product.")
                            category = 'other'

                        if 'json' in output:
                            output = output.replace('json', '')
                            print(f"Cleaned output: {output}")

                        try:
                            pr_data = json.loads(output)
                            print(f"Parsed JSON data: {pr_data}")
                        except json.JSONDecodeError as e:
                            logging.error("JSON decoding error: %s", e)
                            category = 'other'
                        try:
                            main_category = pr_data.get('main_category', 'Unknown')
                            sub_category_1 = pr_data.get('sub_category_1', 'Unknown')
                            sub_category_2 = pr_data.get('sub_category_2', 'Unknown')
                            category = f'{main_category},{sub_category_1},{sub_category_2}'
                            brand = pr_data.get('brand', 'Unknown')
                            print(f"Category: {category}, Brand: {brand}")
                        except:
                            category = 'other'
                    out_of_stock = 'FALSE'
                    product = (
                        title, body_html, price, store, link, image_src,
                        category, brand, out_of_stock, today_date.strftime('%Y-%m-%d'),
                        today_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d'), None)
                    print(f"Appending product: {product}")
                    data.append(product)
                    insert_data(cursor, data, connection)
                    connection.commit()
                    print('Data added successfully')
            except Exception as e:
                print(f"Error processing link {link}: {e}")
                site_value_m.send_telegram_message(f'Error while {link}: and error is {e}')
                continue
    finally:
        print('Succed at data Entry')



def fetch_sitemap_links(sitemap_url):
    if isinstance(sitemap_url, list):  # Check if it's a list
        all_links = []
        for url in sitemap_url:  # Loop through each URL in the list
            response = requests.get(url)
            response.raise_for_status()  # Ensure we handle bad responses
            soup = BeautifulSoup(response.content, 'xml')
            # Extracting the links
            links = [loc.text for loc in soup.find_all('loc')]
            all_links.extend(links)  # Add extracted links to the main list
        return all_links
    else:
        # Handle the case when a single URL is passed
        response = requests.get(sitemap_url)
        response.raise_for_status()  # Ensure we handle bad responses
        soup = BeautifulSoup(response.content, 'xml')
        # Extracting the links
        links = [loc.text for loc in soup.find_all('loc')]
        return list(links)


def insert_data(cursor, data, connection):
    try:
        cursor.execute("USE main_scrape") # any database name
        query = """
        INSERT INTO products (title, description, price, store, link, image_link, category, brand, out_of_stock, listing_date, verified_date, end_date, compare_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            description = VALUES(description),
            price = VALUES(price),
            image_link = VALUES(image_link),
            out_of_stock = VALUES(out_of_stock),
            listing_date = VALUES(listing_date),
            verified_date = VALUES(verified_date),
            end_date = VALUES(end_date)
        """
        cursor.executemany(query, data)
        connection.commit()
        print("Data inserted successfully.")
    except Error as e:
        connection.rollback()
        logging.error(f"Error while inserting data: {e}")
        site_value_m.send_telegram_message(f'Error while inserting data: and error is {e}')

    finally:
        print('Data added to the database')


def main(site_name, store_name):
    all_sitemaps = extract_product_sitemap(site_name)
    connection = db.get_connection()
    cursor = connection.cursor()
    cursor_1 = connection.cursor()
    for sitemap_url in all_sitemaps:  # Loop through each URL
        all_links = fetch_sitemap_links(sitemap_url)  # Process each sitemap
        print(len(all_links))
        product_data_conv(all_links, store_name ,cursor ,connection , cursor_1)
    connection.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a site URL as an argument.")
        sys.exit(1)
    site_name = sys.argv[1]
    store_name = site_name.replace('https://', '').replace('www.', '')  # Just cleaning the URL a bit
    main(site_name, store_name)


