package com.nexuspay.flink.function;


import com.nexuspay.flink.model.AggregatedResult;
import com.nexuspay.flink.model.NexusPayEvent;
import org.apache.flink.api.common.functions.AggregateFunction;

import java.io.Serial;

/**
 * 거래 이벤트 증분 집계 함수.
 * <p>
 * 누적기(Accumulator)에 건수·총액·최대·최소를 증분 갱신한다.
 * 메모리 효율적 — 원본 이벤트를 저장하지 않고 통계값만 유지.
 */
public class TransactionAggregateFunction
        implements AggregateFunction<NexusPayEvent, TransactionAggregateFunction.Accumulator, AggregatedResult> {

    public static class Accumulator implements java.io.Serializable {
        @Serial
        private static final long serialVersionUID = 1L;

        public long count = 0L;
        public double totalAmount = 0.0;
        public double maxAmount = Double.MIN_VALUE;
        public double minAmount = Double.MAX_VALUE;
    }

    @Override
    public Accumulator createAccumulator() {
        return new Accumulator();
    }

    @Override
    public Accumulator add(NexusPayEvent event,
                           Accumulator accumulator) {
        accumulator.count++;
        double amount = event.getAmount() != null ? event.getAmount() : 0.0;
        accumulator.totalAmount += amount;
        accumulator.maxAmount = Math.max(accumulator.maxAmount, amount);
        accumulator.minAmount = Math.min(accumulator.minAmount, amount);
        return accumulator;
    }

    @Override
    public AggregatedResult getResult(Accumulator accumulator) {
        // 윈도우 메타데이터는 ProcessWindowFunction에서 추가
        double avg = accumulator.count > 0 ? accumulator.totalAmount / accumulator.count : 0.0;
        return new AggregatedResult(null, null, null, // eventType, windowStart, windowEnd — ProcessWindowFunction에서 설정
                accumulator.count, accumulator.totalAmount, avg, accumulator.maxAmount, accumulator.minAmount);
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
