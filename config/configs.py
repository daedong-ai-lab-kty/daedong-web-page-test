from config.config_file_loader import ConfigYamlLoader

class WebConfig:

    def __init__(self, config):

        DEFAULT_VERSION = config['web']['default_version']
        print(' - WebConfig DEFAULT_VERSION:', DEFAULT_VERSION)
        
        self.DOMAIN_TO_FOLDER_MAP = {
            f'GX_트랙터': f'rag_db/graphrag_{DEFAULT_VERSION}_GX',
            f'RT_운반로봇_RT100': f'rag_db/graphrag_{DEFAULT_VERSION}_RT100',
            f'DH_콤바인_DH6135': f'rag_db/graphrag_{DEFAULT_VERSION}_DH6135',
            f'HX_트랙터_HX1300_HX1400': f'rag_db/graphrag_{DEFAULT_VERSION}_NEW_HX',
            f'DRP_이앙기_DRP80': f'rag_db/graphrag_{DEFAULT_VERSION}_DRP80',
            f'LK_트랙터_LK2805': f'rag_db/graphrag_{DEFAULT_VERSION}_LK',
            f'NX_트랙터_NX450': f'rag_db/graphrag_{DEFAULT_VERSION}_NX',
            f'HX_트랙터_HX900': f'rag_db/graphrag_{DEFAULT_VERSION}_HX',
            f'DK_트랙터_DK450': f'rag_db/graphrag_{DEFAULT_VERSION}_DK',
            f'지원사업': f'rag_db/graphrag_{DEFAULT_VERSION}_GX',#None, 
            f'agriculture': f'rag_db/graphrag_{DEFAULT_VERSION}_GX',#None,
            f'기타': f'rag_db/graphrag_{DEFAULT_VERSION}_GX', #None
        }

        self.DOMAIN_TO_REFERENCE_MAP = {
            f'GX_트랙터': '[GX 트랙터 유저 메뉴얼], [GX 트랙터 카탈로그]',
            f'RT_운반로봇_RT100': '[RT100 운반로봇 유저 메뉴얼], [RT100 운반로봇 카탈로그]',
            f'DH_콤바인_DH6135': '[DH 콤바인 유저 메뉴얼], [DH 콤바인 카탈로그]',
            f'HX_트랙터_HX1300_HX1400': '[New HX 트랙터 유저 메뉴얼], [New HX 트랙터 카탈로그]',
            f'DRP_이앙기_DRP80': '[DRP 이앙기 유저 메뉴얼], [DRP 이앙기 카탈로그]',
            f'LK_트랙터_LK2805': '[LK 트랙터 유저 메뉴얼], [LK 트랙터 카탈로그]',
            f'NX_트랙터_NX450': '[NX 트랙터 유저 메뉴얼], [NX 트랙터 카탈로그]',
            f'HX_트랙터_HX900': '[HX 트랙터 유저 메뉴얼], [HX 트랙터 카탈로그]',
            f'DK_트랙터_DK450': '[DK 트랙터 유저 메뉴얼], [DK 트랙터 카탈로그]',
            f'지원사업': '[지원사업 리스트]', 
            f'agriculture': '[농진청 농업 자료]', 
            f'기타': None   
        }

        self.KR_DOMAINS = list(self.DOMAIN_TO_FOLDER_MAP.keys()) + ['기타']


class RagConfig:

    def __init__(self, config):

        self.COMMUNITY_LEVEL = config['rag']['community_level']
        self.RESPONSE_TYPE = config['rag']['response_type']
        self.SEARCH_METHOD = config['rag']['search_method']


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