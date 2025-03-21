import phpserialize
import unicodedata
import re
import requests



def send_telegram_message(message):
    token = 'your_tokeb'
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    chat_id = '5791231452'
    payload = {
        'chat_id': chat_id,
        'text': message
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")
        print("Response:", response.json())


def generate_permalink(title):
    # Normalize the Unicode string (e.g., é to e)
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')

    # Convert to lowercase
    title = title.lower()

    # Replace spaces and non-acceptable characters with hyphens
    title = re.sub(r'[^a-z0-9]+', '-', title)

    # Remove leading and trailing hyphens
    title = title.strip('-')

    return title
def price_sort(price,currency):
    if currency in price:
        price = price.replace(currency, '').strip()
    if ',' in price:
        price = price.replace(',', '')

    if price is float or price is str:
        price = int(float(price))
    price = int(float(price))
    return price
def php_serialize(data):
    def serialize_value(value):
        if isinstance(value, dict):
            return php_serialize_dict(value)
        elif isinstance(value, list):
            return php_serialize_list(value)
        elif isinstance(value, str):
            return f's:{len(value)}:"{value}";'
        elif isinstance(value, int):
            return f'i:{value};'
        elif isinstance(value, float):
            return f'd:{value};'
        elif value is None:
            return 'N;'
        else:
            raise TypeError(f'Unsupported type: {type(value)}')

    def php_serialize_dict(data):
        items = ''.join(f'{serialize_value(key)}{serialize_value(value)}' for key, value in data.items())
        return f'a:{len(data)}:{{{items}}}'

    def php_serialize_list(data):
        items = ''.join(f'{serialize_value(index)}{serialize_value(value)}' for index, value in enumerate(data))
        return f'a:{len(data)}:{{{items}}}'

    return serialize_value(data)


def create_php_serialized_array(category_intro, category_image, page_title, demo_import):
    data = {
        "category_intro": category_intro,
        "category_image": category_image,
        "page_title": page_title,
        "demo_import": demo_import,
    }

    serialized_data = phpserialize.dumps(data)
    return serialized_data

