package com.nexuspay.flink.job;

import com.nexuspay.flink.model.NexusPayEvent;
import com.nexuspay.flink.util.NexusPayEventDeserializer;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.AggregateFunction;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.functions.windowing.ProcessWindowFunction;
import org.apache.flink.streaming.api.windowing.assigners.EventTimeSessionWindows;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;
import org.apache.flink.util.Collector;

import java.io.Serial;
import java.time.Duration;
import java.time.Instant;
import java.time.format.DateTimeFormatter;
import java.util.Objects;

/**
 * Session Window 분석 잡.
 * <p>
 * 사용자별 거래 이벤트를 활동 세션으로 묶고,
 * 2분 이상 비활동이 발생하면 세션을 종료하여 건수와 총액을 집계한다.
 * <p>
 * 학습 포인트:
 * 1. 고정 길이 윈도우 대신 활동 기반 동적 윈도우를 사용한다.
 * 2. AggregateFunction + ProcessWindowFunction 조합으로 누적값과 윈도우 메타데이터를 함께 만든다.
 * 3. Day 3 이상 세션 탐지에 사용할 기초 지표를 만든다.
 */
public class SessionWindowAnalysisJob {

    private static final Duration SESSION_GAP = Duration.ofMinutes(2);
    private static final DateTimeFormatter ISO_FMT = DateTimeFormatter.ISO_INSTANT;

    /**
     * 세션 단위 집계에 사용하는 누적기 객체이다.
     * <p>
     * 이벤트 수와 총 거래 금액을 저장하며,
     * Flink 집계 연산의 중간 상태로 활용된다.
     */
    public static class SessionAccumulator implements java.io.Serializable {
        @Serial
        private static final long serialVersionUID = 1L;
        /** 세션 내 이벤트 또는 거래 건수 */
        public long count = 0L;
        /** 세션 내 총 거래 금액 */
        public double totalAmount = 0.0;
    }

    /**
     * Nexus Pay 이벤트 스트림을 세션 단위로 집계하기 위한 AggregateFunction 구현체이다.
     * <p>
     * 이 클래스는 {@link NexusPayEvent}를 입력으로 받아 {@link SessionAccumulator}에
     * 이벤트 건수와 거래 금액 합계 같은 중간 집계 상태를 누적한다.
     * 집계가 완료되면 동일한 {@link SessionAccumulator} 형태로 결과를 반환한다.
     * <p>
     * 주로 Flink의 세션 윈도우와 함께 사용되며, 동일 키 내에서 일정 시간 동안
     * 연속적으로 발생한 이벤트들을 하나의 세션으로 간주하여 집계할 때 활용된다.
     */
    public static class SessionAggregateFunction
            implements AggregateFunction<NexusPayEvent, SessionAccumulator, SessionAccumulator> {

        /**
         * 세션 집계를 시작할 때 사용할 초기 누적기 객체를 생성한다.
         *
         * @return 이벤트 건수와 총 거래 금액이 0으로 초기화된 누적기
         */
        @Override
        public SessionAccumulator createAccumulator() {
            return new SessionAccumulator();
        }

        /**
         * 입력 이벤트 1건을 기존 누적기에 반영한다.
         * <p>
         * 일반적으로 이벤트 건수를 1 증가시키고,
         * 이벤트 금액을 총 거래 금액에 더하는 방식으로 집계를 수행한다.
         *
         * @param value 집계에 반영할 Nexus Pay 이벤트
         * @param accumulator 현재까지의 세션 집계 상태
         * @return 입력 이벤트가 반영된 누적기
         */
        @Override
        public SessionAccumulator add(NexusPayEvent value, SessionAccumulator accumulator) {
            accumulator.count++;
            double amount = value.getAmount() != null ? value.getAmount() : 0.0;

            accumulator.totalAmount += amount;
            return accumulator;
        }

        /**
         * 현재 누적기 상태를 최종 집계 결과로 반환한다.
         *
         * @param accumulator 세션 집계가 누적된 상태 객체
         * @return 최종 집계 결과
         */
        @Override
        public SessionAccumulator getResult(SessionAccumulator accumulator) {
            return accumulator;
        }

        @Override
        public SessionAccumulator merge(SessionAccumulator a, SessionAccumulator b) {
            a.count += b.count;
            a.totalAmount += b.totalAmount;
            return a;
        }
    }

