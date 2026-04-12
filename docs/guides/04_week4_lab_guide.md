# Week 4: 변환 — Flink 실시간 스트림 처리 심화

**기간**: 5일 (월~금, 풀타임 40시간)
**주제**: 윈도우 집계(Window Aggregation), Watermark 기반 이벤트 타임 처리, 정확히 한 번(Exactly-once) 처리, 실시간 이상거래 탐지
**산출물**: Flink 실시간 파이프라인 + 이상거래 탐지 잡 + Exactly-once 검증 보고서 + Flink 운영 가이드
**전제 조건**: Week 1·2·3 환경 정상 기동 (`bash scripts/foundation/healthcheck-all.sh` 전체 통과), NiFi → Kafka(`nexuspay.events.ingested`) 데이터 흐름 정상

---

## 수행 시나리오

### 배경 설정

NiFi 기반 다중 소스 수집 체계 구축이 완료되었다. 결제 API·정산 CSV·고객 DB 세 가지 소스의 데이터가 `nexuspay.events.ingested` 토픽으로 실시간 유입되고 있다. Nexus Pay CTO가 다음 단계 요구사항을 제시한다.

> "수집은 잘 되고 있습니다. 이제 이 데이터를 **실시간으로 분석**해야 합니다. 세 가지가 급합니다. 첫째, 5분 단위로 거래 유형별 금액 합계와 건수를 **실시간 집계**해야 합니다 — 대시보드 팀이 기다리고 있어요. 둘째, **이상거래 탐지**입니다. 동일 사용자가 1분 내 3건 이상 거래하거나, 단건 500만원 초과 거래를 실시간으로 잡아야 합니다. 셋째, 금융 데이터니까 **한 건도 빠지거나 중복 처리되면 안 됩니다**. Exactly-once를 보장해 주세요."

컨설턴트로서 Apache Flink를 활용하여 Kafka에서 실시간 이벤트를 소비하고, 윈도우 집계·이상거래 탐지·정확히 한 번 처리를 구현하는 것이 이번 주의 과제다. Week 3에서 NiFi가 구축한 수집 파이프라인의 데이터를 Flink가 소비하여, NiFi(수집) → Kafka(버퍼) → Flink(변환)로 이어지는 실시간 파이프라인의 핵심 구간을 완성한다.

### 목표

1. Flink 핵심 개념(스트림 처리 모델, 상태 관리, 체크포인트) 이해 및 정리
2. Kafka 소스 커넥터를 통한 `nexuspay.events.ingested` 토픽 실시간 소비
3. Watermark 기반 이벤트 타임 처리 및 지연 데이터(Late Data) 처리 전략 구현
4. 윈도우 집계(Tumbling·Sliding·Session)를 활용한 실시간 거래 통계 파이프라인 구축
5. CEP(Complex Event Processing) 패턴 기반 실시간 이상거래 탐지 로직 구현
6. Exactly-once 시맨틱 설정 및 장애 복구 시 데이터 정합성 검증

### 일정 개요

| 일차 | 주제 | 핵심 작업 |
|------|------|----------|
| Day 1 | Flink 핵심 개념 + 프로젝트 셋업 | 스트림 처리 모델 정리, Flink 프로젝트 구조 생성, Kafka 소스 연동 |
| Day 2 | Watermark + 윈도우 집계 | 이벤트 타임 처리, Watermark 전략, Tumbling·Sliding·Session 윈도우 구현 |
| Day 3 | 실시간 이상거래 탐지 | CEP 패턴 매칭, 룰 기반 탐지, 알림 싱크(Kafka·Redis) 연동 |
| Day 4 | Exactly-once + 체크포인트 | 체크포인트 설정, Kafka 트랜잭션 싱크, 장애 복구 시 정합성 검증 |
| Day 5 | 통합 테스트 + 운영 가이드 문서화 | 전체 파이프라인 검증, 성능 튜닝, 운영 가이드 작성, Git 커밋 |

---

### 대표적인 Flink 활용 예시

대표적인 Flink 활용 예시는 아래 10가지 정도로 보면 됩니다.

#### 실시간 클릭스트림 분석
웹/앱에서 발생하는 클릭, 페이지뷰, 체류시간을 초 단위로 집계해서 대시보드나 마케팅 분석에 씁니다.

#### 이상거래 탐지
카드 결제나 송금 이벤트를 실시간으로 읽어 패턴을 비교하고, 의심 거래를 즉시 차단하거나 알림을 보냅니다.

#### IoT 센서 데이터 처리
공장 설비, 차량, 스마트미터에서 들어오는 센서 스트림을 분석해 이상치 탐지, 임계치 경보, 예지정비에 활용합니다.

#### 로그 및 모니터링 파이프라인
애플리케이션 로그, 시스템 메트릭, 이벤트 로그를 실시간으로 정제하고 집계해서 장애 감지와 운영 관제에 사용합니다.

#### 실시간 추천 시스템
사용자의 최근 행동을 바탕으로 선호도 점수, 인기 상품, 세션 기반 특징을 계속 갱신해 추천 모델 입력으로 씁니다.

#### 실시간 ETL / CDC 처리
DB 변경 데이터(CDC)를 받아 정제, 조인, 필터링 후 데이터 레이크나 DW로 흘려 보내는 실시간 데이터 파이프라인에 적합합니다.

#### 주문/재고/물류 추적
주문 생성, 결제, 출고, 배송 이벤트를 연결해서 현재 상태를 계산하고 지연이나 병목을 실시간으로 파악합니다.

#### 광고 이벤트 분석
노출, 클릭, 전환 데이터를 실시간 집계해서 캠페인 성과, 예산 소진, 이상 트래픽 여부를 바로 확인합니다.

#### 통신/네트워크 품질 모니터링
네트워크 장비와 기지국 이벤트를 모아 장애 징후, 트래픽 급증, 품질 저하를 빠르게 탐지합니다.

#### 보안 이벤트 상관분석
로그인 실패, 권한 변경, 비정상 접근, API 호출 패턴을 연계해 보안 위협을 탐지하는 SIEM/보안 분석에 씁니다.

---

## Day 1: Flink 핵심 개념 + 프로젝트 셋업

### 1-1. Flink 스트림 처리 핵심 개념 정리

컨설팅 현장에서 고객에게 Flink를 설명할 때 사용할 핵심 개념을 정리한다.

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Flink 스트림 처리 핵심 개념                        │
│                                                                      │
│  DataStream = 무한 데이터 흐름                                        │
│    └── 이벤트 단위 처리 (배치가 아닌 연속 스트림)                       │
│                                                                      │
│  시간 개념 (Time Semantics)                                           │
│    ├── Event Time: 이벤트 발생 시점 (가장 정확, 권장)                   │
│    ├── Processing Time: Flink 처리 시점 (간단하지만 비결정적)           │
│    └── Ingestion Time: Flink 유입 시점 (절충안)                        │
│                                                                      │
│  Watermark = "이 시점까지의 데이터는 모두 도착했다"는 신호              │
│    ├── BoundedOutOfOrderness: 최대 지연 허용 시간 지정                 │
│    └── Late Data → Side Output으로 별도 처리                           │
│                                                                      │
│  Window = 무한 스트림을 유한 구간으로 분할                              │
│    ├── Tumbling: 겹치지 않는 고정 구간 (5분 단위 집계)                 │
│    ├── Sliding: 겹치는 구간 (5분 윈도우, 1분 슬라이드)                 │
│    └── Session: 활동 기반 동적 구간 (비활동 간격으로 분할)              │
│                                                                      │
│  State = 연산자별 유지하는 상태 (집계값, 카운터 등)                     │
│    ├── Keyed State: 키별 독립 상태 (user_id별 거래 합계)               │
│    └── Operator State: 연산자 전체 공유 상태                            │
│                                                                      │
│  Checkpoint = 분산 스냅샷 (장애 복구의 핵심)                            │
│    ├── Chandy-Lamport 알고리즘 기반                                    │
│    └── Exactly-once 보장의 기반 메커니즘                                │
│                                                                      │
│  Savepoint = 수동 체크포인트 (업그레이드·마이그레이션용)                 │
└──────────────────────────────────────────────────────────────────────┘
```

```bash
cat > docs/flink-concepts.md << 'EOF'
# Flink 실시간 스트림 처리 핵심 개념 — 컨설팅 설명 자료

## 왜 Flink인가?

Spark Streaming(마이크로 배치)과 달리 Flink는 진정한 이벤트 단위 스트림 처리 엔진이다.
- 이벤트 발생 즉시 처리 → 밀리초 단위 레이턴시
- 이벤트 타임 기반 처리 → 지연 도착 데이터도 정확한 윈도우에 배치
- Exactly-once 상태 일관성 → 금융 데이터 정합성 보장
- 대규모 상태 관리 → TB 단위 상태도 안정적 처리

## 배치 vs 스트림 — Nexus Pay 관점

| 구분 | 배치 (Spark) | 스트림 (Flink) |
|------|-------------|---------------|
| 처리 단위 | 시간/일 단위 묶음 | 이벤트 단위 |
| 레이턴시 | 분~시간 | 밀리초~초 |
| 적합 업무 | 일별 정산, 월간 리포트 | 이상거래 탐지, 실시간 대시보드 |
| Nexus Pay 활용 | Week 5 (Spark 배치 ETL) | Week 4 (실시간 분석) |

## Event Time vs Processing Time

금융 거래에서는 반드시 Event Time을 사용해야 한다.
예: 23:59:58에 발생한 결제가 네트워크 지연으로 00:00:02에 Flink에 도착.
- Processing Time 기준: 다음 날 거래로 집계 (오류)
- Event Time 기준: 당일 거래로 정확하게 집계 (정확)

## Watermark 메커니즘

Watermark(t)의 의미: "타임스탬프 t 이전의 모든 이벤트는 도착 완료되었다."
- BoundedOutOfOrderness(5초): 최대 5초까지 늦게 도착하는 이벤트 허용
- Watermark 이후 도착 = Late Data → Side Output으로 별도 처리

## Checkpoint와 Exactly-once

Flink의 체크포인트는 분산 스냅샷이다.
1. JobManager가 체크포인트 배리어를 소스에 주입
2. 배리어가 연산자를 통과하면서 각 연산자가 상태를 스냅샷
3. 모든 연산자 스냅샷 완료 → 체크포인트 성공
4. 장애 발생 시 마지막 성공 체크포인트에서 복구
5. Kafka 소스 오프셋도 체크포인트에 포함 → 중복/유실 방지

EOF
```

### 1-2. Flink 프로젝트 구조 생성

```bash
mkdir -p flink-jobs/{src/main/java/com/nexuspay/flink/{job,function,model,util},src/main/resources,src/test/java/com/nexuspay/flink,lib}
```

최종 디렉토리 구조:

```
flink-jobs/
├── pom.xml                              # Maven 빌드 설정
├── src/
│   ├── main/
│   │   ├── java/com/nexuspay/flink/
│   │   │   ├── job/                     # Flink Job 엔트리포인트
│   │   │   │   ├── TransactionAggregationJob.java   # 윈도우 집계 잡
│   │   │   │   └── FraudDetectionJob.java           # 이상거래 탐지 잡
│   │   │   ├── function/                # 커스텀 함수
│   │   │   │   ├── TransactionAggregateFunction.java
│   │   │   │   ├── FraudPatternFunction.java
│   │   │   │   └── LateDataSideOutputFunction.java
│   │   │   ├── model/                   # 데이터 모델 (POJO)
│   │   │   │   ├── NexusPayEvent.java
│   │   │   │   ├── AggregatedResult.java
│   │   │   │   └── FraudAlert.java
│   │   │   └── util/                    # 유틸리티
│   │   │       ├── NexusPayEventDeserializer.java
│   │   │       └── FlinkConfigUtil.java
│   │   └── resources/
│   │       └── flink-conf.yaml
│   └── test/java/com/nexuspay/flink/
│       └── TransactionAggregationJobTest.java
└── lib/                                 # 외부 의존성 JAR
```

### 1-3. Maven 프로젝트 설정 (pom.xml)

```bash
cat > flink-jobs/pom.xml << 'POMEOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.nexuspay</groupId>
    <artifactId>flink-jobs</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <flink.version>1.18.1</flink.version>
        <kafka.version>3.7.0</kafka.version>
        <java.version>11</java.version>
        <maven.compiler.source>${java.version}</maven.compiler.source>
        <maven.compiler.target>${java.version}</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <dependencies>
        <!-- Flink Core -->
        <dependency>
            <groupId>org.apache.flink</groupId>
            <artifactId>flink-streaming-java</artifactId>
            <version>${flink.version}</version>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>org.apache.flink</groupId>
            <artifactId>flink-clients</artifactId>
            <version>${flink.version}</version>
            <scope>provided</scope>
        </dependency>

        <!-- Flink Kafka Connector -->
        <dependency>
            <groupId>org.apache.flink</groupId>
            <artifactId>flink-connector-kafka</artifactId>
            <version>3.1.0-1.18</version>
        </dependency>

        <!-- Flink CEP (Complex Event Processing) -->
        <dependency>
            <groupId>org.apache.flink</groupId>
            <artifactId>flink-cep</artifactId>
            <version>${flink.version}</version>
        </dependency>

        <!-- JSON 처리 -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.17.0</version>
        </dependency>

        <!-- 로깅 -->
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-api</artifactId>
            <version>2.0.12</version>
        </dependency>

        <!-- 테스트 -->
        <dependency>
            <groupId>org.apache.flink</groupId>
            <artifactId>flink-test-utils</artifactId>
            <version>${flink.version}</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>3.5.2</version>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals><goal>shade</goal></goals>
                        <configuration>
                            <artifactSet>
                                <excludes>
                                    <exclude>org.apache.flink:flink-shaded-force-shading</exclude>
                                    <exclude>com.google.code.findbugs:jsr305</exclude>
                                </excludes>
                            </artifactSet>
                            <transformers>
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                                    <mainClass>com.nexuspay.flink.job.TransactionAggregationJob</mainClass>
                                </transformer>
                            </transformers>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
