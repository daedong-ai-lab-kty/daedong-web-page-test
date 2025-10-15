import requests
import json
import argparse
import pandas as pd
from datetime import datetime

class DaedongAPIClient:
    """
    대동 TMS API 테스트를 위한 클라이언트 클래스
    """
    
    def __init__(self, environment='dev'):
        
        if environment == 'dev':
            self.base_url = "https://tms-agri-dev.daedong.co.kr/api"
            self.login_url = f"{self.base_url}/user/v1.0/customer/mobile/login"
            self.chat_url = f"{self.base_url}/v1.0/chatbot/getAdvancedGPTStream"
            print("Development (dev) 환경으로 설정되었습니다.")
        elif environment == 'prod':
            self.base_url = "https://tms.daedong.co.kr/api"
            self.login_url = f"{self.base_url}/user/v1.0/customer/mobile/login"
            self.chat_url = f"{self.base_url}/v1.0/chatbot/getAdvancedGPTStream"
            print("Production (prod) 환경으로 설정되었습니다.")
        elif environment == 'test-dev':
            self.base_url = "https://tms-agri-dev.daedong.co.kr/api"
            self.login_url = f"{self.base_url}/user/v1.0/customer/mobile/login"
            self.chat_url = f"{self.base_url}/v1.0/chatbot/ragTest"
            print("Production (prod) 환경으로 설정되었습니다.")
        else:
            raise ValueError("환경은 'dev' 또는 'prod' 중 하나여야 합니다.")
        
        self.credentials = {
            "username": "ict",
            "password": "khj0310@"
        }
        self.token = None
        
    def get_auth_token(self):
        """
        로그인 API를 호출하여 인증 토큰을 발급받습니다.
        """
        
        print("\n인증 토큰을 발급받는 중...")
        try:
            response = requests.post(self.login_url, json=self.credentials, timeout=10)
            response.raise_for_status()  

            self.token = response.json().get("data")["accessToken"] 

            if not self.token:
                print("응답에서 토큰을 찾을 수 없습니다. API 응답 전문을 확인하세요:")
                print(response.json())
                return False

            print("인증 토큰 발급 성공!")
            return True

        except requests.exceptions.RequestException as e:
            print(f"토큰 발급 중 오류 발생: {e}")
            return False

    def ask_question_stream(self, question: str, model: str = "gpt-4o"):
        """
        인증 토큰을 사용하여 챗봇 API에 스트리밍 질문을 보냅니다.
        """
        
        if not self.token:
            print("토큰이 없습니다. 먼저 토큰을 발급받습니다.")
            if not self.get_auth_token():
                return
        
        print(f"\n챗봇에게 질문하는 중: '{question}'")
        
        headers = {
            "X-AUTH-ACCESS-TOKEN": self.token,
            "Accept-Language": "kr"
        }
        
        payload = {
            "model": model,
            "content": question,
            "temperature": 0,
            "stream": True
        }
        
        try:
            
            # stream=True 옵션으로 스트리밍 연결 시작
            with requests.post(self.chat_url, headers=headers, json=payload, stream=True, timeout=30) as response:
                response.raise_for_status()
                
                print("\n챗봇 응답 (스트리밍):")
                full_response_text = ""

                # SSE 형식은 라인 단위로 오는 경우가 많으므로 iter_lines() 사용
                for line in response.iter_lines():

                    # 빈 줄은 건너뜀
                    if not line:
                        continue
                    
                    try:
                        # 1. 수신된 바이트(byte)를 'utf-8'로 직접 디코딩
                        decoded_line = line.decode('utf-8')
                            
                        # 2. SSE 형식("data: ") 확인 및 제거
                        if decoded_line.startswith('data:'):
                            json_str = decoded_line[5:].strip()
                            
                            # 3. 스트리밍 종료 신호 확인
                            if json_str == "[DONE]":
                                break
                            
                            # 4. JSON 문자열을 파싱하여 실제 content 추출
                            chunk_data = json.loads(json_str)
                            content = chunk_data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                            
                            if content:
                                print(content, end='', flush=True)
                                full_response_text += content
                            
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        # 디코딩 또는 JSON 파싱 중 오류 발생 시 디버깅을 위해 출력
                        print(f"\n[파싱 오류 발생] {e}")
                        continue
                
                print("\n\n스트리밍 종료.")
                # print(f"전체 수신 텍스트:\n{full_response_text}")
                return full_response_text.strip()

        except requests.exceptions.RequestException as e:
            print(f"질문 중 오류 발생: {e}")
        
def main():
    
    parser = argparse.ArgumentParser(description="대동 API 테스트 클라이언트")
    parser.add_argument(
        '--env', 
        type=str, 
        choices=['dev', 'prod', 'test-dev'], 
        default='prod',
        help="테스트할 환경을 선택합니다 (dev 또는 prod)"
    )
    args = parser.parse_args()
    
    # API 클라이언트 인스턴스 생성
    client = DaedongAPIClient(environment=args.env)
    
    # 챗봇에게 질문
    questions_list = [
        "농업",
        "딸기 잘 기르는법",
        "배 병충해 치료",
        "태풍 온다는데, 농작물 어떻게 할까?",
        "HX1400L-2C 에어클리너 필터 청소하는 법",
        "GX 트랙터 비교",
        "RT100 작업기 수리 방법", 
        "영농일지 작성 방법",
        "영농 지원 리스트",
        "총 제작 방법",
        "대동 제품들 중에 소작농 추천",
        "전남 화순에서 받을 수 있는 보조금 정책",
        "화순에서 받을 수 있는 보조금 정책",
        "전라남도에서 받을 수 있는 보조금 정책",
        "올해 청년이 지원할 수 있는 영농지원사업 추천해줘",
        "올해 영농인이 지원할 수 있는 영농지원사업 추천해줘"
    ]

    results = []
    for q in questions_list:
        print('='*50)
        print('question_to_ask_1:', q)
        answer = client.ask_question_stream(q)
        print('='*50)

        results.append({
            "question": q,
            "answer": answer 
        })

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"daedong_chat_results_{timestamp}.xlsx"
    
    df = pd.DataFrame(results)
    df.to_excel(output_filename, index=False)
    
    print(f"\n모든 질문과 응답이 '{output_filename}' 파일로 저장되었습니다!")

if __name__ == "__main__":
    main()
