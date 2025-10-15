
def get_business_list_filter_prompt():

    BUSINESS_LIST_FILTER_PROMPT = """
        다음 sql문 결과('title', 'content', 'applicant_type_nm', 'request_fr_date', 'request_to_date', 'institution_charge' 열로 구성)를 보고 사람에게 지원사업을 나열 및 서술해주세요.
        
        - 각 열의 의미
            - 'title': 제목,
            - 'content': 해당 사업 내용,
            - 'request_fr_date': 해당 사업 지원 시작일(지원 시작일),
            - 'request_to_date': 해당 사업 지원 종료일(지원 종료일),
            - 'institution_charge': 담당 기관,
            - 'sido_nm': 지원 사업 주최  시/도
        
        {sql_results}

        - 답안 출력시 고려할 사항
            - 해당 데이터의 모든 칼럼 값들이 응답에 들어가야 합니다.
            - Unordered list format으로 정리해서 출력하세요.
            - 필터링한 데이터가 없을 경우 "현재 지원 가능한 지원 사업 정보가 없습니다. 지원 가능한 사업이 갱신될 경우 알려드리겠습니다!" 정도로 간단하게 답변 해줘.

    """

    return BUSINESS_LIST_FILTER_PROMPT

