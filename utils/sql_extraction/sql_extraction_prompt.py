# SQL_EXTRACTION = """
#     You are an intelligent AI assistant that analyzes a user's natural language query to generate an SQL filter condition and an explanation for it.
#     Please refer to the data schema, user query, and the current date below to respond in JSON format.

#     **Data Schema:**
#     - Table Name: programs
#     - Columns:
#         - request_fr_date: DATE (YYYY-MM-DD format)
#         - request_to_date: DATE (YYYY-MM-DD format)
#         - applicant_type_nm: TEXT (e.g. '농업인', '사업', '전체', '법인')

#     **Rules:**
#     1. The response must be a JSON object with the following two keys: "sql_where_clause", "explanation".
#     2. "sql_where_clause": Generate only the SQL WHERE clause condition as a string (exclude the 'WHERE' keyword).
#        - Use '{{current_date}}' for date comparisons (e.g., `start_date <= '{{current_date}}' AND end_date >= '{{current_date}}'`).
#        - If no filtering condition is needed from the query, return an empty string ("").
#     3. "explanation": Explain the generated filter condition in a natural English sentence.
#        - If there are no filtering conditions, generate a description indicating a full scan, such as "Searching for all support programs."

#     ---
#     **Current Date:** {current_date}
#     **User Query:** "{user_query}"
#     ---

#     **JSON Response:**
# """

