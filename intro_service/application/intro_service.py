import argparse
import concurrent
import json
import os
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import datetime as dt
from functools import partial

import requests
import logging
import time
from bs4 import BeautifulSoup
from config import Config as app_config
from language_services.chatglm.chatglm_generation import GlmRequest
from language_services.openai_api.intro_openai import ChatCompletion
from templates import intro_prompt

log_file_path = "application.log"
# Check if the file exists
if os.path.exists(log_file_path):
    os.remove(log_file_path)

# Ensure the log folder exists, create it if not
log_folder = "log"
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
# Create the message log file path with the current date
message_log_file_path = os.path.join(log_folder, f"message_{dt.date.today()}.log")
if os.path.exists(message_log_file_path):
    os.remove(message_log_file_path)

Config = app_config(log_file_path, message_log_file_path)
logger = logging.getLogger('process')
logger.addHandler(Config.log_handler)
logger.setLevel(logging.INFO)
message_logger = logging.getLogger('debug')
message_logger.addHandler(Config.message_handler)
message_logger.setLevel(logging.DEBUG)


def call_ChatGPT(messages, model="gpt-4-turbo-preview", validator=None, thread_num=1, primer="", stream=False,
                 top_p=1, temperature=0.5, max_tokens=3000,
                 api_key=""):
    chatgpt = ChatCompletion(primer,
                             api_key=api_key,
                             max_tokens=max_tokens,
                             model=model,
                             validator=validator,
                             temperature=temperature,
                             max_attempts=1,
                             top_p=top_p,
                             stream=stream
                             )
    responses = chatgpt.batch(messages, n_workers=thread_num)
    return responses[0]


def call_glm(messages, temperature=0.2, top_p=0.9, api_key=None):

    glm = GlmRequest(temperature=temperature,
                     top_p=top_p,
                     api_key=api_key)
    result = glm(message=messages)
    return result


def clean_text(text):
    current_date = "<p>更新时间 " + datetime.now().strftime("%Y年%m月%d日") + "</p>"
    eng_date = "<p>Updated on " + datetime.now().strftime("%B %d, %Y") + "</p>"
    start_index = text.find('{')
    cleaned_json_string = text[start_index:]
    # Remove triple backticks and newline characters
    cleaned_json_string = cleaned_json_string.strip("```").replace('\n', '')
    des_text = json.loads(cleaned_json_string)
    en_text = des_text['enDes'] + eng_date
    zh_text = des_text['zhDes'] + current_date
    return {"text_en": en_text, "text_zh": zh_text}


def simple_intro_gen(api_key, task_option, user_input, model='glm'):
    intro_text = [' ']*len(user_input)
    for inp in range(len(user_input)):
        formatted_input = f'"""{{ {user_input[inp]} }}"""'
        messages = [{"role": "system", "content": task_option["instruction"]["prompt"]},
                    {"role": "user", "content":
                        task_option["generation"]["prompt"]+ '\n' + formatted_input}]
        if model == 'glm':
            intro_text[inp] = call_glm(messages=messages,
                                       temperature=task_option["generation"]["temperature"],
                                       top_p=task_option["generation"]["top_p"],
                                       api_key=api_key)
        else:
            intro_text[inp] = call_ChatGPT(messages=[messages],
                                           temperature=task_option["generation"]["temperature"],
                                           top_p=task_option["generation"]["top_p"],
                                           api_key=api_key)
        intro_text[inp] = clean_text(intro_text[inp])
    return intro_text


def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        message_logger.info(f"File '{file_path}' removed.")
    else:
        message_logger.info(f"File '{file_path}' does not exist.")


def remove_text_from_db(data):
    # data= {'id': 1, 'text': '对于那些在 Remuera 北坡寻求项目或进入立足点且价格低于奥克兰市议会土地价值的人来说'}
    conn = sqlite3.connect(Config.db_path)
    cursor = conn.cursor()
    # cursor.execute("DELETE FROM task_queue WHERE id = ?", (data['id']))
    cursor.execute("DELETE FROM task_queue WHERE id = :id", {"id": data['id']})
    conn.commit()
    conn.close()


