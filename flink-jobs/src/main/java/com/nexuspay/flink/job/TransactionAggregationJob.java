package com.nexuspay.flink.job;


import com.nexuspay.flink.util.NexusPayEventDeserializer;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

import com.nexuspay.flink.model.NexusPayEvent;

import java.time.Duration;
import java.util.Objects;

/**
 * Nexus Pay 거래 실시간 집계 잡.
 * <p>
 * 파이프라인:
 * Kafka(nexuspay.events.ingested)
 * → Watermark 할당
 * → 거래 이벤트 필터링 (PAYMENT, TRANSFER, WITHDRAWAL)
 * → 윈도우 집계 (5분 Tumbling)
 * → 결과 싱크 (Kafka + Redis)
 */
public class TransactionAggregationJob {

    public static void main(String[] args) throws Exception {
        // 1. 실행 환경 구성
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // 체크포인트 활성화 (Exactly-once 기반 - Day 4에서 상세 설정
        env.enableCheckpointing(60_000); // 60초 주기

        // 2. Kafka 소스 구성
        KafkaSource<NexusPayEvent> kafkaSource = KafkaSource.<NexusPayEvent>builder()
                .setBootstrapServers("kafka-1:9092,kafka-2:9092,kafka-3:9092")
                .setTopics("nexuspay.events.ingested")
                .setGroupId("flink-aggregation")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new NexusPayEventDeserializer())
                .build();

        // 3. Watermark 전략
        WatermarkStrategy<NexusPayEvent> watermarkStrategy = WatermarkStrategy
                // 이벤트가 순서대로 오지 않아도 최대 5초 지연(역순 도착)까지 허용
                .<NexusPayEvent>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                // 실제 이벤트 발생 시각(eventTimeMillis)을 이벤트 타임으로 사용
                .withTimestampAssigner((event, timestamp) -> event.getEventTimeMillis())
                // 특정 소스 파티션에서 1분간 데이터가 없으면 idle로 간주하여
                // 전체 워터마크 진행이 멈추지 않도록 함
                .withIdleness(Duration.ofMinutes(1));

        // 4. 데이터 스트림 생성
        DataStream<NexusPayEvent> eventDataStream = env.fromSource(kafkaSource, watermarkStrategy,
                        "Nexus Pay Kafka Source")
                .filter(Objects::nonNull)
                .name("Filter Null Events");

        // 5. 커래 이벤트만 필터링 (CUSTOMER_UPDATE 제외)
        DataStream<NexusPayEvent> transactionDataStream = eventDataStream.filter(event -> {
                    String type = event.getEventType();
                    return "PAYMENT".equals(type) || "TRANSFER".equals(type)
                            || "WITHDRAWAL".equals(type) || "SETTLEMENT".equals(type);
                })
                .name("Filter Transaction Events");

        // Day 2에서 윈도우 집계 추가
        // Day 3에서 이상거래 탐지 분기 추가
        // Day 4에서 Exactly-once 싱크 추가

        // 6. 디버깅용 콘솔 출력(Day 1 검증용)
        transactionDataStream.print("TX-EVENT");

        // 7. 잡 실행
        env.execute("Nexus Pay Transaction Aggregation Job v1.0");

    }
}
