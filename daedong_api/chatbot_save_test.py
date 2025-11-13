import requests
import json
import datetime

class ChatbotAPITester:
    """
    대동 챗봇 API 테스트를 위한 클라이언트 클래스
    """
    def __init__(self, environment='dev'):
        """
        테스트 환경에 맞는 URL과 인증 정보를 설정합니다.
        """
        if environment == 'dev':
            self.base_url = "https://tms-agri-dev.daedong.co.kr/api"
        elif environment == 'prod':
            self.base_url = "https://tms.daedong.co.kr/api"
        else:
            raise ValueError("environment는 'dev' 또는 'prod' 중 하나여야 합니다.")

        print(f"{environment} 환경으로 설정되었습니다.")
        
        ## API 엔드포인트 URL
        self.login_url = f"{self.base_url}/user/v1.0/customer/mobile/login"
        self.save_call_url = f"{self.base_url}/v1.0/chatbot/save/call"
        
        ## 로그인 계정 정보
        self.credentials = {
            "username": "ict",
            "password": "khj0310@"
        }
        self.token = None

    def get_auth_token(self):
        """
        로그인 API를 호출하여 인증 토큰(accessToken)을 발급받습니다.
        """
        print("\n인증 토큰을 발급받는 중...")
        try:
            response = requests.post(self.login_url, json=self.credentials, timeout=10)
            ## HTTP 오류 발생 시 예외 처리
            response.raise_for_status()

            response_data = response.json()
            ## 응답 구조에 따라 accessToken 경로를 정확히 지정해야 합니다.
            self.token = response_data.get("data", {}).get("accessToken")

            if self.token:
                print("인증 토큰 발급 성공!")
                return True
            else:
                print("오류: 응답 데이터에서 'accessToken'을 찾을 수 없습니다.")
                print("서버 응답:", json.dumps(response_data, indent=2, ensure_ascii=False))
                return False

        except requests.exceptions.HTTPError as errh:
            print(f"\n[HTTP 오류] 토큰 발급에 실패했습니다: {errh}")
            print(f"상태 코드: {errh.response.status_code}")
            print(f"서버 응답: {errh.response.text}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"토큰 발급 중 네트워크 오류 발생: {e}")
            return False

    def test_save_call_api(self):
        """
        인증 토큰을 사용하여 챗봇 상담 내역 저장 API를 테스트합니다.
        """
        ##  1. 인증 토큰 발급 시도
        if not self.get_auth_token():
            print("\n토큰 발급 실패로 테스트를 중단합니다.")
            return

        ## 2. API 요청 데이터 준비
        request_payload = {
            "customerId": "tashuren@naver.com",
            "farmCode": 310,
            "productCode": "100901",
            "serviceDate": "2025-10-17T10:00:00.000Z",
            "callLogs": [
                {
                    "type": "user",
                    "content": "안녕하세요, 트랙터 시동이 걸리지 않습니다."
                },
                {
                    "type": "assistant",
                    "content": "안녕하세요. 대동 AI 상담사입니다. 배터리 전압을 확인해보셨나요?"
                },
                {
                    "type": "user",
                    "content": "네, 확인했는데 정상입니다."
                }
            ]
        }

        ## 3. HTTP 헤더에 인증 토큰 추가
        headers = {
            "Content-Type": "application/json",
            "X-AUTH-ACCESS-TOKEN": self.token
        }

        print("\n" + "="*50)
        print(f"요청 URL: {self.save_call_url}")
        print("요청 데이터:")
        print(json.dumps(request_payload, indent=2, ensure_ascii=False))
        print("요청 헤더 (토큰은 일부만 표시):")
        ## 토큰이 너무 길 경우 일부만 표시하여 로그를 깔끔하게 유지
        masked_headers = headers.copy()
        if self.token:
            masked_headers["X-AUTH-ACCESS-TOKEN"] = self.token[:15] + "..."
        print(json.dumps(masked_headers, indent=2))
        print("="*50)

        ## 4. API 호출
        try:
            response = requests.post(self.save_call_url, headers=headers, json=request_payload, timeout=10)
            response.raise_for_status()

            print("\n[성공] API 호출에 성공했습니다.")
            print(f"상태 코드: {response.status_code}")

            try:
                response_json = response.json()
                print("서버 응답 (JSON):")
                print(json.dumps(response_json, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print("서버 응답 (Text):")
                print(response.text)

        except requests.exceptions.HTTPError as errh:
            print(f"\n[HTTP 오류] API 호출에 실패했습니다: {errh}")
            print(f"상태 코드: {errh.response.status_code}")
            print(f"서버 응답: {errh.response.text}")
        except requests.exceptions.ConnectionError as errc:
            print(f"\n[연결 오류] API 서버에 연결할 수 없습니다: {errc}")
        except requests.exceptions.Timeout as errt:
            print(f"\n[시간 초과 오류] 요청 시간이 초과되었습니다: {errt}")
        except requests.exceptions.RequestException as err:
            print(f"\n[오류] 알 수 없는 오류가 발생했습니다: {err}")

if __name__ == "__main__":
    api_tester = ChatbotAPITester(environment='dev')
    api_tester.test_save_call_api()
    