POMEOF
```

### 1-4. 데이터 모델 — NexusPayEvent POJO

Week 3에서 NiFi가 `nexuspay.events.ingested` 토픽에 전송하는 표준 스키마에 맞춘 Java POJO를 정의한다.

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/model/NexusPayEvent.java << 'JAVAEOF'
package com.nexuspay.flink.model;

import java.io.Serializable;

/**
 * Nexus Pay 표준 이벤트 모델.
 * Week 3 NiFi 스키마 표준화에서 정의한 nexuspay-standard-schema.avsc와 1:1 대응.
 *
 * 필드 매핑:
 *   event_id       — 이벤트 고유 ID
 *   event_type     — PAYMENT | TRANSFER | WITHDRAWAL | SETTLEMENT | CUSTOMER_UPDATE
 *   user_id        — 사용자 ID (파티션 키)
 *   amount         — 거래 금액 (결제·이체·출금·정산)
 *   currency       — 통화 코드 (KRW, USD 등)
 *   status         — 이벤트 상태
 *   data_source    — payment-api | settlement-csv | customer-db
 *   event_timestamp — 이벤트 발생 시각 (ISO 8601)
 *   schema_version — 스키마 버전
 */
public class NexusPayEvent implements Serializable {
    private static final long serialVersionUID = 1L;

    private String eventId;
    private String eventType;
    private Integer userId;
    private Double amount;
    private String currency;
    private String status;
    private String dataSource;
    private String eventTimestamp;  // ISO 8601: "2026-04-07T14:30:00Z"
    private String schemaVersion;
    // NiFi 표준 스키마의 추가 필드 (merchant, channel, 이상거래 플래그)
    private String merchantId;
    private String merchantName;
    private String merchantCategory;
    private String channel;
    private Boolean isSuspicious;

    // 기본 생성자 (Flink 직렬화 필수)
    public NexusPayEvent() {}

    // Getters & Setters
    public String getEventId() { return eventId; }
    public void setEventId(String eventId) { this.eventId = eventId; }

    public String getEventType() { return eventType; }
    public void setEventType(String eventType) { this.eventType = eventType; }

    public Integer getUserId() { return userId; }
    public void setUserId(Integer userId) { this.userId = userId; }

    public Double getAmount() { return amount; }
    public void setAmount(Double amount) { this.amount = amount; }

    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getDataSource() { return dataSource; }
    public void setDataSource(String dataSource) { this.dataSource = dataSource; }

    public String getEventTimestamp() { return eventTimestamp; }
    public void setEventTimestamp(String eventTimestamp) { this.eventTimestamp = eventTimestamp; }

    public String getSchemaVersion() { return schemaVersion; }
    public void setSchemaVersion(String schemaVersion) { this.schemaVersion = schemaVersion; }

    public String getMerchantId() { return merchantId; }
    public void setMerchantId(String merchantId) { this.merchantId = merchantId; }

    public String getMerchantName() { return merchantName; }
    public void setMerchantName(String merchantName) { this.merchantName = merchantName; }

    public String getMerchantCategory() { return merchantCategory; }
    public void setMerchantCategory(String merchantCategory) { this.merchantCategory = merchantCategory; }

    public String getChannel() { return channel; }
    public void setChannel(String channel) { this.channel = channel; }

    public Boolean getIsSuspicious() { return isSuspicious; }
    public void setIsSuspicious(Boolean isSuspicious) { this.isSuspicious = isSuspicious; }

    /**
     * 이벤트 타임스탬프를 epoch milliseconds로 변환.
     * Watermark 할당에 사용.
     */
    public long getEventTimeMillis() {
        try {
            return java.time.Instant.parse(this.eventTimestamp).toEpochMilli();
        } catch (Exception e) {
            // 파싱 실패 시 현재 시간 반환 (Side Output으로 별도 처리 권장)
            return System.currentTimeMillis();
        }
    }

    @Override
    public String toString() {
        return String.format("NexusPayEvent{id=%s, type=%s, user=%d, amount=%.0f, time=%s}",
                eventId, eventType, userId, amount, eventTimestamp);
    }
}
JAVAEOF
```

### 1-5. JSON 역직렬화기 — Kafka 메시지 → NexusPayEvent

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/util/NexusPayEventDeserializer.java << 'JAVAEOF'
package com.nexuspay.flink.util;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.nexuspay.flink.model.NexusPayEvent;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import java.io.IOException;

/**
 * Kafka에서 수신한 JSON 바이트를 NexusPayEvent POJO로 변환.
 * NiFi 표준 스키마의 snake_case 필드명을 Java camelCase에 매핑.
 */
public class NexusPayEventDeserializer implements DeserializationSchema<NexusPayEvent> {
    private static final long serialVersionUID = 1L;
    private transient ObjectMapper mapper;

    private ObjectMapper getMapper() {
        if (mapper == null) {
            mapper = new ObjectMapper();
            mapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
            mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        }
        return mapper;
    }

    @Override
    public NexusPayEvent deserialize(byte[] message) throws IOException {
        try {
            return getMapper().readValue(message, NexusPayEvent.class);
        } catch (Exception e) {
            // 역직렬화 실패 시 null 반환 → .filter()로 제거
            return null;
        }
    }

    @Override
    public boolean isEndOfStream(NexusPayEvent event) {
        return false;  // 무한 스트림
    }

    @Override
    public TypeInformation<NexusPayEvent> getProducedType() {
        return TypeInformation.of(NexusPayEvent.class);
    }
}
JAVAEOF
```

### 1-6. Kafka 소스 연동 — 기본 스트림 구성

Flink가 `nexuspay.events.ingested` 토픽에서 이벤트를 소비하는 기본 잡을 구성한다.

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/job/TransactionAggregationJob.java << 'JAVAEOF'
package com.nexuspay.flink.job;

import com.nexuspay.flink.model.NexusPayEvent;
import com.nexuspay.flink.util.NexusPayEventDeserializer;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

import java.time.Duration;

/**
 * Nexus Pay 거래 실시간 집계 잡.
 *
 * 파이프라인:
 *   Kafka(nexuspay.events.ingested)
 *     → Watermark 할당
 *     → 거래 이벤트 필터링 (PAYMENT, TRANSFER, WITHDRAWAL)
 *     → 윈도우 집계 (5분 Tumbling)
 *     → 결과 싱크 (Kafka + Redis)
 */
public class TransactionAggregationJob {

    public static void main(String[] args) throws Exception {
        // 1. 실행 환경 구성
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // 체크포인트 활성화 (Exactly-once 기반 — Day 4에서 상세 설정)
        env.enableCheckpointing(60_000);  // 60초 주기

        // 2. Kafka 소스 구성
        KafkaSource<NexusPayEvent> kafkaSource = KafkaSource.<NexusPayEvent>builder()
                .setBootstrapServers("kafka-1:9092,kafka-2:9092,kafka-3:9092")
                .setTopics("nexuspay.events.ingested")
                .setGroupId("flink-aggregation")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new NexusPayEventDeserializer())
                .build();

        // 3. Watermark 전략 — 최대 5초 지연 허용
        WatermarkStrategy<NexusPayEvent> watermarkStrategy = WatermarkStrategy
                .<NexusPayEvent>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                .withTimestampAssigner((event, timestamp) -> event.getEventTimeMillis())
                .withIdleness(Duration.ofMinutes(1));  // 1분간 데이터 없으면 idle 처리

        // 4. 데이터 스트림 생성
        DataStream<NexusPayEvent> eventStream = env
                .fromSource(kafkaSource, watermarkStrategy, "Nexus Pay Kafka Source")
                .filter(event -> event != null)  // 역직렬화 실패 이벤트 제거
                .name("Filter Null Events");

        // 5. 거래 이벤트만 필터링 (CUSTOMER_UPDATE 제외)
        DataStream<NexusPayEvent> transactionStream = eventStream
                .filter(event -> {
                    String type = event.getEventType();
                    return "PAYMENT".equals(type) || "TRANSFER".equals(type)
                            || "WITHDRAWAL".equals(type) || "SETTLEMENT".equals(type);
                })
                .name("Filter Transaction Events");

        // Day 2에서 윈도우 집계 추가
        // Day 3에서 이상거래 탐지 분기 추가
        // Day 4에서 Exactly-once 싱크 추가

        // 6. 디버깅용 콘솔 출력 (Day 1 검증용)
        transactionStream.print("TX-EVENT");

        // 7. 잡 실행
        env.execute("Nexus Pay Transaction Aggregation Job v1.0");
    }
}
JAVAEOF
```

### 1-7. 테스트용 이벤트 생성기 — Kafka에 직접 주입

NiFi가 기동 중이라면 자연스럽게 데이터가 흐르지만, Flink 개발·디버깅을 위해 직접 이벤트를 주입하는 스크립트를 작성한다.

