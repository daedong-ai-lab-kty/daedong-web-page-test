import os

from config.config_file_loader import ConfigYamlLoader
from config.configs import web_config

class UserInfoConfig:

    def __init__(self, config):

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

        self.ID = config['user']['id']
        self.NAME = config['user']['name']
        self.EMAIL = config['user']['email']
        self.FARM_ID = config['user']['farm_id']
        self.LOCATION = config['user']['location']
        self.LOCATION_NAME = self.sido_map_full[self.LOCATION]

## Config
config_loader = ConfigYamlLoader()

# user_config_path = 'config/user_config.yaml'
# user_config = config_loader.load_config(user_config_path)
# user_config = UserInfoConfig(user_config)

main_user_base_url = web_config.DOMAIN_TO_FOLDER_MAP['영농일지']
main_user_id = 2
main_user_name = 'minsu'
main_user_config_path = os.path.join(main_user_base_url, f"2_minsu", "user_config.yaml")
print('- main_user_config_path:', main_user_config_path)
user_config = config_loader.load_config(main_user_config_path)
user_config = UserInfoConfig(user_config)