def save_result_locally(data):
    # # data= {'id': 1, 'text': '对于那些在 Remuera 北坡寻求项目或进入立足点且价格低于奥克兰市议会土地价值的人来说'}
    # conn = sqlite3.connect(Config.db_path)
    # cursor = conn.cursor()
    # cursor.execute("SELECT text FROM task_queue WHERE id = ?", (data['id'],))
    # text = cursor.fetchone()
    # conn.close()

    with read_lock:
        conn = sqlite3.connect(Config.local_save_db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS task_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, stru_text TEXT, text TEXT)")
        cursor.execute("INSERT INTO task_queue (id, stru_text, text) VALUES (?, ?, ?)",
                       (data['id'], data['stru_text'], data['text']))
        conn.commit()
        conn.close()


def database_exists():
    return os.path.exists(Config.db_path)


def create_database():
    conn = sqlite3.connect(Config.db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS task_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT,"
                   "processed INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()


def get_queue_length():
    conn = sqlite3.connect(Config.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM task_queue")
    length = cursor.fetchone()[0]
    conn.close()
    return length


def get_text_list(country=1, limit=1, ago=10):
    # Define the API URL and headers
    base_url = Config.text_base_url
    headers = {
        "Authorization": f'Bearer {Config.text_base_auth_key}'
    }

    # Initialize variables for pagination
    limit = limit
    ago = ago
    country = country
    complete_list = None

    url = f"{base_url}?limit={limit}&ago={ago}&country={country}"
    try:
        # Send a GET request to the API with pagination
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            response_data = response.json()
            if response_data:
                complete_list = response_data
        else:
            logging.error(f"No valid data. Response status code: {response.status_code}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    if not database_exists():
        create_database()
    if complete_list:
        with read_lock:
            # Process the collected data
            db_conn = sqlite3.connect(Config.db_path)
            cursor = db_conn.cursor()

            for item in complete_list:
                # Check if there is a record with the given id and processed=0
                cursor.execute("SELECT COUNT(*) FROM task_queue WHERE id=? AND processed=1", (item['property_data_id'],))
                count = cursor.fetchone()[0]

                # If no record with processed=1 exists, perform an INSERT OR REPLACE
                if count == 0:
                    cursor.execute("INSERT OR REPLACE INTO task_queue (id, text, processed) VALUES (?, ?, ?)",
                                   (item['property_data_id'], json.dumps(item), 0))

            db_conn.commit()
            db_conn.close()
    else:
        message_logger.error("No valid data to process.")


def fetch_data(country=1, limit=1, ago=10):
    while True:
        sleep_time = 60
        try:
            if database_exists():
                message_logger.info("Try fetch data")
                queue_len = get_queue_length()
                if queue_len < 10:
                    sleep_time = 5
                    message_logger.info("Fetch data")
                    get_text_list(country=country, limit=limit, ago=ago)
                elif queue_len > 100:
                    message_logger.info("Server is busy")
                    # Get data after 10 minutes
                    sleep_time = 600
                else:
                    # Get data every 1 minutes
                    message_logger.info("Expand the queue")
                    sleep_time = 60
                    get_text_list(country=country, limit=limit, ago=ago)
            else:
                message_logger.info(f"Create database")
                get_text_list(country=country, limit=limit, ago=ago)
                sleep_time = 60
        except Exception as e:
            message_logger.error(e)
        time.sleep(sleep_time)


def get_value_from_dict(dictionary, key, default_value=None):
    """
    This function checks if a key exists in a dictionary.
    If the key exists, it returns the value of the key.
    If the key does not exist, it returns a default value.

    :param dictionary: The dictionary to check.
    :param key: The key to look for in the dictionary.
    :param default_value: The value to return if the key does not exist.
    :return: The value of the key if it exists, else the default value.
    """
    return dictionary.get(key, default_value)


def rework_data(data):
    with read_lock:
        conn = sqlite3.connect(Config.db_path)
        cursor = conn.cursor()
        # cursor.execute("DELETE FROM task_queue WHERE id = ?", (data['id']))
        cursor.execute("UPDATE task_queue SET processed = 0 WHERE id = ?", (data['id'],))
        conn.commit()
        conn.close()


def load_valid_data(data_fom_db):
    # Initialize an empty dictionary to store the valid data
    valid_data = {}
    try:
        data_from_file = json.loads(data_fom_db)

        # Check if 'valuation_history' exists in the data and extract it
        cv_list = get_value_from_dict(dictionary=data_from_file, key="valuation_history")
        if cv_list:
            # Sort the list based on the 'valuationDate' key in descending order
            sorted_list = sorted(cv_list, key=lambda x: x['valuationDate'], reverse=True)

            # Get the maximum 2 items
            latest_2_items = sorted_list[:2]
            valid_data = {f"capitalvalue-{item['valuationDate']}": item['capitalValue'] for item in latest_2_items}
            if len(latest_2_items)>1:
                # Calculate the increase percentage in 'capitalValue'
                inc_per = (latest_2_items[0]['capitalValue'] - latest_2_items[1]['capitalValue']) / latest_2_items[1][
                    'capitalValue']
                # Store the 'capitalValue' and 'cvIncrease' in the valid_data dictionary
                valid_data.update({"cvIncrease": inc_per})

        # Check if 'property_data' exists in the data and extract it
        property_data = get_value_from_dict(dictionary=data_from_file, key="property_data")
        if property_data:
            # Define the property attributes to extract
            pro_attr = ["bedrooms", "bathrooms", "carparks", "floorArea", "landArea", "ownershipType", "fullAddress", "propertyCategoryDes", "roofConstruction", "wallConstruction", "buildingAge", "wallCondition", "roofCondition", "propertyContour"]
            # Extract the property attributes and store them in the valid_data dictionary
            prop_data = {attr: property_data.get(attr) for attr in pro_attr}
            valid_data.update(prop_data)

        # Check if 'school_zone' exists in the data and extract it
        school_data = get_value_from_dict(dictionary=data_from_file, key="school_zone")
        if school_data:
            # Initialize an empty dictionary to store the school data
            sch_data = {}
            for sch_d in school_data:
                # Initialize an empty dictionary to store the school attributes
                sch_attr = {}
                # Check if 'polygonInfo' exists in the school data and extract the 'polygonName'
                if 'polygonInfo' in sch_d:
                    polygon_info = json.loads(sch_d['polygonInfo'])
                    if 'polygonName' in polygon_info[0]:
                        polygon_name = polygon_info[0]['polygonName']
                    else:
                        continue
                # Check if 'schoolType' exists in the school data and extract it
                if 'schoolType' in sch_d:
                    school_type = sch_d['schoolType']
                    sch_attr.update({"schoolType": school_type})
                # Check if 'decile' exists in the school data and extract it
                if 'decile' in sch_d:
                    decile = sch_d['decile']
                    sch_attr.update({"decile": decile})
                # Store the school attributes in the sch_data dictionary
                sch_data.update({polygon_name: sch_attr})
            # Store the sch_data in the valid_data dictionary
            valid_data.update(sch_data)

        # Check if 'latest_avm' exists in the data and extract the 'avm'
        avm_data = get_value_from_dict(dictionary=data_from_file, key="latest_avm")
        if avm_data:
            avm = {"HouGarden avm": avm_data['avm']}
            valid_data.update(avm)

        # Check if 'sold_history' exists in the data and extract it
        sold_data = get_value_from_dict(dictionary=data_from_file, key="sold_history")
        if sold_data:
            # Sort the property_sales based on saleDate in descending order
            sorted_sales = sorted(sold_data, key=lambda x: x['saleDate'], reverse=True)
            # Get the latest two sale prices and sale dates if available
            latest_sales = {datetime.strptime(str(sale['saleDate']), '%Y%m%d').strftime('%Y-%m-%d'): sale['salePriceGross'] for sale in sorted_sales[:2]}
            # Store the latest_sales in the valid_data dictionary
            valid_data.update({"latestSale": latest_sales})

        # Check if 'listing_desc' exists in the data and extract it
        description = get_value_from_dict(dictionary=data_from_file, key="listing_desc")
        if description:
            # Define the description attributes to extract
            des_attr = ["description", "brief", "teaser"]
            # Extract the description attributes and clean the 'description' text using BeautifulSoup
            des_data = {attr: description.get(attr) for attr in des_attr}
            des_data['description'] = ' '.join(BeautifulSoup(des_data['description'], "html.parser").stripped_strings)
            # Store the des_data in the valid_data dictionary
            valid_data.update(des_data)
    except Exception as e:
        # Log any exceptions that occur
        logging.error(e)

    # Return the valid_data dictionary
    return valid_data


# A lock for reading from the database
read_lock = threading.Lock()


def run_intro_gen_app(api_key, language_model):
    logger.info("Start processing task")
    logger.info("Loading model...")
    reply_headers = {
        "Authorization": Config.text_reply_auth_key,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    sleep_time = 5
    if not database_exists():
        time.sleep(30)

    while True:
        try:
            with read_lock:
                conn = sqlite3.connect(Config.db_path)
                cursor = conn.cursor()
                # Retrieve the first item from the database
                cursor.execute("SELECT id, text FROM task_queue WHERE processed = 0 ORDER BY id DESC LIMIT 1")
                data = cursor.fetchone()
                if data:
                    # Mark the item as processed
                    cursor.execute("UPDATE task_queue SET processed = 1 WHERE id = ?", (data[0],))
                    message_logger.info(f"ID {data[0]} is being processed.")
                conn.commit()
                conn.close()

            if data:
                start_time = time.time()  # Record the start time
                sleep_time = 5
                data = [{"id": data[0], "text": data[1]}]
                # load_global_model()
                texts = [item['text'] for item in data]
                texts = [json.dumps(load_valid_data(text)) for text in texts]
                ids = [item['id'] for item in data]
                logger.info("start generating...")
                try:
                    result = simple_intro_gen(api_key=api_key, task_option=intro_prompt, user_input=texts, model=language_model)
                    for item, id_val, text_val in zip(result, ids, texts):
                        item.update({'id': id_val, 'stru_text': text_val})

                    # result_list = [{'id': id_val, 'stru_text': text_val, 'text': trans_val} for
                    #                id_val, text_val, trans_val in zip(ids, texts, result)]
                except Exception as e:
                    for item in data:
                        remove_text_from_db({"id": item['id']})
                    logger.error("Failed to generate text.")
                    logger.error(e)
                    continue
                for re in result:
                    try:

                        trans_result = {"text" if key == "text_en" else key:re[key] for key in ["id", "text_en", "text_zh"]}
                        response = requests.post(Config.text_reply_url, data=trans_result, headers=reply_headers, timeout=30)
                        if response.status_code == 200:
                            message_logger.info("****************************************")
                            message_logger.info(trans_result)
                            message_logger.info(response.json())
                            message_logger.info("****************************************")
                            logger.info(f"ID {re['id']} translate is sent successful.")
                        else:
                            logger.info(f"Request failed with status code: {response.status_code}")
                            # rework_data(re)
                            save_result_locally(re)
                    except requests.exceptions.RequestException as e:
                        logger.error(e)
                    remove_text_from_db(re)

                end_time = time.time()  # Record the end time
                interval = end_time - start_time  # Calculate the time interval
                message_logger.info(f"Time Interval: {interval} seconds, Data {data}: ")
            else:
                sleep_time = 60
                logger.info("No data")
        except Exception as e:
            logger.error(e)

        time.sleep(sleep_time)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Description of your script')
    parser.add_argument('--language_model', type=str, default='glm', help='Specify the language model')
    parser.add_argument('--country', type=str, default=1, help='Specify the country code: 1 for NZ, 2 for AU')
    parser.add_argument('--limit', type=str, default=10, help='Specify the limit of the task list')
    parser.add_argument('--ago', type=str, default=20, help='Specify the time range of the task list')
    args = parser.parse_args()

    if args.language_model == 'glm':
        from language_services.chatglm.chatglm_generation import read_api_key_from_config as conf
    else:
        from language_services.openai_api.intro_openai import read_api_key_from_config as conf
    if args.country == 2:
        api_keys = list(conf("AU_Tran").values())
    else:
        api_keys = list(conf("NZ_Tran").values())

    # run_prop_trans_app(language_model=args.language_model, country=args.country, limit=args.limit, ago=args.ago,
    #                    api_key=api_keys[0])

    # Example usage:
    file_to_remove = Config.db_path
    remove_file(file_to_remove)

    with ThreadPoolExecutor(max_workers=len(api_keys)+1) as executor:
        partial_fetch_app = partial(fetch_data, country=args.country, limit=args.limit, ago=args.ago)
        fetch_data_future = executor.submit(partial_fetch_app)
        time.sleep(5)
        partial_run_app = partial(run_intro_gen_app, language_model=args.language_model)
        futures = {executor.submit(partial_run_app, api_key): api_key for api_key in api_keys}

        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(futures):
            api_key = futures[future]
            try:
                future.result()
            except Exception as e:
                message_logger.error(f"Translation with API Key {api_key} failed: {e}")