```bash
cat > scripts/flink_event_generator.py << 'PYEOF'
#!/usr/bin/env python3
"""
Flink 실습용 이벤트 생성기.
nexuspay.events.ingested 토픽에 테스트 이벤트를 주입한다.

사용법:
  python3 scripts/flink_event_generator.py --mode normal    # 정상 거래 생성
  python3 scripts/flink_event_generator.py --mode fraud     # 이상거래 포함 생성
  python3 scripts/flink_event_generator.py --mode late      # 지연 데이터 포함 생성
  python3 scripts/flink_event_generator.py --mode burst     # 대량 버스트 생성
"""

import json
import time
import random
import argparse
import uuid
from datetime import datetime, timezone, timedelta
from confluent_kafka import Producer

BOOTSTRAP_SERVERS = "localhost:30092,localhost:30093,localhost:30094"
TOPIC = "nexuspay.events.ingested"

EVENT_TYPES = ["PAYMENT", "TRANSFER", "WITHDRAWAL"]
CURRENCIES = ["KRW", "KRW", "KRW", "USD"]  # KRW 가중
STATUSES = ["COMPLETED", "COMPLETED", "COMPLETED", "PENDING", "FAILED"]

def create_event(user_id=None, event_type=None, amount=None, timestamp=None):
    """단일 Nexus Pay 이벤트 생성."""
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type or random.choice(EVENT_TYPES),
        "user_id": user_id or random.randint(1001, 2000),
        "amount": amount or round(random.uniform(1000, 3000000), 0),
        "currency": random.choice(CURRENCIES),
        "status": random.choice(STATUSES),
        "data_source": "payment-api",
        "event_timestamp": (timestamp or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0"
    }

def generate_normal(producer, count=100, interval=0.5):
    """정상 거래 이벤트 생성."""
    print(f"[NORMAL] {count}건 정상 거래 생성 시작 (간격: {interval}초)")
    for i in range(count):
        event = create_event()
        producer.produce(TOPIC, key=str(event["user_id"]), value=json.dumps(event))
        producer.poll(0)
        if (i + 1) % 10 == 0:
            print(f"  ... {i + 1}/{count}건 전송")
        time.sleep(interval)
    producer.flush()
    print(f"[NORMAL] {count}건 전송 완료")

def generate_fraud(producer, count=50):
    """이상거래 패턴 포함 이벤트 생성."""
    print(f"[FRAUD] 이상거래 패턴 포함 {count}건 생성 시작")
    fraud_user = random.randint(1001, 2000)

    for i in range(count):
        if i % 10 == 0:
            # 패턴 1: 동일 사용자 1분 내 연속 5건 (임계값 3건 초과)
            print(f"  [패턴1] user_id={fraud_user} 연속 5건 발생")
            base_time = datetime.now(timezone.utc)
            for j in range(5):
                event = create_event(
                    user_id=fraud_user,
                    event_type="PAYMENT",
                    amount=random.uniform(100000, 500000),
                    timestamp=base_time + timedelta(seconds=j * 10)
                )
                producer.produce(TOPIC, key=str(event["user_id"]), value=json.dumps(event))
        producer.poll(0)
                time.sleep(0.1)

        elif i % 15 == 0:
            # 패턴 2: 단건 고액 거래 (500만원 초과)
            high_amount = random.uniform(5_000_001, 50_000_000)
            event = create_event(amount=high_amount, event_type="TRANSFER")
            print(f"  [패턴2] 고액 거래: {high_amount:,.0f}원")
            producer.produce(TOPIC, key=str(event["user_id"]), value=json.dumps(event))
        producer.poll(0)

        else:
            event = create_event()
            producer.produce(TOPIC, key=str(event["user_id"]), value=json.dumps(event))
        producer.poll(0)

        time.sleep(0.3)

    producer.flush()
    print(f"[FRAUD] {count}건 전송 완료")

def generate_late(producer, count=50):
    """지연 데이터 포함 이벤트 생성 — Watermark 테스트용."""
    print(f"[LATE] 지연 데이터 포함 {count}건 생성 시작")
    for i in range(count):
        if i % 8 == 0:
            # 10~30초 전 타임스탬프를 가진 지연 이벤트
            delay_seconds = random.randint(10, 30)
            late_time = datetime.now(timezone.utc) - timedelta(seconds=delay_seconds)
            event = create_event(timestamp=late_time)
            print(f"  [LATE] {delay_seconds}초 지연 이벤트: {event['event_timestamp']}")
        else:
            event = create_event()

        producer.produce(TOPIC, key=str(event["user_id"]), value=json.dumps(event))
        producer.poll(0)
        time.sleep(0.3)

    producer.flush()
    print(f"[LATE] {count}건 전송 완료")

def generate_burst(producer, count=500):
    """대량 버스트 — 성능 테스트용."""
    print(f"[BURST] {count}건 대량 버스트 생성 시작")
    for i in range(count):
        event = create_event()
        producer.produce(TOPIC, key=str(event["user_id"]), value=json.dumps(event))
        producer.poll(0)
    producer.flush()
    print(f"[BURST] {count}건 전송 완료 (무간격)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flink 실습용 Nexus Pay 이벤트 생성기")
    parser.add_argument("--mode", choices=["normal", "fraud", "late", "burst"], default="normal")
    parser.add_argument("--count", type=int, default=100)
    args = parser.parse_args()

    producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})

    modes = {
        "normal": lambda: generate_normal(producer, args.count),
        "fraud": lambda: generate_fraud(producer, args.count),
        "late": lambda: generate_late(producer, args.count),
        "burst": lambda: generate_burst(producer, args.count),
    }
    modes[args.mode]()
    producer.flush()
PYEOF

chmod +x scripts/flink_event_generator.py
```

### 1-8. Flink 잡 빌드 및 기본 검증

```bash
# Maven 빌드 (Docker 컨테이너 내부에서)
cd flink-jobs
docker run --rm -v $(pwd):/app -w /app maven:3.9-eclipse-temurin-11 \
  mvn clean package -DskipTests

# 빌드된 JAR 확인
ls -la target/flink-jobs-1.0.0.jar

# Flink 클러스터에 JAR 제출 (Day 1 검증용)
docker cp target/flink-jobs-1.0.0.jar lab-flink-jm:/opt/flink/usrlib/

docker exec lab-flink-jm /opt/flink/bin/flink run \
  -d /opt/flink/usrlib/flink-jobs-1.0.0.jar

# Flink Dashboard에서 잡 상태 확인
curl -s http://localhost:8081/jobs | python3 -m json.tool
# 기대: status = RUNNING

# 테스트 이벤트 주입
pip3 install confluent-kafka --break-system-packages
python3 scripts/flink_event_generator.py --mode normal --count 20

# Flink TaskManager 로그에서 이벤트 수신 확인
docker logs lab-flink-tm --tail 20 | grep "TX-EVENT"
# 기대: NexusPayEvent{id=..., type=PAYMENT, user=42, amount=1500000, time=...}
```

**Day 1 완료 기준**: Flink 핵심 개념 문서 작성, Maven 프로젝트 빌드 성공, Kafka 소스 연동 잡이 RUNNING 상태, 테스트 이벤트 20건 수신 확인.

---

## Day 2: Watermark + 윈도우 집계

### 2-1. 집계 결과 모델 정의

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/model/AggregatedResult.java << 'JAVAEOF'
package com.nexuspay.flink.model;

import java.io.Serializable;

/**
 * 윈도우 집계 결과 모델.
 * 5분 Tumbling Window 기준으로 이벤트 타입별 집계값을 담는다.
 */
public class AggregatedResult implements Serializable {
    private static final long serialVersionUID = 1L;

    private String eventType;        // PAYMENT | TRANSFER | WITHDRAWAL | SETTLEMENT
    private String windowStart;      // 윈도우 시작 시각 (ISO 8601)
    private String windowEnd;        // 윈도우 종료 시각 (ISO 8601)
    private long transactionCount;   // 거래 건수
    private double totalAmount;      // 거래 총액
    private double avgAmount;        // 평균 거래 금액
    private double maxAmount;        // 최대 거래 금액
    private double minAmount;        // 최소 거래 금액

    public AggregatedResult() {}

    public AggregatedResult(String eventType, String windowStart, String windowEnd,
                            long count, double total, double avg, double max, double min) {
        this.eventType = eventType;
        this.windowStart = windowStart;
        this.windowEnd = windowEnd;
        this.transactionCount = count;
        this.totalAmount = total;
        this.avgAmount = avg;
        this.maxAmount = max;
        this.minAmount = min;
    }

    // Getters & Setters
    public String getEventType() { return eventType; }
    public void setEventType(String eventType) { this.eventType = eventType; }
    public String getWindowStart() { return windowStart; }
    public void setWindowStart(String windowStart) { this.windowStart = windowStart; }
    public String getWindowEnd() { return windowEnd; }
    public void setWindowEnd(String windowEnd) { this.windowEnd = windowEnd; }
    public long getTransactionCount() { return transactionCount; }
    public void setTransactionCount(long transactionCount) { this.transactionCount = transactionCount; }
    public double getTotalAmount() { return totalAmount; }
    public void setTotalAmount(double totalAmount) { this.totalAmount = totalAmount; }
    public double getAvgAmount() { return avgAmount; }
    public void setAvgAmount(double avgAmount) { this.avgAmount = avgAmount; }
    public double getMaxAmount() { return maxAmount; }
    public void setMaxAmount(double maxAmount) { this.maxAmount = maxAmount; }
    public double getMinAmount() { return minAmount; }
    public void setMinAmount(double minAmount) { this.minAmount = minAmount; }

    @Override
    public String toString() {
        return String.format(
            "AggResult{type=%s, window=[%s ~ %s], count=%d, total=%.0f, avg=%.0f, max=%.0f}",
            eventType, windowStart, windowEnd, transactionCount, totalAmount, avgAmount, maxAmount
        );
    }

    /**
     * JSON 직렬화 (Kafka 싱크용).
     */
    public String toJson() {
        return String.format(
            "{\"event_type\":\"%s\",\"window_start\":\"%s\",\"window_end\":\"%s\"," +
            "\"transaction_count\":%d,\"total_amount\":%.0f,\"avg_amount\":%.0f," +
            "\"max_amount\":%.0f,\"min_amount\":%.0f}",
            eventType, windowStart, windowEnd, transactionCount, totalAmount, avgAmount, maxAmount, minAmount
        );
    }
}
JAVAEOF
```

### 2-2. 커스텀 집계 함수 — AggregateFunction + ProcessWindowFunction

Flink의 윈도우 집계는 두 단계로 구성된다. `AggregateFunction`이 이벤트를 누적하고, `ProcessWindowFunction`이 윈도우 메타데이터(시작·종료 시각)를 붙여 최종 결과를 생성한다.

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/function/TransactionAggregateFunction.java << 'JAVAEOF'
package com.nexuspay.flink.function;

import com.nexuspay.flink.model.AggregatedResult;
import com.nexuspay.flink.model.NexusPayEvent;
import org.apache.flink.api.common.functions.AggregateFunction;

/**
 * 거래 이벤트 증분 집계 함수.
 *
 * 누적기(Accumulator)에 건수·총액·최대·최소를 증분 갱신한다.
 * 메모리 효율적 — 원본 이벤트를 저장하지 않고 통계값만 유지.
 */
public class TransactionAggregateFunction
        implements AggregateFunction<NexusPayEvent, TransactionAggregateFunction.Accumulator, AggregatedResult> {

    /**
     * 중간 집계 상태.
     */
    public static class Accumulator implements java.io.Serializable {
        public long count = 0;
        public double totalAmount = 0.0;
        public double maxAmount = Double.MIN_VALUE;
        public double minAmount = Double.MAX_VALUE;
    }

    @Override
    public Accumulator createAccumulator() {
        return new Accumulator();
    }

    @Override
    public Accumulator add(NexusPayEvent event, Accumulator acc) {
        acc.count++;
        double amount = event.getAmount() != null ? event.getAmount() : 0.0;
        acc.totalAmount += amount;
        acc.maxAmount = Math.max(acc.maxAmount, amount);
        acc.minAmount = Math.min(acc.minAmount, amount);
        return acc;
    }

    @Override
    public AggregatedResult getResult(Accumulator acc) {
        // 윈도우 메타데이터는 ProcessWindowFunction에서 추가
        double avg = acc.count > 0 ? acc.totalAmount / acc.count : 0.0;
        return new AggregatedResult(
                null, null, null,  // eventType, windowStart, windowEnd — ProcessWindowFunction에서 설정
                acc.count, acc.totalAmount, avg, acc.maxAmount,
                acc.count > 0 ? acc.minAmount : 0.0
        );
    }

    @Override
    public Accumulator merge(Accumulator a, Accumulator b) {
        a.count += b.count;
        a.totalAmount += b.totalAmount;
        a.maxAmount = Math.max(a.maxAmount, b.maxAmount);
        a.minAmount = Math.min(a.minAmount, b.minAmount);
        return a;
    }
}
JAVAEOF
```

### 2-3. ProcessWindowFunction — 윈도우 메타데이터 바인딩

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/function/TransactionWindowFunction.java << 'JAVAEOF'
package com.nexuspay.flink.function;

import com.nexuspay.flink.model.AggregatedResult;
import org.apache.flink.streaming.api.functions.windowing.ProcessWindowFunction;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;
import org.apache.flink.util.Collector;

import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

/**
 * 윈도우 메타데이터(시작·종료 시각, 키)를 집계 결과에 바인딩.
 * AggregateFunction과 결합하여 사용.
 */
public class TransactionWindowFunction
        extends ProcessWindowFunction<AggregatedResult, AggregatedResult, String, TimeWindow> {

    private static final DateTimeFormatter ISO_FMT =
            DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'").withZone(ZoneOffset.UTC);

    @Override
    public void process(String key, Context context, Iterable<AggregatedResult> results,
                        Collector<AggregatedResult> out) {
        AggregatedResult result = results.iterator().next();  // AggregateFunction에서 이미 단일 결과

        // 윈도우 메타데이터 바인딩
        result.setEventType(key);
        result.setWindowStart(ISO_FMT.format(Instant.ofEpochMilli(context.window().getStart())));
        result.setWindowEnd(ISO_FMT.format(Instant.ofEpochMilli(context.window().getEnd())));

        out.collect(result);
    }
}
JAVAEOF
```

### 2-4. Late Data Side Output 처리

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/function/LateDataSideOutputFunction.java << 'JAVAEOF'
package com.nexuspay.flink.function;

import com.nexuspay.flink.model.NexusPayEvent;
import org.apache.flink.util.OutputTag;

/**
 * 지연 데이터(Late Data) Side Output 태그 정의.
 *
 * Watermark 이후 도착한 이벤트는 Side Output으로 분리하여:
 * 1. DLQ 토픽으로 전송 (재처리 또는 수동 검토)
 * 2. 별도 로그에 기록 (감사 추적)
 * 3. 지연 통계 수집 (Watermark 전략 튜닝 자료)
 */
public class LateDataSideOutputFunction {

    /** 지연 이벤트를 별도 스트림으로 분리하는 태그. */
    public static final OutputTag<NexusPayEvent> LATE_DATA_TAG =
            new OutputTag<NexusPayEvent>("late-data") {};
}
JAVAEOF
```

