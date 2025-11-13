import os

from config.config_file_loader import ConfigYamlLoader

class UserInfoConfig:

    def __init__(self, config):

        self.ID = config['user']['id']
        self.NAME = config['user']['name']
        self.FARM_ID = config['user']['farm_id']
        self.LOCATION = config['user']['location']

        self.sido_map_full = {
            11: "서울특별시",
            26: "부산광역시",
            27: "대구광역시",
            28: "인천광역시",
            29: "광주광역시",
            30: "대전광역시",
            31: "울산광역시",
            36: "세종특별자치시",
            41: "경기도",
            42: "강원특별자치도",  
            43: "충청북도",
            44: "충청남도",
            45: "전북특별자치도", 
            46: "전라남도",
            47: "경상북도",
            48: "경상남도",
            50: "제주특별자치도"
        }

## Config
config_loader = ConfigYamlLoader()

user_config_path = 'config/user_config.yaml'
user_config = config_loader.load_config(user_config_path)
user_config = UserInfoConfig(user_config)