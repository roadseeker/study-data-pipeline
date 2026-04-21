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
 * <p>
 * 파이프라인:
 *   Kafka(nexuspay.events.ingested)
 *     → Watermark 할당
 *     → keyBy(userId)
 *     → FraudDetectionFunction (상태 기반 규칙 평가)
 *     → 알림 싱크: Kafka(nexuspay.alerts.fraud) + 콘솔
 * <p>
 * 탐지 규칙:
 *   RULE-001: 1분 내 3건 이상 연속 거래 (HIGH)
 *   RULE-002: 단건 500만원 초과 (HIGH)
 *   RULE-003: 1분 내 합계 1,000만원 초과 (MEDIUM)
 */
public class FraudDetectionJob {
    public static void main(String[] args) throws Exception {

        // ── 1. 환경 구성 ──
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.enableCheckpointing(30_000); // 30초 주기 (이상거래는 빠른 복구 필요)

        // ── 2. Kafka 소스 ──
        KafkaSource<NexusPayEvent> kafkaSource = KafkaSource.<NexusPayEvent>builder()
                .setBootstrapServers("kafka-1:9092,kafka-2:9092,kafka-3:9092")
                .setTopics("nexuspay.events.ingested")
                .setGroupId("flink-fraud-detection")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new NexusPayEventDeserializer())
                .build();

        // 이베트 타임/워터마크 전략
        WatermarkStrategy<NexusPayEvent> watermarkStrategy = WatermarkStrategy
                .<NexusPayEvent>forBoundedOutOfOrderness(Duration.ofSeconds(5)) // 최대 5초 out-of-order 허용
                .withTimestampAssigner((event, timestamp) -> event.getEventTimeMillis()) // 이벤트 타임을 NexusPayEvent.getEventTimeMills() 사용
                .withIdleness(Duration.ofMinutes(1)); // 1분 무입력 파티션은 idle 처리

        // 입력 정제
        DataStream<NexusPayEvent> eventStream = env
                .fromSource(kafkaSource, watermarkStrategy, "Nexus Pay Kafka Source")
                // null 이벤트 또는 userId 가 없는 이베트 제거
                .filter(event -> event != null && event.getUserId() != null)
                .name("Filter Valid Events");


        // ── 3. 이상거래 탐지 ──
        DataStream<FraudAlert> alerts = eventStream
                // 사용자 단위 상태/타이머 기반 룰 평가
                .keyBy(NexusPayEvent::getUserId)
                .process(new FraudDetectionFunction())
                .name("Fraud Detection Function");

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

        // 운영용 Kafka 출력 Json 문자열 변환 후 KafkaSink로 전송
        alerts.map(FraudAlert::toJson)
                .sinkTo(alertSink)
                .name("Kafka Alert Sink");

        // ── 6. 실행 ──
        env.execute("Nexus Pay Fraud Detection Job v1.0");
    }
}