### 2-5. TransactionAggregationJob 업데이트 — 윈도우 집계 추가

Day 1에서 작성한 잡에 윈도우 집계 로직을 추가한다.

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/job/TransactionAggregationJob.java << 'JAVAEOF'
package com.nexuspay.flink.job;

import com.nexuspay.flink.function.LateDataSideOutputFunction;
import com.nexuspay.flink.function.TransactionAggregateFunction;
import com.nexuspay.flink.function.TransactionWindowFunction;
import com.nexuspay.flink.model.AggregatedResult;
import com.nexuspay.flink.model.NexusPayEvent;
import com.nexuspay.flink.util.NexusPayEventDeserializer;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.datastream.SingleOutputStreamOperator;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.windowing.assigners.TumblingEventTimeWindows;
import org.apache.flink.streaming.api.windowing.assigners.SlidingEventTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;

import java.time.Duration;

/**
 * Nexus Pay 거래 실시간 집계 잡 — v2.0 (윈도우 집계 포함).
 *
 * 파이프라인 구조:
 *   Kafka(nexuspay.events.ingested)
 *     → Watermark 할당 (5초 지연 허용)
 *     → 거래 이벤트 필터링
 *     → keyBy(eventType)
 *     ├── [Tumbling 5분] 거래 유형별 5분 단위 집계
 *     ├── [Sliding 5분/1분] 1분마다 갱신되는 5분 이동 평균
 *     └── [Late Data] Side Output → DLQ
 */
public class TransactionAggregationJob {

    public static void main(String[] args) throws Exception {
        // ── 1. 실행 환경 ──
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.enableCheckpointing(60_000);
        env.getConfig().setAutoWatermarkInterval(1000);  // Watermark 1초 주기 갱신

        // ── 2. Kafka 소스 ──
        KafkaSource<NexusPayEvent> kafkaSource = KafkaSource.<NexusPayEvent>builder()
                .setBootstrapServers("kafka-1:9092,kafka-2:9092,kafka-3:9092")
                .setTopics("nexuspay.events.ingested")
                .setGroupId("flink-aggregation")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new NexusPayEventDeserializer())
                .build();

        // ── 3. Watermark 전략 ──
        WatermarkStrategy<NexusPayEvent> watermarkStrategy = WatermarkStrategy
                .<NexusPayEvent>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                .withTimestampAssigner((event, ts) -> event.getEventTimeMillis())
                .withIdleness(Duration.ofMinutes(1));

        // ── 4. 소스 스트림 ──
        DataStream<NexusPayEvent> eventStream = env
                .fromSource(kafkaSource, watermarkStrategy, "Nexus Pay Kafka Source")
                .filter(event -> event != null)
                .name("Filter Null Events");

        // ── 5. 거래 이벤트 필터 ──
        DataStream<NexusPayEvent> txStream = eventStream
                .filter(event -> {
                    String type = event.getEventType();
                    return "PAYMENT".equals(type) || "TRANSFER".equals(type)
                            || "WITHDRAWAL".equals(type) || "SETTLEMENT".equals(type);
                })
                .name("Filter Transaction Events");

        // ── 6. Tumbling Window — 5분 단위 집계 ──
        SingleOutputStreamOperator<AggregatedResult> tumblingResult = txStream
                .keyBy(NexusPayEvent::getEventType)
                .window(TumblingEventTimeWindows.of(Time.minutes(5)))
                .allowedLateness(Time.seconds(10))                    // 10초 추가 지연 허용
                .sideOutputLateData(LateDataSideOutputFunction.LATE_DATA_TAG)  // 그 이후 → Side Output
                .aggregate(
                        new TransactionAggregateFunction(),
                        new TransactionWindowFunction()
                )
                .name("5min Tumbling Aggregation");

        // 집계 결과 출력 (Day 4에서 Kafka 싱크로 교체)
        tumblingResult.print("TUMBLING-5MIN");

        // ── 7. Sliding Window — 5분 윈도우, 1분 슬라이드 (이동 평균) ──
        SingleOutputStreamOperator<AggregatedResult> slidingResult = txStream
                .keyBy(NexusPayEvent::getEventType)
                .window(SlidingEventTimeWindows.of(Time.minutes(5), Time.minutes(1)))
                .allowedLateness(Time.seconds(10))
                .sideOutputLateData(LateDataSideOutputFunction.LATE_DATA_TAG)
                .aggregate(
                        new TransactionAggregateFunction(),
                        new TransactionWindowFunction()
                )
                .name("5min Sliding (1min step) Aggregation");

        slidingResult.print("SLIDING-5MIN-1MIN");

        // ── 8. Late Data 처리 ──
        DataStream<NexusPayEvent> lateData = tumblingResult
                .getSideOutput(LateDataSideOutputFunction.LATE_DATA_TAG);

        lateData.print("LATE-DATA");
        // Day 4에서 DLQ Kafka 싱크 연결

        // ── 9. 잡 실행 ──
        env.execute("Nexus Pay Transaction Aggregation Job v2.0");
    }
}
JAVAEOF
```

### 2-6. Watermark 동작 검증

```bash
# 빌드
cd flink-jobs
docker run --rm -v $(pwd):/app -w /app maven:3.9-eclipse-temurin-11 \
  mvn clean package -DskipTests

