package com.nexuspay.flink.function;


import com.nexuspay.flink.model.FraudAlert;
import com.nexuspay.flink.model.NexusPayEvent;
import org.apache.flink.api.common.functions.OpenContext;
import org.apache.flink.api.common.state.ListState;
import org.apache.flink.api.common.state.ListStateDescriptor;
import org.apache.flink.api.common.state.ValueState;
import org.apache.flink.api.common.state.ValueStateDescriptor;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.streaming.api.functions.KeyedProcessFunction;
import org.apache.flink.util.Collector;

import java.util.ArrayList;
import java.util.List;

/**
 * Nexus Pay 거래 이벤트 스트림에서 이상거래를 탐지하는
 * {@link KeyedProcessFunction} 구현체이다.
 * <p>
 * 이 함수는 사용자 ID 기준으로 키잉된 {@link NexusPayEvent}를 입력받아,
 * 최근 1분 범위의 이벤트를 상태로 유지하면서 사전에 정의한 탐지 규칙을
 * 실시간으로 평가한다. 규칙을 만족하는 경우 {@link FraudAlert}를 생성해 출력한다.
 * <p>
 * 주요 탐지 규칙은 다음과 같다.
 * <ul>
 *   <li>RULE-001: 동일 사용자 1분 내 3건 이상 연속 거래</li>
 *   <li>RULE-002: 단건 500만원 초과 거래</li>
 *   <li>RULE-003: 동일 사용자 1분 내 거래 금액 합계 1,000만원 초과</li>
 * </ul>
 * 이 클래스는 최근 이벤트 목록과 정리 타이머를 Flink keyed state로 관리하며,
 * 일정 시간이 지난 이벤트는 타이머 기반으로 정리한다.
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
    /** 현재 등록되어 있는 정리 타이머의 event-time timestamp. 재등록 시 기존 타이머는 해제한다. */
    private transient ValueState<Long> cleanupTimerState;

    /**
     * 최근 이벤트 목록 상태와 정리 타이머 상태를 초기화한다.
     * <p>
     * {@code recentEventsState}는 사용자별 최근 1분 범위 이벤트를 보관하고,
     * {@code cleanupTimerState}는 현재 등록된 정리 타이머 시각을 추적한다.
     *
     * @param openContext 함수 초기화 컨텍스트
     */
    @Override
    public void open(OpenContext openContext) {
        recentEventsState = getRuntimeContext().getListState(
                new ListStateDescriptor<>("recent-events",
                        TypeInformation.of(NexusPayEvent.class)));
        cleanupTimerState = getRuntimeContext().getState(
                new ValueStateDescriptor<>("cleanup-timer", Long.class));
    }

    /**
     * 입력된 거래 이벤트를 상태에 반영하고 이상거래 규칙을 평가한다.
     * <p>
     * 처리 순서는 다음과 같다.
     * <ol>
     *   <li>단건 고액 거래 여부를 즉시 판정한다.</li>
     *   <li>현재 이벤트를 최근 이벤트 상태에 추가한다.</li>
     *   <li>1분 범위를 벗어난 만료 이벤트를 제거한다.</li>
     *   <li>거래 빈도 및 누적 금액 기준 이상거래를 평가한다.</li>
     *   <li>후속 상태 정리를 위한 event-time 타이머를 등록하거나 갱신한다.</li>
     * </ol>
     *
     * @param event 현재 처리 중인 Nexus Pay 거래 이벤트
     * @param ctx 타이머 서비스와 현재 키 컨텍스트에 접근하기 위한 처리 컨텍스트
     * @param out 탐지된 이상거래 알림을 내보내는 Collector
     * @throws Exception 상태 접근 또는 타이머 처리 중 예외가 발생한 경우
     */
    @Override
    public void processElement(NexusPayEvent event,
                               Context ctx,
                               Collector<FraudAlert> out) throws Exception {

        long currentTime = event.getEventTimeMillis();
        // ── RULE-002: 단건 고액 거래 즉시 판정 ──
        if (event.getAmount() >= HIGH_AMOUNT_THRESHOLD) {
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
        for (NexusPayEvent e : recentEventsState.get()) {
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
                .mapToDouble(e -> e.getAmount() !=null ? e.getAmount() : 0)
                .sum();
        if(totalAmount > SUM_AMOUNT_THRESHOLD) {
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
        // 기존 타이머가 있으면 해제 후 최신 시각 기준으로 하나만 등록한다.
        // 매 이벤트마다 등록하면 사용자당 타이머가 폭증해 상태 크기가 비정상적으로 커진다.
        long nextTimer = currentTime + WINDOW_DURATION_MS * 2;
        Long existingTimer = cleanupTimerState.value();

        if (existingTimer == null || nextTimer - existingTimer > WINDOW_DURATION_MS) {
            if(existingTimer != null) {
                ctx.timerService().deleteEventTimeTimer(existingTimer);
            }
            ctx.timerService().registerEventTimeTimer(nextTimer);
            cleanupTimerState.update(nextTimer);
        }
    }

    /**
     * 등록된 정리 타이머가 발동했을 때 만료된 이벤트를 상태에서 제거한다.
     * <p>
     * 타이머 시각 기준으로 최근 1분 범위에 포함되는 이벤트만 남기고
     * 오래된 이벤트는 삭제하여 keyed state 크기가 지속적으로 증가하지 않도록 한다.
     *
     * @param timestamp 발동한 event-time 타이머 시각
     * @param ctx 현재 타이머 실행 컨텍스트
     * @param out 타이머 처리 시 출력할 알림 Collector
     * @throws Exception 상태 정리 중 예외가 발생한 경우
     */
    @Override
    public void onTimer(long timestamp,
                        OnTimerContext ctx,
                        Collector<FraudAlert> out) throws Exception {
        // 타이머 발동 시 만료 이벤트 정리
        List<NexusPayEvent> activeEvents = new ArrayList<>();
        for (NexusPayEvent e : recentEventsState.get()) {
            if (timestamp - e.getEventTimeMillis() <= WINDOW_DURATION_MS) {
                activeEvents.add(e);
            }
        }
        recentEventsState.update(activeEvents);
    }
}
