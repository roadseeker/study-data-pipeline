package com.nexuspay.flink.function;


import com.nexuspay.flink.model.NexusPayEvent;
import org.apache.flink.util.OutputTag;

/**
 * 지연 데이터(Late Data) Side Output 태그 정의.
 * <p>
 * Watermark 이후 도착한 이벤트는 Side Output으로 분리하여:
 * 1. DLQ 토픽으로 전송 (재처리 또는 수동 검토)
 * 2. 별도 로그에 기록 (감사 추적)
 * 3. 지연 통계 수집 (Watermark 전략 튜닝 자료)
 */
public class LateDataSideOutputFunction {
    /** Tumbling Window용 지연 이벤트 태그. */
    public static final OutputTag<NexusPayEvent> LATE_DATA_TAG
            = new OutputTag<>("late-data-tumbling"){};

    /** Sliding Window용 지연 이벤트 태그 — 두 경로 분리로 union 시 충돌 방지. */
    public static final OutputTag<NexusPayEvent> SLIDING_LATE_DATA_TAG
            = new OutputTag<>("late-data-sliding"){};
}