# 기존 잡 취소 (Day 1 잡)
JOB_ID=$(curl -s http://localhost:8081/jobs | python3 -c "import sys,json; jobs=json.load(sys.stdin)['jobs']; print(jobs[0]['id'] if jobs else '')")
if [ -n "$JOB_ID" ]; then
  curl -X PATCH "http://localhost:8081/jobs/$JOB_ID?mode=cancel"
  echo "기존 잡 취소: $JOB_ID"
  sleep 5
fi

# 새 잡 제출
docker cp target/flink-jobs-1.0.0.jar lab-flink-jm:/opt/flink/usrlib/
docker exec lab-flink-jm /opt/flink/bin/flink run \
  -d /opt/flink/usrlib/flink-jobs-1.0.0.jar

# 정상 이벤트 생성
python3 scripts/flink_event_generator.py --mode normal --count 50

# 5분 대기 후 Tumbling Window 결과 확인
echo "5분 윈도우 결과를 기다리는 중..."
sleep 310
docker logs lab-flink-tm --tail 30 | grep "TUMBLING-5MIN"
# 기대: AggResult{type=PAYMENT, window=[...], count=N, total=...}

# 지연 데이터 테스트
python3 scripts/flink_event_generator.py --mode late --count 30

# Late Data Side Output 확인
sleep 30
docker logs lab-flink-tm --tail 20 | grep "LATE-DATA"
# 기대: 지연 이벤트가 Side Output으로 분리되어 출력
```

### 2-7. Session Window — 사용자 활동 세션 분석

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/job/SessionWindowAnalysisJob.java << 'JAVAEOF'
package com.nexuspay.flink.job;

import com.nexuspay.flink.model.NexusPayEvent;
import com.nexuspay.flink.util.NexusPayEventDeserializer;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.java.tuple.Tuple4;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.windowing.assigners.EventTimeSessionWindows;
import org.apache.flink.streaming.api.windowing.time.Time;

import java.time.Duration;

/**
 * Session Window 분석 잡.
 *
 * 사용자별 활동 세션을 동적으로 감지한다.
 * 2분간 거래가 없으면 세션 종료 → 세션별 거래 건수·총액 집계.
 *
 * 활용: 사용자 행동 패턴 분석, 이상 세션 탐지 (한 세션에 비정상 다수 거래).
 */
public class SessionWindowAnalysisJob {

    public static void main(String[] args) throws Exception {
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.enableCheckpointing(60_000);

        KafkaSource<NexusPayEvent> kafkaSource = KafkaSource.<NexusPayEvent>builder()
                .setBootstrapServers("kafka-1:9092,kafka-2:9092,kafka-3:9092")
                .setTopics("nexuspay.events.ingested")
                .setGroupId("flink-session-analysis")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new NexusPayEventDeserializer())
                .build();

        WatermarkStrategy<NexusPayEvent> wmStrategy = WatermarkStrategy
                .<NexusPayEvent>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                .withTimestampAssigner((event, ts) -> event.getEventTimeMillis())
                .withIdleness(Duration.ofMinutes(1));

        DataStream<NexusPayEvent> eventStream = env
                .fromSource(kafkaSource, wmStrategy, "Nexus Pay Kafka Source")
                .filter(e -> e != null && e.getUserId() != null);

        // Session Window: 2분 비활동 간격으로 세션 분리
        eventStream
                .keyBy(event -> String.valueOf(event.getUserId()))
                .window(EventTimeSessionWindows.withGap(Time.minutes(2)))
                .reduce((e1, e2) -> {
                    // 간단한 reduce: 건수 합산을 위해 amount를 누적
                    NexusPayEvent merged = new NexusPayEvent();
                    merged.setUserId(e1.getUserId());
                    merged.setEventType("SESSION_SUMMARY");
                    merged.setAmount((e1.getAmount() != null ? e1.getAmount() : 0)
                            + (e2.getAmount() != null ? e2.getAmount() : 0));
                    merged.setEventTimestamp(e2.getEventTimestamp());
                    return merged;
                })
                .print("SESSION");

        env.execute("Nexus Pay Session Window Analysis");
    }
}
JAVAEOF
```

### 2-8. 윈도우 유형 비교 정리

```bash
cat >> docs/flink-concepts.md << 'EOF'

## 윈도우 유형 비교 — Nexus Pay 실습 기준

| 윈도우 | 구현 | 용도 | 특성 |
|--------|------|------|------|
| Tumbling 5min | `TumblingEventTimeWindows.of(Time.minutes(5))` | 5분 단위 거래 통계 대시보드 | 겹침 없음, 정확한 구간 집계 |
| Sliding 5min/1min | `SlidingEventTimeWindows.of(Time.minutes(5), Time.minutes(1))` | 1분마다 갱신되는 이동 평균 | 겹침 있음, 부드러운 추세 |
| Session 2min gap | `EventTimeSessionWindows.withGap(Time.minutes(2))` | 사용자 활동 세션 분석 | 동적 크기, 행동 기반 |

### Watermark 전략 정리

| 파라미터 | 값 | 근거 |
|----------|-----|------|
| BoundedOutOfOrderness | 5초 | API 수집 주기(30초) 대비 충분한 여유 |
| allowedLateness | 10초 | Watermark 이후 추가 10초까지 윈도우 재계산 허용 |
| withIdleness | 1분 | 특정 파티션 데이터 없을 때 Watermark 진행 차단 방지 |
| Side Output | LATE_DATA_TAG | 15초(5+10) 이후 도착 → DLQ로 분리 |

### Late Data 처리 전략

```
이벤트 도착 시점에 따른 처리:
  
  [윈도우 종료 전]     → 정상 집계에 포함
  [종료 ~ +10초]       → allowedLateness — 윈도우 재계산 (업데이트 결과 emit)
  [+10초 초과]         → Side Output (LATE_DATA_TAG) → DLQ 토픽으로 전송
```

EOF
```

**Day 2 완료 기준**: Tumbling·Sliding·Session 세 가지 윈도우 집계 잡 구현, Watermark 기반 이벤트 타임 처리 검증, Late Data Side Output 동작 확인.

---

## Day 3: 실시간 이상거래 탐지

### 3-1. 이상거래 알림 모델 정의

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/model/FraudAlert.java << 'JAVAEOF'
package com.nexuspay.flink.model;

import java.io.Serializable;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

/**
 * 이상거래 탐지 알림 모델.
 *
 * 탐지 규칙:
 *   RULE-001: 동일 사용자 1분 내 3건 이상 연속 거래
 *   RULE-002: 단건 500만원 초과 거래
 *   RULE-003: 동일 사용자 1분 내 거래 금액 합계 1,000만원 초과
 */
public class FraudAlert implements Serializable {
    private static final long serialVersionUID = 1L;

    private String alertId;
    private String ruleId;          // RULE-001, RULE-002, RULE-003
    private String ruleDescription;
    private Integer userId;
    private String severity;        // HIGH, MEDIUM, LOW
    private String triggerEventId;  // 트리거 이벤트 ID
    private double triggerAmount;
    private int eventCount;         // 연관 이벤트 수
    private String detectedAt;      // 탐지 시각

    public FraudAlert() {}

    public FraudAlert(String ruleId, String description, Integer userId,
                      String severity, String triggerEventId, double amount, int count) {
        this.alertId = "ALERT-" + System.currentTimeMillis() + "-" + userId;
        this.ruleId = ruleId;
        this.ruleDescription = description;
        this.userId = userId;
        this.severity = severity;
        this.triggerEventId = triggerEventId;
        this.triggerAmount = amount;
        this.eventCount = count;
        this.detectedAt = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'")
                .withZone(ZoneOffset.UTC).format(Instant.now());
    }

    // Getters & Setters
    public String getAlertId() { return alertId; }
    public void setAlertId(String alertId) { this.alertId = alertId; }
    public String getRuleId() { return ruleId; }
    public void setRuleId(String ruleId) { this.ruleId = ruleId; }
    public String getRuleDescription() { return ruleDescription; }
    public void setRuleDescription(String desc) { this.ruleDescription = desc; }
    public Integer getUserId() { return userId; }
    public void setUserId(Integer userId) { this.userId = userId; }
    public String getSeverity() { return severity; }
    public void setSeverity(String severity) { this.severity = severity; }
    public String getTriggerEventId() { return triggerEventId; }
    public void setTriggerEventId(String id) { this.triggerEventId = id; }
    public double getTriggerAmount() { return triggerAmount; }
    public void setTriggerAmount(double amount) { this.triggerAmount = amount; }
    public int getEventCount() { return eventCount; }
    public void setEventCount(int count) { this.eventCount = count; }
    public String getDetectedAt() { return detectedAt; }
    public void setDetectedAt(String time) { this.detectedAt = time; }

    public String toJson() {
        return String.format(
            "{\"alert_id\":\"%s\",\"rule_id\":\"%s\",\"rule_description\":\"%s\"," +
            "\"user_id\":%d,\"severity\":\"%s\",\"trigger_event_id\":\"%s\"," +
            "\"trigger_amount\":%.0f,\"event_count\":%d,\"detected_at\":\"%s\"}",
            alertId, ruleId, ruleDescription, userId, severity,
            triggerEventId, triggerAmount, eventCount, detectedAt
        );
    }

    @Override
    public String toString() {
        return String.format("[%s] %s | user=%d, severity=%s, amount=%.0f, events=%d",
                ruleId, ruleDescription, userId, severity, triggerAmount, eventCount);
    }
}
JAVAEOF
```

### 3-2. 이상거래 탐지 함수 — KeyedProcessFunction 기반

CEP 라이브러리를 사용하는 패턴 매칭과 함께, `KeyedProcessFunction`을 활용한 상태 기반 탐지를 구현한다. 실무에서는 두 접근을 병행한다.

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/function/FraudDetectionFunction.java << 'JAVAEOF'
package com.nexuspay.flink.function;

import com.nexuspay.flink.model.FraudAlert;
import com.nexuspay.flink.model.NexusPayEvent;
import org.apache.flink.api.common.state.ListState;
import org.apache.flink.api.common.state.ListStateDescriptor;
import org.apache.flink.api.common.state.ValueState;
import org.apache.flink.api.common.state.ValueStateDescriptor;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.KeyedProcessFunction;
import org.apache.flink.util.Collector;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/**
 * 상태 기반 이상거래 탐지 함수.
 *
 * 사용자(userId)별로 키잉된 상태에서 다음 규칙을 실시간 평가:
 *
 * RULE-001: 동일 사용자 1분 내 3건 이상 연속 거래 → HIGH
 * RULE-002: 단건 500만원 초과 → HIGH
 * RULE-003: 1분 내 거래 합계 1,000만원 초과 → MEDIUM
 *
 * 상태:
 *   recentEvents: 최근 1분간 이벤트 리스트 (타이머로 만료 관리)
 *   lastCleanupTime: 마지막 상태 정리 시각
 */
public class FraudDetectionFunction
        extends KeyedProcessFunction<Integer, NexusPayEvent, FraudAlert> {

    // 탐지 임계값
    private static final int FREQUENCY_THRESHOLD = 3;      // 1분 내 최대 거래 건수
    private static final double HIGH_AMOUNT_THRESHOLD = 5_000_000.0;  // 단건 고액 임계값
    private static final double SUM_AMOUNT_THRESHOLD = 10_000_000.0;  // 1분 합계 임계값
    private static final long WINDOW_DURATION_MS = 60_000;  // 1분 (밀리초)

    // Keyed State
    private transient ListState<NexusPayEvent> recentEventsState;
    private transient ValueState<Long> lastCleanupState;

    @Override
    public void open(Configuration parameters) {
        recentEventsState = getRuntimeContext().getListState(
                new ListStateDescriptor<>("recent-events", TypeInformation.of(NexusPayEvent.class)));
        lastCleanupState = getRuntimeContext().getState(
                new ValueStateDescriptor<>("last-cleanup", Long.class));
    }

    @Override
    public void processElement(NexusPayEvent event, Context ctx, Collector<FraudAlert> out)
            throws Exception {

        long currentTime = event.getEventTimeMillis();

        // ── RULE-002: 단건 고액 거래 즉시 판정 ──
        if (event.getAmount() != null && event.getAmount() > HIGH_AMOUNT_THRESHOLD) {
            out.collect(new FraudAlert(
                    "RULE-002",
                    "단건 500만원 초과 거래",
                    event.getUserId(),
                    "HIGH",
                    event.getEventId(),
                    event.getAmount(),
                    1
            ));
        }

        // ── 상태 업데이트: 최근 이벤트 추가 ──
        recentEventsState.add(event);

        // ── 만료 이벤트 정리 (1분 경과) ──
        List<NexusPayEvent> activeEvents = new ArrayList<>();
        Iterator<NexusPayEvent> iter = recentEventsState.get().iterator();
        while (iter.hasNext()) {
            NexusPayEvent e = iter.next();
            if (currentTime - e.getEventTimeMillis() <= WINDOW_DURATION_MS) {
                activeEvents.add(e);
            }
        }
        recentEventsState.update(activeEvents);

        // ── RULE-001: 1분 내 연속 거래 빈도 검사 ──
        if (activeEvents.size() >= FREQUENCY_THRESHOLD) {
            out.collect(new FraudAlert(
                    "RULE-001",
                    "1분 내 " + activeEvents.size() + "건 연속 거래",
                    event.getUserId(),
                    "HIGH",
                    event.getEventId(),
                    event.getAmount() != null ? event.getAmount() : 0,
                    activeEvents.size()
            ));
        }

        // ── RULE-003: 1분 내 거래 합계 검사 ──
        double totalAmount = activeEvents.stream()
                .mapToDouble(e -> e.getAmount() != null ? e.getAmount() : 0)
                .sum();

        if (totalAmount > SUM_AMOUNT_THRESHOLD) {
            out.collect(new FraudAlert(
                    "RULE-003",
                    "1분 내 거래 합계 " + String.format("%.0f", totalAmount) + "원 초과",
                    event.getUserId(),
                    "MEDIUM",
                    event.getEventId(),
                    totalAmount,
                    activeEvents.size()
            ));
        }

        // ── 상태 정리 타이머 등록 (2분 후) ──
        Long lastCleanup = lastCleanupState.value();
        if (lastCleanup == null || currentTime - lastCleanup > WINDOW_DURATION_MS) {
            ctx.timerService().registerEventTimeTimer(currentTime + WINDOW_DURATION_MS * 2);
            lastCleanupState.update(currentTime);
        }
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<FraudAlert> out)
            throws Exception {
        // 타이머 발동 시 만료 이벤트 정리
        List<NexusPayEvent> activeEvents = new ArrayList<>();
        Iterator<NexusPayEvent> iter = recentEventsState.get().iterator();
        while (iter.hasNext()) {
            NexusPayEvent e = iter.next();
            if (timestamp - e.getEventTimeMillis() <= WINDOW_DURATION_MS) {
                activeEvents.add(e);
            }
        }
        recentEventsState.update(activeEvents);
    }
}
JAVAEOF
```

### 3-3. 이상거래 탐지 잡 — FraudDetectionJob

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/job/FraudDetectionJob.java << 'JAVAEOF'
package com.nexuspay.flink.job;

import com.nexuspay.flink.function.FraudDetectionFunction;
import com.nexuspay.flink.model.FraudAlert;
import com.nexuspay.flink.model.NexusPayEvent;
import com.nexuspay.flink.util.NexusPayEventDeserializer;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

import java.time.Duration;

/**
 * Nexus Pay 이상거래 실시간 탐지 잡.
 *
 * 파이프라인:
 *   Kafka(nexuspay.events.ingested)
 *     → Watermark 할당
 *     → keyBy(userId)
 *     → FraudDetectionFunction (상태 기반 규칙 평가)
 *     → 알림 싱크: Kafka(nexuspay.alerts.fraud) + 콘솔
 *
 * 탐지 규칙:
 *   RULE-001: 1분 내 3건 이상 연속 거래 (HIGH)
 *   RULE-002: 단건 500만원 초과 (HIGH)
 *   RULE-003: 1분 내 합계 1,000만원 초과 (MEDIUM)
 */
public class FraudDetectionJob {

    public static void main(String[] args) throws Exception {
        // ── 1. 환경 구성 ──
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.enableCheckpointing(30_000);  // 30초 주기 (이상거래는 빠른 복구 필요)

        // ── 2. Kafka 소스 ──
        KafkaSource<NexusPayEvent> kafkaSource = KafkaSource.<NexusPayEvent>builder()
                .setBootstrapServers("kafka-1:9092,kafka-2:9092,kafka-3:9092")
                .setTopics("nexuspay.events.ingested")
                .setGroupId("flink-fraud-detection")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new NexusPayEventDeserializer())
                .build();

        WatermarkStrategy<NexusPayEvent> wmStrategy = WatermarkStrategy
                .<NexusPayEvent>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                .withTimestampAssigner((event, ts) -> event.getEventTimeMillis())
                .withIdleness(Duration.ofMinutes(1));

        DataStream<NexusPayEvent> eventStream = env
                .fromSource(kafkaSource, wmStrategy, "Nexus Pay Kafka Source")
                .filter(event -> event != null && event.getUserId() != null)
                .name("Filter Valid Events");

        // ── 3. 이상거래 탐지 ──
        DataStream<FraudAlert> alerts = eventStream
                .keyBy(NexusPayEvent::getUserId)
                .process(new FraudDetectionFunction())
                .name("Fraud Detection Rules");

        // ── 4. 알림 콘솔 출력 (디버깅) ──
        alerts.print("FRAUD-ALERT");

        // ── 5. 알림 Kafka 싱크 ──
        KafkaSink<String> alertSink = KafkaSink.<String>builder()
                .setBootstrapServers("kafka-1:9092,kafka-2:9092,kafka-3:9092")
                .setRecordSerializer(KafkaRecordSerializationSchema.builder()
                        .setTopic("nexuspay.alerts.fraud")
                        .setValueSerializationSchema(new SimpleStringSchema())
                        .build())
                .build();

        alerts.map(FraudAlert::toJson)
              .sinkTo(alertSink)
              .name("Kafka Alert Sink");

        // ── 6. 실행 ──
        env.execute("Nexus Pay Fraud Detection Job v1.0");
    }
}
JAVAEOF
```

### 3-4. 알림 토픽 생성 및 탐지 검증

```bash
# 알림 토픽 생성
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --create --topic nexuspay.alerts.fraud \
  --partitions 3 \
  --replication-factor 3 \
  --config min.insync.replicas=2 \
  --config retention.ms=2592000000  # 30일 보관

# 빌드
cd flink-jobs
docker run --rm -v $(pwd):/app -w /app maven:3.9-eclipse-temurin-11 \
  mvn clean package -DskipTests

# FraudDetectionJob 제출
docker cp target/flink-jobs-1.0.0.jar lab-flink-jm:/opt/flink/usrlib/
docker exec lab-flink-jm /opt/flink/bin/flink run \
  -d -c com.nexuspay.flink.job.FraudDetectionJob \
  /opt/flink/usrlib/flink-jobs-1.0.0.jar

