class WebConfig:

    def __init__(self, config):

        DEFAULT_VERSION = config.DEFAULT_VERSION
    
        self.DOMAIN_TO_FOLDER_MAP = {
            f'GX_트랙터': 'graphrag_{DEFAULT_VERSION}_GX',
            f'RT_운반로봇_RT100': 'graphrag_{DEFAULT_VERSION}_RT100',
            f'DH_콤바인_DH6135': 'graphrag_{DEFAULT_VERSION}_DH6135',
            f'HX_트랙터_HX1300_HX1400': 'graphrag_{DEFAULT_VERSION}_NEW_HX',
            f'DRP_이앙기_DRP80': 'graphrag_{DEFAULT_VERSION}_DRP80',
            f'LK_트랙터_LK2805': 'graphrag_{DEFAULT_VERSION}_LK',
            f'NX_트랙터_NX450': 'graphrag_{DEFAULT_VERSION}_NX',
            f'HX_트랙터_HX900': 'graphrag_{DEFAULT_VERSION}_HX',
            f'DK_트랙터_DK450': 'graphrag_{DEFAULT_VERSION}_DK',
            f'지원사업': 'graphrag_{DEFAULT_VERSION}_GX', 
            f'농업': 'graphrag_{DEFAULT_VERSION}_GX',    
        }

        self.KR_DOMAINS = list(self.DOMAIN_TO_FOLDER_MAP.keys()) + ['기타']

        # 기타 설정값
        self.COMMUNITY_LEVEL = config.COMMUNITY_LEVEL
        self.RESPONSE_TYPE = config.RESPONSE_TYPE