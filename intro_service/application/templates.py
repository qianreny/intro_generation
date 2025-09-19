import pandas as pd


def get_common_words():
    file_path = 'common_words.csv'
    try:
        common_words = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return [], []
    eng_column = common_words['ENG']
    chn_column = common_words['CHN']
    translation_strings = [f"{eng}翻译成{chn}" for eng, chn in zip(eng_column, chn_column)]
    chn_column = list(chn_column)
    chn_column = list(set(chn_column))
    return translation_strings, chn_column


common_words_paris, chinese_words = get_common_words()


news_task = {"trans_promt": ("面向华人读者，以专业的视角流畅的文笔编译中文新闻。不要道歉。查看新闻的发生国家，"
                             "在涉及金钱时注意货币类型是澳元还是其他货币。"
                             "保留原文的所有内容，不要解释。"
                             "如果新闻发生在澳大利亚，则货币单位是澳元，如果新闻发生在新西兰，则货币单位是是纽币。"
                             "在翻译过程中，"
                             "一些名词不需要翻译，包括人名、地名、机构等等。"
                             "请注意，人名使用英文，地区使用英文，机构名称使用英文，缩写使用英文。"
                             "出现大写的英文单词，思考是否使用英文。"
                             "而著名地标景点的名称保持原文不变。"
                             "在翻译过程中，不要将地名（如Chatswood，Mission Bay，Mt Eden，Epsom，Parnell，"
                             "Takapuna， Remuera，Omaha，Te Atatu，CV等等）、"
                             "人名（如Mary，Dan，等等）翻译成中文，请保持它们的英文形式。"
                             "房地产翻译中常用的词汇：" + "；".join(common_words_paris) + "。"),
             "edit_prompt": ("根据以下文章撰写符合海外华人阅读的中文新闻，行文流畅，保留细节并突出重点。不要解释。"
                             "人名(Marry)使用英文，地名 （Chatswood）使用英文，机构名称，缩写使用英文。"
                             "发生在澳大利亚的新闻里的货币单位是澳元，发生在新西兰的新闻是纽币。不要道歉。")}

property_task = {"trans_promt": ("作为一位专业的房地产翻译员，面向华人买家，您的任务是将英文翻译成中文。"
                                 "请将包含 ‘after … years’ 的句子翻译成中文，确保明确表达 ‘…年后’ 这个时间点。"
                                 "在翻译过程中，"
                                 "一些名词不需要翻译，包括人名、地名、机构等等。"
                                 "请注意，人名使用英文，地区使用英文，机构名称使用英文，缩写使用英文。"
                                 "出现大写的英文单词，思考是否使用英文。"
                                 "而著名地标景点的名称保持原文不变。"
                                 "在翻译过程中，不要将地名（如Chatswood，Mission Bay，Mt Eden，Epsom，Parnell，"
                                 "Takapuna， Remuera，Omaha，Te Atatu，CV等等）、"
                                 "人名（如Mary，Dan，等等）翻译成中文，请保持它们的英文形式。"
                                 "房地产翻译中常用的词汇：" + "；".join(common_words_paris) + "。"
                                 "默认货币单位为纽币，确保所有的数字金额用$符号表示。"
                                 ),
                 "common_words": ("请只回复翻译文本，不要解释。不要增加内容。不要道歉。"),
                 "error_prompt": ("指出下文哪里不符合中文书写习惯，或者哪里不符合华人阅读习惯。如果原文有这些词汇，不需要改动: "
                                  + "；".join(chinese_words) + "。"
                                  "$符号表示纽币，确保所有的金额都用$符号表示。"
                                  "请注意，人名使用英文，地区使用英文，机构名称使用英文，缩写使用英文。"
                                  "文中的英文词组不需要翻译。"
                                  "不要增加内容。"),
                 "edit_prompt": ("根据以上问题重写中文房源广告的正文，行文流畅，符合华人阅读习惯。文中的英文词组不需要翻译或者改写。"
                                 "人名使用英文 ，地名使用英文，机构名称，缩写使用英文。"
                                 "风格严谨，广告有吸引力。不需要加小标题。"
                                 "包括所有内容。"
                                 # "如果原文有这些词汇，不需要改动，没有的话，不需要增加: "
                                 #  + "；".join(chinese_words) + "。"
                                 "将文字分段重写成html格式，用来在网页展示。只写body部分，不需要header。从<p>开始，到</p>结束。"
                                 "不要解释。不要增加内容。不要道歉。"
                                 "默认货币单位为纽币。"
                                 "如果原文没有价格，请不要增加价格内容。"
                                 "")}

