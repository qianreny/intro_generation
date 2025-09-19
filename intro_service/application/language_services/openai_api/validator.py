import json, logging, re

# Set the logging level to DEBUG, INFO, ERROR
logging.basicConfig(level=logging.INFO)


def get_json_object(text):
    try:
        content = ''.join(text)
        start_index = content.find('{')
        end_index = content.rfind('}')
        valid_json_data = content[start_index:end_index + 1]
        json_data = json.loads(valid_json_data)
        return json_data
    except:
        return None


def get_json_object_remove_repeat_json(text):
    # Define the regular expression pattern to match JSON objects
    pattern = r'({.*?})'

    # Find all matches of the pattern in the text
    matches = re.findall(pattern, text, re.DOTALL)

    # Attempt to parse each match as JSON
    json_forms = []
    for match in matches:
        try:
            json_form = json.loads(match)
            json_forms.append(json_form)
        except json.JSONDecodeError:
            return None  # Ignore if unable to parse as JSON

    return json_forms[0]


class Validator:
    def __init__(self, type):
        self.type = type

        if type == "translate":
            self.valid_key_list = None
            self.valid_value_list = None
        elif type == 'summarise':
            # self.valid_key_list = ['Summary:']
            self.valid_key_list = None
            self.valid_value_list = None
        pass

    def __call__(self, text):
        try:
            # pending to add validation
            return True
            json_object = get_json_object(text)
            # 1. Check if the text is a json format string
            if json_object is None or not isinstance(json_object, dict):
                raise ValueError(f"{self.type} Validator: Not JSON")

            # 2. Check if all keys are present in the JSON object
            if not all(key in json_object for key in self.valid_key_list):
                raise ValueError(f"{self.type} Validator: Key invalid")

            # 3. check inside the value
            if self.valid_value_list is not None:
                all_values_valid = all(
                    isinstance(inner_v, dict) and all(key in self.valid_value_list for key in inner_v.keys())
                    for inner_v in json_object.get(self.valid_key_list, [])
                )
                if not all_values_valid:
                    raise ValueError(f"{self.type} Validator: Value invalid")

            # Passed the 3 checks
            logging.debug(f"{self.type} Validator: Pass")
            return True
        except ValueError as err:
            logging.error(f"\nError: {err}")
            logging.error(f"Response Text is: {text}")
            logging.error(f"{self.type} Validate: Fail")

        return False
