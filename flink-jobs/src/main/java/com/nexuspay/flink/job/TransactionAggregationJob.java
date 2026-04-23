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
import org.apache.flink.streaming.api.windowing.assigners.SlidingEventTimeWindows;
import org.apache.flink.streaming.api.windowing.assigners.TumblingEventTimeWindows;

import java.time.Duration;
import java.util.Objects;

/**
 * Nexus Pay 거래 실시간 집계 잡 — v3.0 (Exactly-once 적용 최종판).
 * <p>
 * 파이프라인:
 * Kafka(nexuspay.events.ingested)
 * → Watermark 할당
 * → 거래 이벤트 필터링 (PAYMENT, TRANSFER, WITHDRAWAL)
 * → 윈도우 집계 (5분 Tumbling)
 * → keyBy(eventType)
 * ├── [Tumbling 5분] 거래 유형별 5분 단위 집계
 * ├── [Sliding 5분/1분] 1분마다 갱신되는 5분 이동 평균
 * └── [Late Data] Side Output → DLQ
 * → 결과 싱크 (Kafka + Redis)
 * End-to-End 보장:
 * Kafka Source (오프셋 체크포인트)
 * → Flink Stateful Operator (상태 체크포인트)
 * → Kafka Sink (트랜잭션 2PC)
 */
public class TransactionAggregationJob {

    private static final String KAFKA_BROKERS = "kafka-1:9092,kafka-2:9092,kafka-3:9092";

    public static void main(String[] args) throws Exception {
        // 1. 실행 환경 구성
        final StreamExecutionEnvironment env = StreamExecutionEnvironment
                .getExecutionEnvironment();
        // 체크포인트 활성화 (Exactly-once 기반 - Day 4에서 상세 설정
        FlinkConfigUtil.configureExactlyOnce(env, 60_000);
        FlinkConfigUtil.configureRestartStrategy(env);
        env.getConfig().setAutoWatermarkInterval(1000L); //watermark 1초 주기 갱신

        // 2. Kafka 소스 구성
        KafkaSource<NexusPayEvent> kafkaSource = KafkaSource.<NexusPayEvent>builder()
                .setBootstrapServers(KAFKA_BROKERS)
                .setTopics("nexuspay.events.ingested")
                .setGroupId("flink-aggregation-v3")
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

        // 4. 소스 스트림
        DataStream<NexusPayEvent> transactionDataStream = env
                .fromSource(kafkaSource, watermarkStrategy, "Nexus Pay Kafka Source")
                .filter(Objects::nonNull)
                .filter(event -> {
                    String type = event.getEventType();
                    return "PAYMENT".equals(type) || "TRANSFER".equals(type)
                            || "WITHDRAWAL".equals(type) || "SETTLEMENT".equals(type);
                })
                .name("Transaction Events");

        // 5. Tumbling window aggregation - 5분단위 집계
        SingleOutputStreamOperator<AggregatedResult> tumblingResult = transactionDataStream
                .keyBy(NexusPayEvent::getEventType)
                .window(TumblingEventTimeWindows.of(Duration.ofMinutes(5)))
                .allowedLateness(Duration.ofSeconds(10)) //10초 추가 지연 허용
                .sideOutputLateData(LateDataSideOutputFunction.LATE_DATA_TAG) // 그 이후 Side Output
                .aggregate(
                        new TransactionAggregateFunction(),
                        new TransactionWindowFunction()
                )
                .name("5min Tumbling Window Aggregation");


        // 6. Sliding Window — 5분 윈도우, 1분 슬라이드 (이동 평균)
        SingleOutputStreamOperator<AggregatedResult> slidingResult = transactionDataStream
                .keyBy(NexusPayEvent::getEventType)
                .window(SlidingEventTimeWindows.of(Duration.ofMinutes(5), Duration.ofMinutes(1)))
                .allowedLateness(Duration.ofSeconds(10))
                .sideOutputLateData(LateDataSideOutputFunction.SLIDING_LATE_DATA_TAG)
                .aggregate(
                        new TransactionAggregateFunction(),
                        new TransactionWindowFunction()
                )
                .name("5min Sliding Window Aggregation");

        // 7. Exactly-once Kafka 싱크
        KafkaSink<String> aggSink = ExactlyOnceKafkaSinkBuilder.build(KAFKA_BROKERS,
                "nexuspay.aggregation.5min",
                "flink-agg-tumbling-tx");

        tumblingResult.map(AggregatedResult::toJson)
                .sinkTo(aggSink)
                .name("Tumbling -> Kafka (Exactly-once");

        KafkaSink<String> slidingSink = ExactlyOnceKafkaSinkBuilder.build(
                KAFKA_BROKERS, "nexuspay.aggregation.sliding", "flink-agg-sliding-tx"
        );

        slidingResult.map(AggregatedResult::toJson)
                .sinkTo(slidingSink)
                .name("Sliding -> Kafka (Exactly-once");

        // 8. Late Data → DLQ
        // Tumbling·Sliding 두 경로의 Side Output을 union하여 DLQ 싱크로 한꺼번에 내보낸다.
        DataStream<NexusPayEvent> tumblingLate = tumblingResult
                .getSideOutput(LateDataSideOutputFunction.LATE_DATA_TAG);
        DataStream<NexusPayEvent> slidingLate = slidingResult
                .getSideOutput(LateDataSideOutputFunction.SLIDING_LATE_DATA_TAG);

        DataStream<NexusPayEvent> lateData = tumblingLate.union(slidingLate);

        KafkaSink<String> dlqSink = ExactlyOnceKafkaSinkBuilder.build(
                KAFKA_BROKERS, "nexuspay.events.dlq", "flink-dlq-tx"
        );

        lateData.map(NexusPayEvent::toString)
                .sinkTo(dlqSink)
                .name("DLQ -> Kafka (Exactly-once");

        // 9 디버깅 출력
        tumblingResult.print("TUMBLING-5MIN");

        // 10. 잡 실행
        env.execute("Nexus Pay Transaction Aggregation Job v3.0 (Exactly-once)");

    }
}
