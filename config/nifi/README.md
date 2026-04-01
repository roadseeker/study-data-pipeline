# config/nifi

NiFi 데이터 수집·라우팅 설정 파일을 관리하는 폴더.

NiFi 플로우 템플릿, 프로세서 설정, 인증 설정 등이 위치한다.

## 주요 설정 항목

- 웹 UI 포트 및 접속 설정 (NIFI_WEB_HTTP_PORT)
- 단일 사용자 인증 정보 (SINGLE_USER_CREDENTIALS)
- 플로우 파일 저장 경로
- 프로세서 스레드 설정

## 관련 주차

- Week 1: NiFi 기동 및 기본 플로우 검증 (GenerateFlowFile → LogAttribute)
- Week 2 이후: PostgreSQL → Kafka 수집 플로우, 데이터 라우팅 규칙 설정