# 이상거래 패턴 이벤트 주입
python3 scripts/flink_event_generator.py --mode fraud --count 50

# 알림 확인 — Kafka 컨슈머
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic nexuspay.alerts.fraud \
  --from-beginning \
  --max-messages 10

# 기대 출력 예시:
# {"alert_id":"ALERT-1712500000-42","rule_id":"RULE-001","rule_description":"1분 내 5건 연속 거래",...}
# {"alert_id":"ALERT-1712500001-55","rule_id":"RULE-002","rule_description":"단건 500만원 초과 거래",...}

# Flink TaskManager 로그에서도 확인
docker logs lab-flink-tm --tail 30 | grep "FRAUD-ALERT"
```

### 3-5. Redis 알림 캐싱 — 실시간 대시보드용

```bash
cat > scripts/fraud_alert_redis_sink.py << 'PYEOF'
#!/usr/bin/env python3
"""
Kafka nexuspay.alerts.fraud 토픽을 소비하여 Redis에 캐싱.
실시간 대시보드에서 조회할 수 있도록 사용자별 최근 알림을 저장한다.

Redis 키 구조:
  fraud:alert:latest:{user_id}  — 사용자별 최신 알림 (Hash)
  fraud:alert:count:{user_id}   — 사용자별 누적 알림 수 (Counter)
  fraud:alerts:recent            — 최근 100건 알림 (Sorted Set, score=timestamp)
"""

import json
import redis
import time
from confluent_kafka import Consumer

KAFKA_SERVERS = "localhost:30092,localhost:30093,localhost:30094"
TOPIC = "nexuspay.alerts.fraud"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_PASSWORD = "redis"

def main():
    consumer = Consumer({
        "bootstrap.servers": KAFKA_SERVERS,
        "group.id": "fraud-redis-sink",
        "auto.offset.reset": "latest",
    })
    consumer.subscribe([TOPIC])

    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
    print(f"[Redis Sink] 시작 — {TOPIC} → Redis 캐싱")

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"  Consumer error: {msg.error()}")
            continue
        alert = json.loads(msg.value().decode("utf-8"))
        user_id = alert.get("user_id")

        # 1. 사용자별 최신 알림
        r.hset(f"fraud:alert:latest:{user_id}", mapping=alert)
        r.expire(f"fraud:alert:latest:{user_id}", 86400)  # 24시간 TTL

        # 2. 사용자별 알림 카운터
        r.incr(f"fraud:alert:count:{user_id}")

        # 3. 최근 100건 Sorted Set
        score = time.time()
        r.zadd("fraud:alerts:recent", {json.dumps(alert): score})
        r.zremrangebyrank("fraud:alerts:recent", 0, -101)  # 100건 초과 시 오래된 항목 제거

        print(f"  [{alert['rule_id']}] user={user_id} → Redis 캐싱 완료")

if __name__ == "__main__":
    main()
PYEOF

chmod +x scripts/fraud_alert_redis_sink.py
```

```bash
# Redis 싱크 실행 (백그라운드)
python3 scripts/fraud_alert_redis_sink.py &

# Redis에서 알림 조회
docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli ZRANGE fraud:alerts:recent 0 -1
docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli HGETALL fraud:alert:latest:42
docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli GET fraud:alert:count:42
```

**Day 3 완료 기준**: FraudDetectionJob 정상 실행, 3가지 규칙(RULE-001·002·003) 탐지 동작 확인, 알림이 `nexuspay.alerts.fraud` 토픽에 전달, Redis 캐싱 동작 확인.

---

## Day 4: Exactly-once + 체크포인트

### 4-0. Flink 볼륨 생성 가이드

Flink는 Day 4에서 Exactly-once와 장애 복구를 검증하므로, 체크포인트와 세이브포인트 저장 경로를 이 시점에 외부 경로로 분리하는 것이 적절하다.

먼저 호스트 디렉터리를 준비한다.

```bash
mkdir -p data/flink/checkpoints
mkdir -p data/flink/savepoints
```

`docker-compose.yml`의 Flink 서비스에는 아래 마운트를 추가한다.

```yaml
  flink-jobmanager:
    volumes:
      - ./flink-jobs:/opt/flink-jobs
      - ./data/flink/checkpoints:/opt/flink/checkpoints
      - ./data/flink/savepoints:/opt/flink/savepoints

  flink-taskmanager:
    volumes:
      - ./flink-jobs:/opt/flink-jobs
      - ./data/flink/checkpoints:/opt/flink/checkpoints
      - ./data/flink/savepoints:/opt/flink/savepoints
```

적용 시점:
- Day 4 Exactly-once 실습 직전
- 체크포인트 경로는 코드 또는 `flink-conf.yaml` 설정과 동일해야 함
- savepoint 경로를 분리해 두면 업그레이드·복구 리허설에 유리함

### 4-1. Exactly-once 개념 정리

```bash
cat >> docs/flink-concepts.md << 'EOF'

## Exactly-once 처리 — 금융 데이터의 핵심 요구사항

### 세 가지 처리 보장 수준

| 수준 | 의미 | 위험 |
|------|------|------|
| At-most-once | 유실 가능, 중복 없음 | 거래 누락 → 정산 오류 |
| At-least-once | 유실 없음, 중복 가능 | 거래 중복 → 이중 청구 |
| **Exactly-once** | **유실 없음, 중복 없음** | **금융 데이터 필수** |

### Flink의 Exactly-once 메커니즘

```
[Kafka Source] ─→ [Flink Operator (Stateful)] ─→ [Kafka Sink]
      │                    │                          │
      │         Checkpoint Barrier                    │
      │                    │                          │
      ▼                    ▼                          ▼
  오프셋 저장         상태 스냅샷              트랜잭션 커밋
      └────────────────────┴──────────────────────────┘
                           │
                    모두 원자적(atomic)으로
                    하나의 체크포인트에 묶임
```

1. **소스(Kafka Consumer)**: 체크포인트에 현재 오프셋 기록 → 장애 시 해당 오프셋부터 재소비
2. **연산자(Stateful Operator)**: 체크포인트에 내부 상태 스냅샷 → 장애 시 복원
3. **싱크(Kafka Producer)**: 2-Phase Commit 프로토콜 → 체크포인트 완료 시만 커밋

세 요소가 하나의 체크포인트에 원자적으로 묶이므로 end-to-end Exactly-once가 보장된다.

EOF
```

### 4-2. Exactly-once 체크포인트 설정

TransactionAggregationJob에 상세 체크포인트 설정을 추가한다.

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/util/FlinkConfigUtil.java << 'JAVAEOF'
package com.nexuspay.flink.util;

import org.apache.flink.streaming.api.CheckpointingMode;
import org.apache.flink.streaming.api.environment.CheckpointConfig;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

/**
 * Flink 실행 환경 공통 설정 유틸리티.
 * 모든 잡에서 동일한 Exactly-once 체크포인트 설정을 적용한다.
 */
public class FlinkConfigUtil {

    /**
     * Exactly-once 체크포인트 설정 적용.
     *
     * @param env Flink 실행 환경
     * @param checkpointIntervalMs 체크포인트 주기 (밀리초)
     */
    public static void configureExactlyOnce(StreamExecutionEnvironment env, long checkpointIntervalMs) {
        // 1. 체크포인트 모드: EXACTLY_ONCE
        env.enableCheckpointing(checkpointIntervalMs, CheckpointingMode.EXACTLY_ONCE);

        CheckpointConfig cpConfig = env.getCheckpointConfig();

        // 2. 체크포인트 타임아웃: 2분 (대규모 상태에서도 충분한 시간)
        cpConfig.setCheckpointTimeout(120_000);

        // 3. 최소 간격: 체크포인트 간 최소 30초 간격
        cpConfig.setMinPauseBetweenCheckpoints(30_000);

        // 4. 동시 체크포인트: 1개만 허용 (리소스 경합 방지)
        cpConfig.setMaxConcurrentCheckpoints(1);

        // 5. 잡 취소 시 체크포인트 보존 (디버깅·재시작용)
        cpConfig.setExternalizedCheckpointCleanup(
                CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);

        // 6. 연속 실패 허용: 3회까지 허용 후 잡 실패
        cpConfig.setTolerableCheckpointFailureNumber(3);

        // 7. Unaligned Checkpoint: 백프레셔 상황에서도 체크포인트 진행
        cpConfig.enableUnalignedCheckpoints();
    }

    /**
     * 재시작 전략 설정.
     * 장애 발생 시 최대 3회 재시작, 재시작 간 10초 대기.
     */
    public static void configureRestartStrategy(StreamExecutionEnvironment env) {
        env.setRestartStrategy(
                org.apache.flink.api.common.restartstrategy.RestartStrategies
                        .fixedDelayRestart(3, org.apache.flink.api.common.time.Time.seconds(10))
        );
    }
}
JAVAEOF
```

### 4-3. Kafka 트랜잭션 싱크 — End-to-End Exactly-once

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/util/ExactlyOnceKafkaSinkBuilder.java << 'JAVAEOF'
package com.nexuspay.flink.util;

import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.kafka.clients.producer.ProducerConfig;

import java.util.Properties;

/**
 * Exactly-once Kafka 싱크 빌더.
 *
 * Kafka 트랜잭션 프로듀서를 사용하여 체크포인트와 연동된 2-Phase Commit을 수행한다.
 * 체크포인트 완료 시에만 Kafka 트랜잭션을 커밋하므로 중복 메시지가 발생하지 않는다.
 */
public class ExactlyOnceKafkaSinkBuilder {

    public static KafkaSink<String> build(String brokers, String topic, String transactionalIdPrefix) {
        Properties kafkaProps = new Properties();
        // Exactly-once를 위한 Kafka 프로듀서 설정
        kafkaProps.setProperty(ProducerConfig.TRANSACTION_TIMEOUT_CONFIG, "900000");  // 15분
        kafkaProps.setProperty(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
        kafkaProps.setProperty(ProducerConfig.ACKS_CONFIG, "all");
        kafkaProps.setProperty(ProducerConfig.RETRIES_CONFIG, "3");

        return KafkaSink.<String>builder()
                .setBootstrapServers(brokers)
                .setRecordSerializer(KafkaRecordSerializationSchema.builder()
                        .setTopic(topic)
                        .setValueSerializationSchema(new SimpleStringSchema())
                        .build())
                .setDeliveryGuarantee(org.apache.flink.connector.base.DeliveryGuarantee.EXACTLY_ONCE)
                .setTransactionalIdPrefix(transactionalIdPrefix)
                .setKafkaProducerConfig(kafkaProps)
                .build();
    }
}
JAVAEOF
```

### 4-4. TransactionAggregationJob 최종 버전 — Exactly-once 적용

```bash
cat > flink-jobs/src/main/java/com/nexuspay/flink/job/TransactionAggregationJob.java << 'JAVAEOF'
package com.nexuspay.flink.job;

import com.nexuspay.flink.function.LateDataSideOutputFunction;
import com.nexuspay.flink.function.TransactionAggregateFunction;
import com.nexuspay.flink.function.TransactionWindowFunction;
import com.nexuspay.flink.model.AggregatedResult;
import com.nexuspay.flink.model.NexusPayEvent;
import com.nexuspay.flink.util.ExactlyOnceKafkaSinkBuilder;
import com.nexuspay.flink.util.FlinkConfigUtil;
import com.nexuspay.flink.util.NexusPayEventDeserializer;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.datastream.SingleOutputStreamOperator;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.windowing.assigners.TumblingEventTimeWindows;
import org.apache.flink.streaming.api.windowing.assigners.SlidingEventTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;

import java.time.Duration;

/**
 * Nexus Pay 거래 실시간 집계 잡 — v3.0 (Exactly-once 적용 최종판).
 *
 * End-to-End 보장:
 *   Kafka Source (오프셋 체크포인트)
 *   → Flink Stateful Operator (상태 체크포인트)
 *   → Kafka Sink (트랜잭션 2PC)
 */
public class TransactionAggregationJob {

    private static final String KAFKA_BROKERS = "kafka-1:9092,kafka-2:9092,kafka-3:9092";

    public static void main(String[] args) throws Exception {
        // ── 1. 환경 + Exactly-once 설정 ──
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        FlinkConfigUtil.configureExactlyOnce(env, 60_000);  // 60초 체크포인트
        FlinkConfigUtil.configureRestartStrategy(env);
        env.getConfig().setAutoWatermarkInterval(1000);

        // ── 2. Kafka 소스 ──
        KafkaSource<NexusPayEvent> kafkaSource = KafkaSource.<NexusPayEvent>builder()
                .setBootstrapServers(KAFKA_BROKERS)
                .setTopics("nexuspay.events.ingested")
                .setGroupId("flink-aggregation-v3")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new NexusPayEventDeserializer())
                .build();

