# shopify_products_scraper
Scarpe any shopify based store with just by website url

# Product Categorization Scraper

A Python script for scraping product data from Shopify-based websites, categorizing products using LLM, and storing the information in a MySQL database.

## Overview

This script automates several tasks:
1. Extracts all product links from site sitemaps
2. Fetches product data from Shopify's JSON endpoints
3. Uses Meta's Llama 3.1 (via OpenRouter) to categorize products and extract brands
4. Stores all product data in a MySQL database

## Features

- Sitemap parsing to automatically discover product URLs
- LLM-based product categorization (main category > subcategory 1 > subcategory 2)
- Brand extraction from product titles
- Duplicate detection to avoid processing the same products
- Error handling and logging with Telegram notifications
- Connection pooling for database efficiency

## Requirements

- Python 3.x
- MySQL database
- OpenRouter API key

### Required Python Packages

```
requests
beautifulsoup4
mysql-connector-python
lxml
```

## Installation

1. Clone this repository
2. Install required packages: `pip install -r requirements.txt`
3. Set up your MySQL database with the required schema
4. Update the configuration variables at the top of the script

## Usage

Run the script with the target website URL as an argument:

```bash
python scraper.py https://example.com
```

## Configuration

The following parameters can be customized in the script:

- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `YOUR_SITE_URL`: Your website URL (for API attribution)
- `YOUR_APP_NAME`: Your application name (for API attribution)
- Database connection parameters (host, user, password, database name)

## Database Schema

The script assumes a MySQL table called `products` with the following structure:

```sql
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    price DECIMAL(10, 2),
    store VARCHAR(100),
    link VARCHAR(255) UNIQUE,
    image_link VARCHAR(255),
    category VARCHAR(255),
    brand VARCHAR(100),
    out_of_stock BOOLEAN,
    listing_date DATE,
    verified_date DATE,
    end_date DATE,
    compare_data TEXT
);
```

## How It Works

1. The script first extracts product sitemaps from the main sitemap
2. It then parses these sitemaps to get all product URLs
3. For each product URL, it appends `.json` to access the Shopify JSON API
4. Product data is extracted and cleaned
5. The LLM model categorizes the product based on its title
6. All data is stored in the MySQL database

## Notes

- The script includes random delays to avoid overloading the target server
- Duplicate products are detected but still updated with new information
- Error handling and notifications are implemented through a separate module

## License

[MIT]