intro_prompt = {
    "instruction": {
        "prompt": "As a professional property guru, your assignment is to craft a detialed and clear "
                  "text based on the given structured data. The text should encompass key "
                  "property highlights, such as the school zone, title, capital value (CV) "
                  "increase speed, and other pertinent information. "
                  "Please provide the summary in both Chinese and English."
                  "请根据数据写一份详细的描述，包含所有数据，适当加些修辞手法。"
                  "一些名词不需要翻译，包括人名、地名、机构等等。"
                  # "请注意，人名使用英文，地区使用英文，机构名称使用英文，缩写使用英文。"
                  # "出现大写的英文单词，思考是否使用英文。"
                  # "而著名地标景点的名称保持原文不变。"
                  # "在翻译过程中，不要将地名（如Chatswood，Mission Bay，Mt Eden，Epsom，Parnell，"
                  # "Takapuna， Remuera，Omaha，Te Atatu，CV等等）、"
                  # "人名（如Mary，Dan，等等）翻译成中文，请保持它们的英文形式。"
                  "文本共分成三部分。每部份是一个段落。"
                  "第一部分介绍房源基本信息（房间数，外墙，屋顶，地契，等等）。"
                  "第二部分介绍政府估价历史，后花园估价，最近售出历史，capitalValue增长百分比，等等。"
                  "第三部分介绍校网相关，评分，学校，等等。"
                  "介绍过程要包含所有数据信息。"
                  "请回复好的，如果你明确了解了任务要求。",
        "temperature": 0.2,
        "top_p": 0.75,
    },
    "generation": {
        "prompt": f"""
                请只回复文本，不要解释。不要增加内容。不要道歉。Please only return the text, no explanations。
                请回复一份英文描述与一份中文描述。
                内容详细并包括所有数据内容。
                房地产翻译中常用的词汇：{"；".join(common_words_paris)}。
                默认货币单位为纽币，确保所有的数字金额用$符号表示。
                不要提到联系方式，不要提到中介信息。
                不要小标题。
                介绍过程要包含所有提供的数据信息。但不要重复信息。
                文本共分成三部分。每部份是一个段落。
                第一部分介绍房源基本信息（房间数，外墙，屋顶，地契，等等）。
                第二部分介绍政府估价历史，后花园估价，最近售出历史，capitalValue增长百分比，等等。
                第三部分介绍校网相关，评分，学校，等等。
                将文字分段重写成html格式，用来在网页展示。只写body部分，不需要header。从<p>开始，到</p>结束。
                用以下json格式回复：'''{{"enDes":"" , "zhDes":"" }}'''
            """,
        "temperature": 0.2,
        "top_p": 0.9,
    },
    "polish": {
        "prompt": "Identify areas in the following text that deviate from standard writing conventions,"
                  " highlighting aspects that may not align with typical Chinese reading habits. "
                  "Additionally, pinpoint aspects in the English text that do not adhere "
                  "to common English writing conventions. "
                  "请指出以下文本中哪些地方违反了标准写作惯例，"
                  "特别关注可能不符合一般中文阅读习惯的地方。同时，指出英文文本中不符合常见英语写作惯例的地方。"
                  "如果原文有这些词汇，不需要改动: " + "；".join(chinese_words) + "。"
                  "默认货币单位为纽币，确保所有的数字金额用$符号表示。",
        "temperature": 0.75,
        "top_p": 0.3,
    },
    "edit": {
        "prompt": "根据以上问题重写房源描述的正文，行文流畅。文中的英文词组不需要翻译或者改写。"
                  "默认货币单位为纽币，确保所有的数字金额用$符号表示。"
                  "不要加小标题。不需要解释。不要增加内容。不要道歉。"
                  "在中文和英文描述中都使用同样的分段格式："
                  "第一段写房源基本信息描述，第二段写房源的价格相关，cv增长速度，avm等等。第三段写房源学区信息。"
                  "请回复一份英文描述与一份中文描述。",
        "temperature": 0.9,
        "top_p": 0.2,
    },
    "common_words": "",

    "polish_edit": {
        "system": "Identify areas in the following text that deviate from standard writing conventions,"
                  " highlighting aspects that may not align with typical Chinese reading habits. "
                  "Additionally, pinpoint aspects in the English text that do not adhere "
                  "to common English writing conventions. "
                  "请指出以下文本中哪些地方违反了标准写作惯例，"
                  "特别关注可能不符合一般中文阅读习惯的地方。同时，指出英文文本中不符合常见英语写作惯例的地方。"
                  "如果原文有这些词汇，不需要改动: " + "；".join(chinese_words) + "。"
                  "默认货币单位为纽币，确保所有的数字金额用$符号表示。"
                  "根据找到的问题重写房源描述的正文，行文流畅。文中的英文词组不需要翻译或者改写。"
                  "不要提到联系方式，不要提到中介信息。",
        "prompt": "请根据所给的内容回复一份英文描述与一份中文描述。"
                  "默认货币单位为纽币，确保所有的数字金额用$符号表示。"
                  "不需要解释。不要增加内容。不要道歉。"
                  "在中文和英文描述中都使用同样的分段格式："
                  "文本共分成三部分。每部份是一个段落。"
                  "第一部分介绍房源基本信息（房间数，外墙，屋顶，地契，等等）。"
                  "第二部分介绍政府估价历史，后花园估价，最近售出历史，等等。"
                  "第三部分介绍校网相关，评分，学校，等等。"
                  "介绍过程要包含所有数据信息。"
                  "不要小标题。",
        "temperature": 0.9,
        "top_p": 0.2,
    },
}