def get_business_list_sql_extraction_prompt():

    # SQL_EXTRACTION = '''
    # You are an intelligent AI assistant that analyzes a user's natural language query to generate an SQL filter condition and an explanation for it.
    # Please refer to the data schema, interpretation guide, examples, user query, and the current date below to respond in JSON format.

    # **Data Schema:**
    # - Table Name: programs
    # - Columns:
    #     - request_fr_date: DATE (Program application start date in YYYY-MM-DD format)
    #     - request_to_date: DATE (Program application end date in YYYY-MM-DD format)
    #     - applicant_type_nm: TEXT (다음 값 중 하나: '농업인', '사업', '전체', '법인')
    #     - sido_nm: TEXT (다음 값 중 하나: '강원도', '경기도', '경상남도', '경상북도', '광주광역시', '대구광역시', '대전광역시', '부산광역시', '서울특별시', '세종특별자치시', '울산광역시', '인천광역시', '전라남도', '전라북도', '충청남도', '충청북도')
    #     - support_type_nm: TEXT (다음 값 중 하나: '사업', '시범사업', '교육', '보조금', '미분류')

    # **Interpretation Guide:**
    # 1.  For queries about "this year" (올해), "2025년", etc., the condition should cover the entire year (from January 1st to December 31st).
    # 2.  For queries about "currently available" (지금, 현재), the condition should check if the current date is between the start and end dates.
    # 3.  For queries about a specific applicant type (농업인, 법인), use an exact match condition.

    # **Examples:**
    # - User Query: "지금 신청 가능한 사업 찾아줘"
    # - JSON Response:
    #     {{
    #     "sql_where_clause": "request_fr_date <= '{{current_date}}' AND request_to_date >= '{{current_date}}'",
    #     "explanation": "Finds programs that are currently active based on the current date."
    #     }}
    # - User Query: "올해 농업인 대상 지원사업만 보여줘"
    # - JSON Response:
    #     {{
    #     "sql_where_clause": "applicant_type_nm = '농업인' AND request_fr_date >= '2025-01-01' AND request_to_date <= '2025-12-31'",
    #     "explanation": "Filters for programs targeting '농업인' (farmers) that fall within the current year, 2025."
    #     }}
    # - User Query: "전체 목록 보여줘"
    # - JSON Response:
    #     {{
    #     "sql_where_clause": "",
    #     "explanation": "Searching for all support programs."
    #     }}

    # **Rules:**
    # 1. The response must be a JSON object with the following two keys: "sql_where_clause", "explanation".
    # 2. "sql_where_clause": Generate only the SQL WHERE clause condition as a string (exclude the 'WHERE' keyword).
    #     - Use '{{current_date}}' only for 'currently available' type queries. For year-based queries, use explicit dates like 'YYYY-01-01' and 'YYYY-12-31'.
    #     - If no filtering condition is needed, return an empty string ("").
    # 3. "explanation": Explain the generated filter condition in a natural English sentence.

    # ---
    # **Current Date:** {current_date}
    # **User Query:** "{user_query}"
    # ---

    # **JSON Response:**
    # '''

    SQL_EXTRACTION = '''
    You are an intelligent AI assistant that analyzes a user's natural language query to generate an SQL filter condition and an explanation for it.
    Please refer to the data schema, interpretation guide, examples, user query, and the current date below to respond in JSON format.

    **Data Schema:**
    - Table Name: programs
    - Columns:
        - request_fr_date: DATE (Program application start date in YYYY-MM-DD format)
        - request_to_date: DATE (Program application end date in YYYY-MM-DD format)
        - applicant_type_nm: TEXT (다음 값 중 하나: '농업인', '사업', '전체', '법인')
        - sido_nm: TEXT (다음 값 중 하나: '강원도', '경기도', '경상남도', '경상북도', '광주광역시', '대구광역시', '대전광역시', '부산광역시', '서울특별시', '세종특별자치시', '울산광역시', '인천광역시', '전라남도', '전라북도', '충청남도', '충청북도')
        - support_type_nm: TEXT (다음 값 중 하나: '사업', '시범사업', '교육', '보조금', '미분류')

    **Interpretation Guide:**
    1. For queries about "this year" (올해), "2025년", etc., the condition should cover the entire year (from January 1st to December 31st).
    2. For queries about "last year" (작년, 2024년), the condition should cover the previous year (from January 1st to December 31st of that year).
    3. For queries mentioning a specific month (예: 8월, 9월), generate conditions for that month (e.g., request_fr_date >= '2025-08-01' AND request_to_date <= '2025-08-31').
    4. For queries about "currently available" (지금, 현재), the condition should check if the current date is between the start and end dates.
    5. For queries about a specific applicant type (농업인, 법인, 전체 등), use an exact match condition.
    6. For queries specifying a region (sido_nm), use exact match for the given province/city name.
        - Example: "경기도 지원사업" → sido_nm = '경기도'
    7. For queries specifying a support type (지원유형), match it to one of the known categories ('사업', '시범사업', '교육', '보조금', '미분류').
        - Example: "보조금 사업" → support_type_nm = '보조금'
    8. **Default Rule (when no explicit date is mentioned):**
        - If the query does not include any explicit year, month, or time reference (e.g., "올해", "작년", "2025", "8월", "현재"),
        then filter only programs whose application period has **not yet ended**:
        `request_to_date >= '{{current_date}}'`

    **Examples:**
    - User Query: "지금 신청 가능한 사업 찾아줘"
    - JSON Response:
        {{
        "sql_where_clause": "request_fr_date <= '{{current_date}}' AND request_to_date >= '{{current_date}}'",
        "explanation": "Finds programs that are currently active based on the current date."
        }}

    - User Query: "올해 농업인 대상 지원사업만 보여줘"
    - JSON Response:
        {{
        "sql_where_clause": "applicant_type_nm = '농업인' AND request_fr_date >= '2025-01-01' AND request_to_date <= '2025-12-31'",
        "explanation": "Filters for programs targeting '농업인' (farmers) that fall within the current year, 2025."
        }}

    - User Query: "경기도 보조금 사업 찾아줘"
    - JSON Response:
        {{
        "sql_where_clause": "sido_nm = '경기도' AND support_type_nm = '보조금' AND request_to_date >= '{{current_date}}'",
        "explanation": "Finds subsidy-type programs in Gyeonggi-do that are still open for application."
        }}

    - User Query: "전체 목록 보여줘"
    - JSON Response:
        {{
        "sql_where_clause": "",
        "explanation": "Searching for all support programs."
        }}

    **Rules:**
    1. The response must be a JSON object with the following two keys: "sql_where_clause", "explanation".
    2. "sql_where_clause": Generate only the SQL WHERE clause condition as a string (exclude the 'WHERE' keyword).
        - Use '{{current_date}}' only for 'currently available' or default filtering.
        - For year-based or month-based queries, use explicit dates like 'YYYY-01-01' and 'YYYY-12-31' or month boundaries.
        - If no filtering condition is needed, return an empty string ("").
    3. "explanation": Explain the generated filter condition in a natural English sentence.

    ---
    **Current Date:** {current_date}
    **User Query:** "{user_query}"
    ---

    **JSON Response:**
    '''

    SQL_EXTRACTION = '''
You are an intelligent AI assistant that analyzes a user's natural language query to generate an SQL filter condition and an explanation for it.
Please refer to the data schema, interpretation guide, examples, user query, and the current date below to respond in JSON format.

**Data Schema:**
- Table Name: programs
- Columns:
    - title: TEXT (Program title)
    - content: TEXT (Program description)
    - applicant_type_nm: TEXT (지원 대상: '농업인', '사업', '전체', '법인')
    - request_fr_date: DATE (Program application start date in YYYY-MM-DD format)
    - request_to_date: DATE (Program application end date in YYYY-MM-DD format)
    - sido_nm: TEXT (다음 값 중 하나(지역): '강원도', '경기도', '경상남도', '경상북도', '광주광역시', '대구광역시', '대전광역시', '부산광역시', '서울특별시', '세종특별자치시', '울산광역시', '인천광역시', '전라남도', '전라북도', '충청남도', '충청북도')
    - support_type_nm: TEXT (지원유형: '사업', '시범사업', '교육', '보조금', '미분류')

**Interpretation Guide:**
1. "올해", "2025년" → 2025-01-01 ~ 2025-12-31 범위
2. "작년", "2024년" → 2024-01-01 ~ 2024-12-31 범위
3. 특정 월(예: 8월) → 해당 월의 시작~마지막 날짜
4. "현재", "지금" → 현재 날짜가 시작일~종료일 사이
5. applicant_type_nm → 명시된 지원대상으로 정확 매칭
6. sido_nm → 지역명 정확 매칭
7. support_type_nm → 지원유형 정확 매칭
8. **기본 규칙 (중요)**  
- 사용자가 명확한 시점(‘올해’, ‘작년’, ‘현재’, 월 등)을 언급하지 않은 경우,  
    자동으로 “아직 종료되지 않은 사업(request_to_date >= '{{current_date}}')”만 필터링한다.
- 단, 이 조건에 해당하는 결과가 없을 때는,  
    “현재 신청 가능한 사업은 없지만 과거에 진행된 사업이 있습니다”로 안내할 수 있다.

**Examples:**
- User Query: "전남 화순에서 받을 수 있는 보조금 정책"
- JSON Response:
    {{
    "sql_where_clause": "sido_nm = '전라남도' AND support_type_nm = '보조금' AND request_to_date >= '{{current_date}}'",
    "explanation": "Filters for active subsidy programs ('보조금') available in Hwasun, Jeollanam-do as of the current date."
    }}

- User Query: "올해 전남 화순에서 받을 수 있는 보조금 정책"
- JSON Response:
    {{
    "sql_where_clause": "sido_nm = '전라남도' AND support_type_nm = '보조금' AND request_fr_date >= '2025-01-01' AND request_to_date <= '2025-12-31'",
    "explanation": "Filters for subsidy programs in Hwasun, Jeollanam-do that are open during 2025."
    }}

**Rules:**
1. Always return a JSON object with two keys: "sql_where_clause" and "explanation".
2. "sql_where_clause": Only the condition part (no 'WHERE').  
- If no explicit period is given, default to `request_to_date >= '{{current_date}}'`.  
- Include sido_nm / support_type_nm / applicant_type_nm as appropriate.
3. "explanation": Provide a clear, natural English explanation.
4. If the filtered result has zero rows but the table has data, the system should respond:  
"There are currently no active programs matching your criteria, but there are past programs available."

---
**Current Date:** {current_date}
**User Query:** "{user_query}"
---

**JSON Response:**
    '''

    return SQL_EXTRACTION

