import os

# Set the CUDA_VISIBLE_DEVICES variable
# os.environ['CUDA_VISIBLE_DEVICES'] = "6,7"
import logging
from logging.handlers import TimedRotatingFileHandler


class Config():
    def __init__(self, log_path="application.log", message_log_path="message.log"):

        # Configure the log file rotation
        self.log_handler = TimedRotatingFileHandler(log_path, when="D", interval=1, backupCount=7)
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s:%(levelname)s] %(message)s'))
        # Configure the log file rotation
        self.message_handler = TimedRotatingFileHandler(message_log_path, when="D", interval=1, backupCount=30)
        self.message_handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s:%(levelname)s] %(message)s'))

        # Define the data path
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "offline_prop_queue.db")
        self.local_save_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unsuccessful_task_queue.db")
        self.model_path = os.path.join(os.path.dirname(__file__), 'deploy_model')
        self.model_path = os.path.join(self.model_path, "checkpoint-143880")

        self.base_model_path = os.path.join(os.path.dirname(__file__), 'base_model')

        # self.available_gpu = 1,2
        self.task_handler_url = "3.105.148.92:1783/trans_proxy"
        # self.trans_process_url = "54.206.253.30:1256/property_trans"

        self.text_base_url = "https://thavetest.hougarden.com/api/v0.0.2/ai/seo_description/property"
        self.text_reply_url = "https://api1.hougarden.com/api/v4.5.0/ai/translate/property"

        #testing to be removed after testing
        # self.text_base_url = "https://thavetest.hougarden.com/iter_property"
        # self.text_reply_url = "https://test3.hougarden.com/api/v4.5.0/ai/translate/property"

        self.text_base_auth_key = "Bearer cb97f9d379e2c823bc5054c00ed19fd2523924433276040fd3d5d1a14bbbd79c"
        self.text_reply_auth_key = "Public QjQxbjczaXZiay13MFc4T3lFa20xLXdobW5FOXc2NmU6cHM0ejFhNGM1Si1OcERjNnVqWDY3LVlOeUJnWDhEN28="
        self.batch_size = 4

        self.instance_id = "i-0ad8c9907b74591f7"

        # self.task_queue_path = os.path.join(os.path.dirname(__file__), "offline_prop_queue.db")
        # self.local_save_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unsuccessful_task_queue.db")
