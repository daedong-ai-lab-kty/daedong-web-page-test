import os

from config.config_file_loader import ConfigYamlLoader

class WebConfig:

    def __init__(self, config):

        DEFAULT_VERSION = config['web']['default_version']
        print(' - WebConfig DEFAULT_VERSION:', DEFAULT_VERSION)

        self.RAG_DB_ROOT_PATH = config['web']['rag_db_root_path']
        
        self.DOMAIN_TO_FOLDER_MAP = {
            f'GX_트랙터': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_GX'),
            f'RT_운반로봇_RT100': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_RT100'),
            f'DH_콤바인_DH6135': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_DH6135'), 
            f'HX_트랙터_HX1300': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_NEW_HX'),  
            f'HX_트랙터_HX1400': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_NEW_HX'),  
            f'DRP_이앙기_DRP80': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_DRP80'),  
            f'LK_트랙터_LK2805': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_LK'), 
            f'NX_트랙터_NX450': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_NX'), 
            f'HX_트랙터_HX900': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_HX'), 
            f'DK_트랙터_DK450': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_DK'),
            f'지원사업': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_support_business/input/support_project_list.txt'), #f'rag_db/graphrag_{DEFAULT_VERSION}_support_business/input/support_project_list.txt', #None, 
            f'agriculture': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_GX'), #None,
            f'영농일지_조회': os.path.join(self.RAG_DB_ROOT_PATH, f'rag_{DEFAULT_VERSION}_farming_diary'), #None,
            f'영농일지_삽입': os.path.join(self.RAG_DB_ROOT_PATH, f'rag_{DEFAULT_VERSION}_farming_diary'), #None,
            f'영농일지_수정': os.path.join(self.RAG_DB_ROOT_PATH, f'rag_{DEFAULT_VERSION}_farming_diary'), #None,
            f'영농일지_삭제': os.path.join(self.RAG_DB_ROOT_PATH, f'rag_{DEFAULT_VERSION}_farming_diary'), #None,
            f'기타': os.path.join(self.RAG_DB_ROOT_PATH, f'graphrag_{DEFAULT_VERSION}_GX'), #None,
        }

        self.DOMAIN_TO_REFERENCE_MAP = {
            f'GX_트랙터': '[GX 트랙터 유저 메뉴얼], [GX 트랙터 카탈로그]',
            f'RT_운반로봇_RT100': '[RT100 운반로봇 유저 메뉴얼], [RT100 운반로봇 카탈로그]',
            f'DH_콤바인_DH6135': '[DH 콤바인 유저 메뉴얼], [DH 콤바인 카탈로그]',
            f'HX_트랙터_HX1300': '[New HX 트랙터 유저 메뉴얼], [New HX 트랙터 카탈로그]',
            f'HX_트랙터_HX1400': '[New HX 트랙터 유저 메뉴얼], [New HX 트랙터 카탈로그]',
            f'DRP_이앙기_DRP80': '[DRP 이앙기 유저 메뉴얼], [DRP 이앙기 카탈로그]',
            f'LK_트랙터_LK2805': '[LK 트랙터 유저 메뉴얼], [LK 트랙터 카탈로그]',
            f'NX_트랙터_NX450': '[NX 트랙터 유저 메뉴얼], [NX 트랙터 카탈로그]',
            f'HX_트랙터_HX900': '[HX 트랙터 유저 메뉴얼], [HX 트랙터 카탈로그]',
            f'DK_트랙터_DK450': '[DK 트랙터 유저 메뉴얼], [DK 트랙터 카탈로그]',
            f'영농일지': None,
            f'지원사업': '[지원사업 리스트]', 
            f'agriculture': '[농진청 농업 자료]', 
            f'기타': None   
        }

        self.KR_DOMAINS = list(self.DOMAIN_TO_FOLDER_MAP.keys())
        print(' - KR_DOMAINS:', self.KR_DOMAINS)

        self.BASE_SERVER_ADDRESS = "http://172.16.10.57:8000"
        self.BASE_ENDPOINT = "kr_ai_server_test"
        # self.BASE_FINAL_LLM = "gpt"
        # self.BASE_UTIL_LLM = "gpt"


class RagConfig:

    def __init__(self, config):

        self.COMMUNITY_LEVEL = config['rag']['community_level']
        self.RESPONSE_TYPE = config['rag']['response_type']
        self.SEARCH_METHOD = config['rag']['search_method']


class UtilConfig:

    def __init__(self, config):

        self.BUSINESS_LIST_TABLE_NAME = config['util']['business_list_table_name']


## Config
config_loader = ConfigYamlLoader()

llm_config_path = 'config/llm_config.yaml'
llm_config = config_loader.load_config(llm_config_path)

web_config_path = 'config/web_config.yaml'
web_config = config_loader.load_config(web_config_path)
web_config = WebConfig(web_config)

rag_config_path = 'config/rag_config.yaml'
rag_config = config_loader.load_config(rag_config_path)
rag_config = RagConfig(rag_config)

util_config_path = 'config/util_config.yaml'
util_config = config_loader.load_config(util_config_path)
util_config = UtilConfig(util_config)

