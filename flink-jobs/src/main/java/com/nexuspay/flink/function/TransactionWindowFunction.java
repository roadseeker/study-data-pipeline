package com.nexuspay.flink.function;


import com.nexuspay.flink.model.AggregatedResult;
import org.apache.flink.streaming.api.functions.windowing.ProcessWindowFunction;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;
import org.apache.flink.util.Collector;

import java.time.Instant;
import java.time.format.DateTimeFormatter;

/**
 * 윈도우 메타데이터(시작·종료 시각, 키)를 집계 결과에 바인딩.
 * AggregateFunction과 결합하여 사용.
 */
public class TransactionWindowFunction extends
        ProcessWindowFunction<AggregatedResult, AggregatedResult, String, TimeWindow> {

    private static final DateTimeFormatter ISO_FMT = DateTimeFormatter
            .ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'")
            .withZone(java.time.ZoneId.of("UTC"));

    @Override
    public void process(String key, Context context, Iterable<AggregatedResult> results,
            Collector<AggregatedResult> out){

        AggregatedResult result = results.iterator().next();

        // 윈도우 메타테이터 바인딩
        result.setEventType(key);
        result.setWindowStart(ISO_FMT.format(Instant.ofEpochMilli(context.window().getStart())));
        result.setWindowEnd(ISO_FMT.format(Instant.ofEpochMilli(context.window().getEnd())));

        out.collect(result);
    }
}