        // ── 3. Watermark ──
        WatermarkStrategy<NexusPayEvent> wmStrategy = WatermarkStrategy
                .<NexusPayEvent>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                .withTimestampAssigner((event, ts) -> event.getEventTimeMillis())
                .withIdleness(Duration.ofMinutes(1));

        // ── 4. 소스 스트림 ──
        DataStream<NexusPayEvent> txStream = env
                .fromSource(kafkaSource, wmStrategy, "Nexus Pay Kafka Source")
                .filter(event -> event != null)
                .filter(event -> {
                    String type = event.getEventType();
                    return "PAYMENT".equals(type) || "TRANSFER".equals(type)
                            || "WITHDRAWAL".equals(type) || "SETTLEMENT".equals(type);
                })
                .name("Transaction Events");

        // ── 5. Tumbling Window 5분 집계 ──
        SingleOutputStreamOperator<AggregatedResult> tumblingResult = txStream
                .keyBy(NexusPayEvent::getEventType)
                .window(TumblingEventTimeWindows.of(Time.minutes(5)))
                .allowedLateness(Time.seconds(10))
                .sideOutputLateData(LateDataSideOutputFunction.LATE_DATA_TAG)
                .aggregate(new TransactionAggregateFunction(), new TransactionWindowFunction())
                .name("5min Tumbling Aggregation");

        // ── 6. Sliding Window 5분/1분 ──
        SingleOutputStreamOperator<AggregatedResult> slidingResult = txStream
                .keyBy(NexusPayEvent::getEventType)
                .window(SlidingEventTimeWindows.of(Time.minutes(5), Time.minutes(1)))
                .allowedLateness(Time.seconds(10))
                .sideOutputLateData(LateDataSideOutputFunction.LATE_DATA_TAG)
                .aggregate(new TransactionAggregateFunction(), new TransactionWindowFunction())
                .name("5min Sliding Aggregation");

        // ── 7. Exactly-once Kafka 싱크 ──
        KafkaSink<String> aggSink = ExactlyOnceKafkaSinkBuilder.build(
                KAFKA_BROKERS, "nexuspay.aggregation.5min", "flink-agg-tx");

        tumblingResult.map(AggregatedResult::toJson)
                      .sinkTo(aggSink)
                      .name("Tumbling → Kafka (Exactly-once)");

        KafkaSink<String> slidingSink = ExactlyOnceKafkaSinkBuilder.build(
                KAFKA_BROKERS, "nexuspay.aggregation.sliding", "flink-sliding-tx");

        slidingResult.map(AggregatedResult::toJson)
                     .sinkTo(slidingSink)
                     .name("Sliding → Kafka (Exactly-once)");

        // ── 8. Late Data → DLQ ──
        DataStream<NexusPayEvent> lateData = tumblingResult
                .getSideOutput(LateDataSideOutputFunction.LATE_DATA_TAG);

        KafkaSink<String> dlqSink = ExactlyOnceKafkaSinkBuilder.build(
                KAFKA_BROKERS, "nexuspay.events.dlq", "flink-dlq-tx");

        lateData.map(event -> event.toString())
                .sinkTo(dlqSink)
                .name("Late Data → DLQ (Exactly-once)");

        // ── 9. 디버깅 출력 ──
        tumblingResult.print("TUMBLING-5MIN");
        lateData.print("LATE-DATA");

        // ── 10. 실행 ──
        env.execute("Nexus Pay Transaction Aggregation Job v3.0 (Exactly-once)");
    }
}
JAVAEOF
```

### 4-5. 결과 토픽 생성

```bash
# 집계 결과 토픽
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --create --topic nexuspay.aggregation.5min \
  --partitions 3 \
  --replication-factor 3 \
  --config min.insync.replicas=2

docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --create --topic nexuspay.aggregation.sliding \
  --partitions 3 \
  --replication-factor 3 \
  --config min.insync.replicas=2

# Kafka 브로커 트랜잭션 타임아웃 설정 확인
# Flink 트랜잭션 타임아웃(15분)보다 Kafka의 transaction.max.timeout.ms가 커야 함
docker exec lab-kafka-1 /opt/kafka/bin/kafka-configs.sh \
  --bootstrap-server kafka-1:9092 \
  --entity-type brokers \
  --entity-default \
  --describe | grep transaction.max.timeout
# 기본값 900000ms (15분) — Flink 설정과 일치하면 OK
```

### 4-6. Exactly-once 검증 — 장애 주입 테스트

```bash
# 빌드 & 배포
cd flink-jobs
docker run --rm -v $(pwd):/app -w /app maven:3.9-eclipse-temurin-11 \
  mvn clean package -DskipTests
docker cp target/flink-jobs-1.0.0.jar lab-flink-jm:/opt/flink/usrlib/

