# config/kafka

Kafka 브로커 설정 파일을 관리하는 폴더.

Week 1에서는 KRaft 모드 단일 브로커로 운영하며, Week 2에서 멀티 브로커 구성으로 확장 시 브로커별 설정 파일이 이 폴더에 추가된다.

## 주요 설정 항목

- 브로커 ID 및 클러스터 ID
- 리스너 및 포트 구성 (PLAINTEXT / CONTROLLER / EXTERNAL)
- 토픽 보존 정책 (retention.hours, retention.bytes)
- 복제 팩터 기본값
- 오토 토픽 생성 여부 (`auto.create.topics.enable=false`)

## 관련 주차

- Week 1: 단일 브로커 기동 검증
- Week 2: 멀티 브로커 구성, 토픽 설계, 파티션 전략

## 주요 문서

- `topic-naming-convention.md`: Nexus Pay Kafka 토픽 명명 규칙
- `partition-sizing-guide.md`: 처리량·컨슈머 병렬성 기반 파티션 수 산정 기준
- `topic-configs.md`: Week 2 토픽 설정 기준과 운영 권장사항