brief_prompt = {
    "instruction": {
        "prompt": "请根据文章内容，撰写广告语来突出五到八个物业的优点，例如：优越地理位置、海滨瑰宝、高端优雅奢居、8年新现代别墅、醇熟配套、"
                  "顶级教育资源、独立产权、新油漆、梦幻北向别墅、等等，创作一个中文房源广告。不需要提售卖方式。"
                  "不要加【】，不要加·。用空格分割每个优点，字数在50个字以内。适当加广告修辞。给人以积极的印象。"
                  "广告既要传达物业的特点，也要激发了潜在买家的兴趣，有效地吸引目标受众的注意力。"
                  "请回复好的，如果你明确了解了任务要求。"
                  "以下是一些广告语例子：{宝藏私密舒居 506㎡全幅地 邻近繁华中心&Dominion Rd}、"
                  "{大户型砖瓦别墅 543㎡全幅地 美妙户外空间 位踞中心地段 公私好校云集 社区氛围友好 业主必售 大家庭自住首选！}、"
                  "{现代梦幻舒邸 自然采光充沛 大牌Bosch电器 内外空间灵动过渡 步行至学校&商圈 用心诠释美好生活！}、"
                  "{经典别墅焕然新生 雪松木weatherboard 中心人气地段 180度壮丽水景 公私好校荟萃 生活如度假般美妙！}"
                  ,
        "temperature": 0.75,
        "top_p": 0.2,
    },
    "generation": {
        "prompt": "请只回复广告语，不要解释。不要增加内容。不要道歉。"
                  "不要加【】，不要加·。用空格分割每个优点。"
                  "字数在50个字以内。优点需要具体到细节。",
        "temperature": 0.9,
        "top_p": 0.3,
    }
}
