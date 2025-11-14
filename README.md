Docker & Server Commands
============

<details>
<summary>Run Server</summary>

### - Run Server

* 최신 버전
    * 3.37.114.2 AWS 서버 허용 port = 8666

```
## 1. Docker Network
docker network create daedong_ai_server_network

## 2. 기존 이미지 삭제
docker stop daedong_ai_server
docker rmi -f daedong_ai_server_env

## 3. Docker Build Image
### E.g. docker build --build-arg SERVER_PORT=8666 -t daedong_ai_server_env -f Dockerfile.server .
docker build --build-arg SERVER_PORT={PORT} -t daedong_ai_server_env -f Dockerfile.server .

## 4. Build '.env': {token}

## 5. Docker Run Container
export PUBLIC_IP=$(curl -s ifconfig.me)
### E.g. docker run --rm -d --name daedong_ai_server -p 8666:8666 --network daedong_ai_server_network -e PUBLIC_IP=$PUBLIC_IP daedong_ai_server_env
docker run --rm -d --name daedong_ai_server -p {SERVER_PORT}:{SERVER_PORT} --network daedong_ai_server_network -e PUBLIC_IP=$PUBLIC_IP daedong_ai_server_env

## 6. Log
docker logs -f daedong_ai_server
```

* 이전 버전

```
### E.g. sudo docker run --name rag_250902 --shm-size=64G -p 8666:8666 -e GRANT_SUDO=yes --user root -v /home/ec2-user/rag_250902/hybrid-rag-multi-modal-llm-systems-main_3.7:/workspace/daedong -w /workspace/daedong -d rag_250902_env tail -f /dev/null bash
### E.g. docker start rag_250902
### E.g. sudo docker exec -it rag_250902 bash

pip install openai==1.58.1
python3 server.py
```

</details>

<details>
<summary>Close Server</summary>

### - Close Server

* 최신 버전

```
docker stop daedong_ai_server
docker rmi -f daedong_ai_server_env
```

* 2509 이전 버전

```
### E.g. docker stop rag_250902
### E.g. docker rm rag_250902
```

</details>


Response & API Test
============

<details>
<summary>dev, prod test</summary>

* choices=['dev', 'prod', 'test-dev]
    * 'dev': 배포-포트 개발계 통신 검증
    * 'prod': 배포-포트 운영계 통신 검증
    * 'test-dev': 테스트-포트 운영계 통신 검증
    * Save response as Excel

```
docker exec -it daedong_ai_server bash
python daedong_api/ai_daedong_server_communication_test.py --env {dev|prod|test-dev}
```

</details>


<details>
<summary>TMS chat save</summary>

```
python daedong_api/chatbot_save_test.py
```

</details>


Sample Web Test
============

```
docker exec -it daedong_ai_server bash
python test_app/client_server.py 
```