    /**
     * 세션 윈도우 집계 결과를 최종 출력 형식으로 변환하는 ProcessWindowFunction 구현체이다.
     * <p>
     * 이 클래스는 {@link SessionAggregateFunction}이 계산한 {@link SessionAccumulator}
     * 결과를 받아, 윈도우 메타데이터(시작 시간, 종료 시간 등)와 함께 가공한 뒤
     * 문자열 형태의 최종 결과로 출력한다.
     * <p>
     * 입력 키는 {@link Integer} 타입이며, 출력은 요약 문자열인 {@link String}이다.
     * 주로 세션별 이벤트 건수, 총 거래 금액, 윈도우 시간 범위를 포함한
     * 집계 결과를 생성하는 데 사용된다.
     */
    public static class SessionWindowFunction
            extends ProcessWindowFunction<SessionAccumulator, String, Integer, TimeWindow> {

        /**
         * 세션 윈도우 집계 결과를 처리하여 최종 출력값을 생성한다.
         * <p>
         * {@code elements}에는 일반적으로 세션 윈도우에 대해 집계된 결과 1건이 포함되며,
         * {@code context}를 통해 윈도우 시작/종료 시간 같은 메타데이터에 접근할 수 있다.
         * 가공된 결과는 {@code out}으로 수집된다.
         *
         * @param userId 세션 집계의 기준 키
         * @param context 현재 세션 윈도우의 컨텍스트
         * @param elements 세션 윈도우에 대한 집계 결과
         * @param out 최종 출력 결과를 수집하는 Collector
         * @throws Exception 윈도우 결과 처리 중 예외가 발생한 경우
         */
        @Override
        public void process(Integer userId,
                            ProcessWindowFunction<SessionAccumulator, String, Integer, TimeWindow>.Context context,
                            Iterable<SessionAccumulator> elements,
                            Collector<String> out) throws Exception {
            SessionAccumulator sessionAccumulator = elements.iterator().next();
            out.collect(String.format(
                    "SESSION userId=%d, count=%d, total=%.0f, window_start=%s, window_end=%s",
                    userId,
                    sessionAccumulator.count,
                    sessionAccumulator.totalAmount,
                    ISO_FMT.format(Instant.ofEpochMilli(context.window().getStart())),
                    ISO_FMT.format(Instant.ofEpochMilli(context.window().getEnd()))
            ));

        }
    }

    /**
     * Nexus Pay 결제 이벤트를 Kafka에서 수신하여 세션 윈도우 기반으로 집계하는
     * Flink 스트리밍 작업의 진입점이다.
     * <p>
     * 이 메서드는 Flink 실행 환경을 구성하고, Kafka 소스와 워터마크 전략을 설정한 뒤,
     * 유효한 이벤트만 필터링하여 사용자별 세션 윈도우 집계를 수행한다.
     * 집계 결과는 세션별 이벤트 건수 및 총 거래 금액 등의 형태로 계산되어 출력된다.
     * <p>
     * 주요 처리 흐름은 다음과 같다.
     * <p>
     * <ol>
     *   <li>체크포인팅 및 워터마크 간격 설정</li>
     *   <li>Kafka 토픽 {@code nexuspay.events.ingested}로부터 이벤트 수신</li>
     *   <li>이벤트 타임 기반 워터마크 적용</li>
     *   <li>사용자 ID 및 거래 금액이 존재하는 이벤트만 필터링</li>
     *   <li>사용자별 세션 윈도우 집계 수행</li>
     *   <li>집계 결과를 표준 출력으로 기록</li>
     * </ol>
     * @param args 애플리케이션 실행 시 전달되는 인자
     */
    public static void main(String[] args) throws Exception {
        // Flink 스트리밍 실행 환경을 생성하고,
        // 체크포인팅 및 워터마크 생성 주기를 설정한다.
        final StreamExecutionEnvironment env = StreamExecutionEnvironment
                .getExecutionEnvironment();
        env.enableCheckpointing(60_000);
        env.getConfig().setAutoWatermarkInterval(1000);

        // Nexus Pay 수집 이벤트 토픽에서 데이터를 읽기 위한
        // Kafka 소스를 구성한다.
        KafkaSource<NexusPayEvent> kafkaSource = KafkaSource.<NexusPayEvent>builder()
                .setBootstrapServers("kafka-1:9092,kafka-2:9092,kafka-3:9092")
                .setTopics("nexuspay.events.ingested")
                .setGroupId("flink-session-analysis")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new NexusPayEventDeserializer())
                .build();

        // 최대 5초 지연 도착 이벤트를 허용하는 이벤트 타임 워터마크 전략을 정의하고,
        // 이벤트 시각과 유휴 소스 감지 기준을 함께 설정한다.
        WatermarkStrategy<NexusPayEvent> watermarkStrategy = WatermarkStrategy
                .<NexusPayEvent>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                .withTimestampAssigner((event, timestamp) -> event.getEventTimeMillis())
                .withIdleness(Duration.ofMinutes(1));

        // Kafka 소스로부터 이벤트 스트림을 생성한 뒤,
        // 세션 분석에 필요한 기본 조건을 만족하는 데이터만 남긴다.
        DataStream<NexusPayEvent> eventDataStream = env
                .fromSource(kafkaSource, watermarkStrategy, "Nexus Pay Kafka Source")
                .filter(Objects::nonNull)
                .filter(event -> event.getUserId() != null)
                .filter(event -> event.getAmount() != null)
                .name("Filter Session Candidates");

        // 사용자별로 이벤트를 그룹화하고,
        // 세션 간격 기준의 이벤트 타임 세션 윈도우를 적용한 뒤,
        // 세션 집계 결과를 생성하여 출력한다.
        eventDataStream
                .keyBy(NexusPayEvent::getUserId)
                .window(EventTimeSessionWindows.withGap(SESSION_GAP))
                .aggregate(new SessionAggregateFunction(), new SessionWindowFunction())
                .name("Session Window Aggregation")
                .print("SESSION");

        env.execute("Nexus Pay Session Window Analysis Job v1.0");
    }
}
