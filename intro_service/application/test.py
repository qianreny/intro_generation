import logging
from datetime import datetime
import json
from bs4 import BeautifulSoup
from templates import intro_prompt, brief_prompt
from intro_service import intro_gen, simple_intro_gen


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


def load_valid_data():
    # Initialize an empty dictionary to store the valid data
    valid_data = {}
    try:
        # Define the file path
        file_path = 'example_auckland_2'
        # Open the file and read its content
        with open(file_path, 'r') as file:
            # Load the JSON data from the file
            data_from_file = json.load(file)

        # Check if 'valuation_history' exists in the data and extract it
        cv_list = get_value_from_dict(dictionary=data_from_file, key="valuation_history")
        if cv_list:
            # Sort the list based on the 'valuationDate' key in descending order
            sorted_list = sorted(cv_list, key=lambda x: x['valuationDate'], reverse=True)

            # Get the maximum 2 items
            latest_2_items = sorted_list[:2]
            # Calculate the increase percentage in 'capitalValue'
            inc_per = (latest_2_items[0]['capitalValue'] - latest_2_items[1]['capitalValue']) / latest_2_items[1]['capitalValue']
            # Store the 'capitalValue' and 'cvIncrease' in the valid_data dictionary
            valid_data = {f"capitalvalue-{item['valuationDate']}": item['capitalValue'] for item in latest_2_items}
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


if __name__ == '__main__':
    # test structure data to text generation
    # data = load_valid_data()
    # data_text = json.dumps(data)
    # result = simple_intro_gen(task_option=intro_prompt, user_input=data_text)
    # print(result)

    # test brief intro generation
    data_text = f'''
房地产投资者Realside与上市地主Vicinity Centres达成协议，以1.07亿澳元的价格购买位于珀斯中央商务区17公里外的Maddington Central购物中心。Realside正在寻求股权支持者参与这项投资。

据Street Talk了解，潜在投资者被告知Realside以略高于9700万澳元账面价值的小幅溢价，在非公开交易中获得了这笔投资。然而，收购价格比土地和替代价值低40%以上，也低于Vicinity对该资产的1.22亿澳元最高估值。

Realside的负责人Linda Rudd，前Knight Frank Australia合伙人，与创始人Mark Vonic一起，正在与高净值人士会面。Mark Vonic此前是Primewest的首席投资官。该基金的募集将于5月8日结束。

募资文件中提出了一个基本情景，即五年持有期内8.5%的年现金收益率和15.5%的内部收益率。

通过该资产约三公顷的空置土地，具有广泛的分区，可以容纳建设出租开发、物流、托儿中心、健身房或医疗中心，收益可能会增加。

这个次区域购物中心建于1980年，最后一次翻新是在2020年，占地13公顷。主要租户Woolworths、Coles和Kmart的WALE平均超过八年，为2.07亿澳元的移动平均营业额提供担保。根据向投资者展示的募资文件，特别是Coles正在讨论再续约10年。

潜在的支持者被告知这是一个时机恰到好处的收购，预计从2025年开始收益率将会收紧。在基础设施的推动下，文件指出，其位置距离Maddington火车站不到600米，预计将是西澳110亿澳元Metronet项目的受益者之一。

Maddington的大约22万主要贸易区人口大约是其同行在次区域购物中心的两倍，这些购物中心在其他行业的机遇中提供最高的平均收益率。

对于总市值达143.6亿澳元的Vicinity来说，这是一笔小交易，但应该会出现在其6月30日的报告中。

在Vicinity以5.9%的溢价出售了另一个位于珀斯郊区的购物中心Dianella Plaza后，这笔交易才得以实现。

买家，西澳的物业管理公司Greenpool Capital同意在12月支付7630万澳元，并在3月结算。
  '''
    result = intro_gen(task_option=brief_prompt, user_input=data_text, polish_time=0)
    print(result)