# 기존 잡 모두 취소
for JOB_ID in $(curl -s http://localhost:8081/jobs | python3 -c "
import sys, json
for j in json.load(sys.stdin).get('jobs', []):
    if j['status'] == 'RUNNING': print(j['id'])
"); do
  curl -X PATCH "http://localhost:8081/jobs/$JOB_ID?mode=cancel"
  echo "취소: $JOB_ID"
done
sleep 5

# v3.0 잡 제출
docker exec lab-flink-jm /opt/flink/bin/flink run \
  -d /opt/flink/usrlib/flink-jobs-1.0.0.jar

# 잡 ID 확인
JOB_ID=$(curl -s http://localhost:8081/jobs | python3 -c "
import sys, json
for j in json.load(sys.stdin)['jobs']:
    if j['status'] == 'RUNNING': print(j['id']); break
")
echo "실행 중인 잡: $JOB_ID"

# ── 검증 시나리오 A: 정상 흐름 확인 ──
python3 scripts/flink_event_generator.py --mode normal --count 100

# 집계 토픽 확인
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic nexuspay.aggregation.5min \
  --from-beginning --max-messages 5

# ── 검증 시나리오 B: TaskManager 장애 중 데이터 정합성 ──
echo "=== 장애 주입: TaskManager 강제 중단 ==="

# 이벤트 주입 시작 (백그라운드)
python3 scripts/flink_event_generator.py --mode normal --count 200 &
GENERATOR_PID=$!

# 3초 후 TaskManager 중단
sleep 3
docker stop lab-flink-tm
echo "TaskManager 중단됨"

# 10초 대기 후 재기동
sleep 10
docker start lab-flink-tm
echo "TaskManager 재기동"

# 이벤트 생성기 완료 대기
wait $GENERATOR_PID

# 체크포인트 복구 확인
sleep 30
curl -s "http://localhost:8081/jobs/$JOB_ID/checkpoints" | python3 -m json.tool
# 기대: restored_latest_checkpoint != null

# ── 검증 시나리오 C: 메시지 중복·유실 검사 ──
# 소스 토픽의 오프셋과 싱크 토픽의 메시지 수를 비교
echo "=== 소스 vs 싱크 메시지 수 비교 ==="

docker exec lab-kafka-1 /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server kafka-1:9092 \
  --group flink-aggregation-v3 \
  --describe
# LAG가 0에 수렴해야 함
```

### 4-7. 체크포인트 모니터링 스크립트

```bash
cat > scripts/monitor_checkpoints.sh << 'SHEOF'
#!/bin/bash
# Flink 체크포인트 상태 모니터링

FLINK_URL="http://localhost:8081"

echo "=== Flink 잡 & 체크포인트 모니터링 ==="
echo ""

# 실행 중인 잡 목록
JOBS=$(curl -s $FLINK_URL/jobs | python3 -c "
import sys, json
data = json.load(sys.stdin)
for j in data.get('jobs', []):
    print(f\"{j['id']} [{j['status']}]\")
")
echo "실행 중인 잡:"
echo "$JOBS"
echo ""

# 각 잡의 체크포인트 상태
for JOB_ID in $(curl -s $FLINK_URL/jobs | python3 -c "
import sys, json
for j in json.load(sys.stdin).get('jobs', []):
    if j['status'] == 'RUNNING': print(j['id'])
"); do
    echo "--- 잡: $JOB_ID ---"
    curl -s "$FLINK_URL/jobs/$JOB_ID/checkpoints" | python3 -c "
import sys, json
data = json.load(sys.stdin)
counts = data.get('counts', {})
print(f\"  완료: {counts.get('completed', 0)}건\")
print(f\"  실패: {counts.get('failed', 0)}건\")
print(f\"  진행중: {counts.get('in_progress', 0)}건\")

latest = data.get('latest', {}).get('completed', {})
if latest:
    print(f\"  최근 체크포인트 ID: {latest.get('id')}\")
    print(f\"  소요 시간: {latest.get('duration', 0)}ms\")
    print(f\"  상태 크기: {latest.get('state_size', 0)} bytes\")

restored = data.get('latest', {}).get('restored', {})
if restored:
    print(f\"  복구된 체크포인트: {restored.get('id')} (장애 복구)\")
"
    echo ""
done
SHEOF

chmod +x scripts/monitor_checkpoints.sh
```

**Day 4 완료 기준**: Exactly-once 체크포인트 설정 완료, Kafka 트랜잭션 싱크 동작 확인, TaskManager 장애 주입 후 체크포인트 복구 확인, 메시지 중복·유실 없음 검증.

---

## Day 5: 통합 테스트 + 운영 가이드 문서화

### 5-1. 전체 파이프라인 통합 검증

```bash
cat > scripts/verify_flink_pipeline.sh << 'SHEOF'
#!/bin/bash
# Week 4 Flink 파이프라인 통합 검증 스크립트

PASS=0
FAIL=0

check() {
    if [ $1 -eq 0 ]; then
        echo "  ✅ $2"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $2"
        FAIL=$((FAIL + 1))
    fi
}

echo "=========================================="
echo " Week 4: Flink 파이프라인 통합 검증"
echo "=========================================="
echo ""

# 1. Flink 클러스터 상태
echo "[1] Flink 클러스터 상태"
FLINK_STATUS=$(curl -sf http://localhost:8081/overview 2>/dev/null)
echo "$FLINK_STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('taskmanagers',0)>0 else 1)" 2>/dev/null
check $? "Flink TaskManager 활성"

SLOTS=$(echo "$FLINK_STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('slots-available',0))" 2>/dev/null)
echo "     사용 가능 슬롯: $SLOTS"

# 2. Flink 잡 실행 상태
echo ""
echo "[2] Flink 잡 상태"
RUNNING_JOBS=$(curl -sf http://localhost:8081/jobs 2>/dev/null | python3 -c "
import sys,json
jobs = [j for j in json.load(sys.stdin).get('jobs',[]) if j['status']=='RUNNING']
print(len(jobs))
" 2>/dev/null)
[ "$RUNNING_JOBS" -ge 1 ] 2>/dev/null
check $? "실행 중인 잡 존재 ($RUNNING_JOBS건)"

# 3. 소스 토픽 데이터 존재
echo ""
echo "[3] Kafka 토픽 검증"
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 --list 2>/dev/null | grep -q "nexuspay.events.ingested"
check $? "소스 토픽 nexuspay.events.ingested 존재"

docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 --list 2>/dev/null | grep -q "nexuspay.aggregation.5min"
check $? "집계 토픽 nexuspay.aggregation.5min 존재"

docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 --list 2>/dev/null | grep -q "nexuspay.alerts.fraud"
check $? "알림 토픽 nexuspay.alerts.fraud 존재"

# 4. 이벤트 주입 및 결과 확인
echo ""
echo "[4] 이벤트 주입 테스트"
python3 scripts/flink_event_generator.py --mode fraud --count 30 2>/dev/null
check $? "이벤트 생성기 실행 성공"

sleep 10

# 알림 토픽에 메시지 도착 확인
ALERT_COUNT=$(docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic nexuspay.alerts.fraud \
  --from-beginning --timeout-ms 5000 2>/dev/null | wc -l)
[ "$ALERT_COUNT" -ge 1 ] 2>/dev/null
check $? "이상거래 알림 생성 확인 ($ALERT_COUNT건)"

# 5. 체크포인트 상태
echo ""
echo "[5] 체크포인트 상태"
for JOB_ID in $(curl -sf http://localhost:8081/jobs 2>/dev/null | python3 -c "
import sys,json
for j in json.load(sys.stdin).get('jobs',[]):
    if j['status']=='RUNNING': print(j['id'])
" 2>/dev/null); do
    CP_COMPLETED=$(curl -sf "http://localhost:8081/jobs/$JOB_ID/checkpoints" 2>/dev/null | \
      python3 -c "import sys,json; print(json.load(sys.stdin).get('counts',{}).get('completed',0))" 2>/dev/null)
    [ "$CP_COMPLETED" -ge 1 ] 2>/dev/null
    check $? "잡 $JOB_ID 체크포인트 완료 ($CP_COMPLETED건)"
done

# 6. Redis 알림 캐시
echo ""
echo "[6] Redis 캐시 상태"
REDIS_KEYS=$(docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli KEYS "fraud:*" 2>/dev/null | wc -l)
[ "$REDIS_KEYS" -ge 1 ] 2>/dev/null
check $? "Redis 알림 캐시 존재 ($REDIS_KEYS 키)"

echo ""
echo "=========================================="
echo " 결과: ✅ $PASS건 통과 / ❌ $FAIL건 실패"
echo "=========================================="
SHEOF

chmod +x scripts/verify_flink_pipeline.sh
bash scripts/verify_flink_pipeline.sh
```

### 5-2. Flink 운영 가이드 작성

```bash
cat > docs/flink-operations-guide.md << 'EOF'
# Nexus Pay Flink 운영 가이드

## 1. 잡 관리

### 잡 제출
```bash
docker exec lab-flink-jm /opt/flink/bin/flink run \
  -d -c <MainClass> /opt/flink/usrlib/flink-jobs-1.0.0.jar
```

### 잡 목록 확인
```bash
curl -s http://localhost:8081/jobs | python3 -m json.tool
```

### 잡 취소 (체크포인트 보존)
```bash
curl -X PATCH "http://localhost:8081/jobs/<JOB_ID>?mode=cancel"
```

### Savepoint 생성 (업그레이드 전)
```bash
docker exec lab-flink-jm /opt/flink/bin/flink savepoint <JOB_ID> /opt/flink/savepoints
```

### Savepoint에서 재시작
```bash
docker exec lab-flink-jm /opt/flink/bin/flink run \
  -d -s /opt/flink/savepoints/<SAVEPOINT_DIR> \
  /opt/flink/usrlib/flink-jobs-1.0.0.jar
```

## 2. 모니터링 항목

| 지표 | 임계값 | 확인 방법 |
|------|--------|----------|
| 체크포인트 소요 시간 | < 30초 | Dashboard → Checkpoints |
| 체크포인트 실패율 | 0% | `monitor_checkpoints.sh` |
| 백프레셔 | 0~LOW | Dashboard → Task → Back Pressure |
| 컨슈머 LAG | < 1000 | `kafka-consumer-groups.sh --describe` |
| TaskManager 가용 슬롯 | > 0 | Dashboard → Overview |
| 상태 크기 | < 1GB/잡 | Dashboard → Checkpoints → State Size |

## 3. 장애 대응

### TaskManager 장애
1. Flink 자동 재시작 전략에 의해 최대 3회 재시도
2. 마지막 성공 체크포인트에서 자동 복구
3. 3회 초과 실패 시 잡 FAILED → 수동 개입 필요

### 체크포인트 연속 실패
1. 상태 크기 확인 → 비정상 증가 시 상태 TTL 점검
2. 백프레셔 확인 → 병렬도 조정 또는 리소스 증설
3. Kafka 브로커 상태 확인 → 트랜잭션 타임아웃 점검

### Kafka 브로커 장애
1. Flink Kafka Source는 자동 재연결 시도
2. ISR < min.insync.replicas 시 싱크 쓰기 실패 → 체크포인트 실패
3. 브로커 복구 후 잡 자동 재시작

## 4. 성능 튜닝 가이드

| 파라미터 | 현재값 | 튜닝 방향 |
|----------|--------|----------|
| parallelism.default | 2 | Kafka 파티션 수에 맞춤 (최대 6) |
| checkpointing.interval | 60초 | 상태 크기에 따라 조정 (30~120초) |
| taskmanager.numberOfTaskSlots | 4 | 코어 수와 일치 |
| watermark.interval | 1초 | 지연 허용 범위에 따라 조정 |
| state.backend | hashmap | 상태 > 1GB 시 rocksdb 전환 |

## 5. 배포 토픽 맵

| 토픽 | 용도 | RF | 파티션 |
|------|------|-----|--------|
| nexuspay.events.ingested | NiFi 수집 데이터 (소스) | 3 | 6 |
| nexuspay.aggregation.5min | Tumbling 5분 집계 결과 | 3 | 3 |
| nexuspay.aggregation.sliding | Sliding 이동 평균 결과 | 3 | 3 |
| nexuspay.alerts.fraud | 이상거래 알림 | 3 | 3 |
| nexuspay.events.dlq | 지연·불량 데이터 | 3 | 2 |

EOF
```

### 5-3. 아키텍처 문서 — NiFi → Kafka → Flink 실시간 파이프라인

```bash
cat > docs/flink-architecture.md << 'EOF'
# Nexus Pay 실시간 파이프라인 아키텍처 — Week 4 완성

## 전체 흐름

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Nexus Pay 실시간 데이터 파이프라인                          │
│                                                                          │
│  [수집 계층 — Week 3]                                                     │
│  ┌─────────┐                                                             │
│  │ NiFi    │ API·CSV·DB → 스키마 표준화 → PublishKafka                    │
│  └────┬────┘                                                             │
│       ▼                                                                  │
│  [버퍼 계층 — Week 2]                                                     │
│  ┌────────────────────────────────┐                                      │
│  │ Kafka (nexuspay.events.ingested) │  6 파티션, RF=3, min.ISR=2           │
│  └────────────┬───────────────────┘                                      │
│               │                                                          │
│       ┌───────┴───────┐                                                  │
│       ▼               ▼                                                  │
│  [변환 계층 — Week 4]                                                     │
│  ┌────────────────┐  ┌───────────────────┐                               │
│  │ Aggregation Job │  │ Fraud Detection   │                               │
│  │ ─────────────── │  │ Job               │                               │
│  │ Tumbling 5min   │  │ ───────────────── │                               │
│  │ Sliding 5min/1m │  │ RULE-001: 빈도    │                               │
│  │ Session 2min    │  │ RULE-002: 고액    │                               │
│  │                 │  │ RULE-003: 합계    │                               │
│  └───────┬─────┬──┘  └──────┬────────────┘                               │
│          │     │             │                                            │
│          ▼     ▼             ▼                                            │
│  ┌──────────┐ ┌──────┐ ┌──────────────┐  ┌──────┐                        │
│  │ 집계 토픽 │ │ DLQ  │ │ 알림 토픽      │  │ Redis │                       │
│  │ .5min    │ │ .dlq │ │ .alerts.fraud │  │ 캐시  │                        │
│  │ .sliding │ │      │ │              │  │      │                          │
│  └──────────┘ └──────┘ └──────────────┘  └──────┘                        │
│                                                                          │
│  [보장 수준]  End-to-End Exactly-once (체크포인트 + 트랜잭션)              │
└──────────────────────────────────────────────────────────────────────────┘
```

## Exactly-once 보장 체인

| 구간 | 메커니즘 | 설정 |
|------|----------|------|
| NiFi → Kafka | PublishKafka 트랜잭션 (Week 3) | Use Transactions=true |
| Kafka → Flink | 체크포인트에 오프셋 포함 | CheckpointingMode.EXACTLY_ONCE |
| Flink 내부 | 분산 스냅샷 (Chandy-Lamport) | 60초 주기 체크포인트 |
| Flink → Kafka | 2-Phase Commit | DeliveryGuarantee.EXACTLY_ONCE |

## 잡별 리소스

| 잡 | 슬롯 | 병렬도 | 체크포인트 주기 | 상태 백엔드 |
|-----|------|--------|---------------|-----------|
| TransactionAggregationJob | 2 | 2 | 60초 | HashMap |
| FraudDetectionJob | 2 | 2 | 30초 | HashMap |
| SessionWindowAnalysisJob | 1 | 1 | 60초 | HashMap |

EOF
```

### 5-4. Git 커밋

```bash
git add .
git commit -m "Week 4: Flink 실시간 파이프라인 — 윈도우 집계 + 이상거래 탐지 + Exactly-once"
```

**Day 5 완료 기준**: 통합 검증 스크립트 전체 통과, 운영 가이드 작성, 아키텍처 문서 작성, Git 커밋.

---

## Week 4 산출물 체크리스트

| # | 산출물 | 완료 |
|---|--------|------|
| 1 | docs/flink-concepts.md (Flink 핵심 개념 정리) | ☐ |
| 2 | flink-jobs/pom.xml (Maven 프로젝트 설정) | ☐ |
| 3 | NexusPayEvent.java (표준 이벤트 POJO) | ☐ |
| 4 | AggregatedResult.java (집계 결과 모델) | ☐ |
| 5 | FraudAlert.java (이상거래 알림 모델) | ☐ |
| 6 | NexusPayEventDeserializer.java (Kafka JSON 역직렬화기) | ☐ |
| 7 | TransactionAggregateFunction.java (증분 집계 함수) | ☐ |
| 8 | TransactionWindowFunction.java (윈도우 메타데이터 바인딩) | ☐ |
| 9 | LateDataSideOutputFunction.java (지연 데이터 처리) | ☐ |
| 10 | FraudDetectionFunction.java (상태 기반 이상거래 탐지) | ☐ |
| 11 | TransactionAggregationJob.java v3.0 (윈도우 집계 + Exactly-once) | ☐ |
| 12 | FraudDetectionJob.java (이상거래 탐지 잡) | ☐ |
| 13 | SessionWindowAnalysisJob.java (세션 윈도우 분석) | ☐ |
| 14 | FlinkConfigUtil.java (Exactly-once 설정 유틸) | ☐ |
| 15 | ExactlyOnceKafkaSinkBuilder.java (트랜잭션 싱크 빌더) | ☐ |
| 16 | scripts/flink_event_generator.py (테스트 이벤트 생성기) | ☐ |
| 17 | scripts/fraud_alert_redis_sink.py (Redis 알림 캐싱) | ☐ |
| 18 | scripts/verify_flink_pipeline.sh (통합 검증 스크립트) | ☐ |
| 19 | scripts/monitor_checkpoints.sh (체크포인트 모니터링) | ☐ |
| 20 | docs/flink-operations-guide.md (Flink 운영 가이드) | ☐ |
| 21 | docs/flink-architecture.md (파이프라인 아키텍처 문서) | ☐ |
| 22 | Git 커밋 | ☐ |

## 핵심 개념 요약

| 개념 | 요약 | 실습에서 확인한 것 |
|------|------|------------------|
| Event Time | 이벤트 발생 시점 기반 처리 (Processing Time 대비 정확) | ISO 8601 → epochMillis 변환, 금융 거래 정확한 일자 집계 |
| Watermark | "이 시점까지 데이터 도착 완료" 신호 | BoundedOutOfOrderness(5초), withIdleness(1분) |
| Late Data | Watermark 이후 도착 데이터 | allowedLateness(10초) + Side Output → DLQ |
| Tumbling Window | 겹치지 않는 고정 구간 집계 | 5분 단위 거래 유형별 건수·금액 집계 |
| Sliding Window | 겹치는 구간 (이동 평균) | 5분 윈도우 / 1분 슬라이드 |
| Session Window | 활동 기반 동적 구간 | 2분 비활동 간격으로 사용자 세션 분리 |
| Keyed State | 키별 독립 상태 관리 | userId별 최근 거래 리스트 (이상거래 탐지) |
| Checkpoint | 분산 스냅샷 (장애 복구 기반) | 60초 주기, EXACTLY_ONCE 모드 |
| Exactly-once | 유실·중복 없는 처리 보장 | Kafka 트랜잭션 싱크 2PC + 체크포인트 |
| CEP/Process Function | 복잡 이벤트 패턴 탐지 | 3가지 이상거래 규칙 (빈도·고액·합계) |

## Week 5 예고

Week 5에서는 Spark를 활용한 배치 ETL 파이프라인을 구축한다. Flink가 실시간 처리를 담당하는 동안, Spark는 일별·월별 대용량 배치 집계, 데이터 품질 정제, Delta Lake 기반 ACID 트랜잭션 저장소 구축을 담당한다. 실시간(Flink)과 배치(Spark)를 결합한 Lambda 아키텍처의 배치 레이어가 완성된다.

