package com.nexuspay.flink.model;

import java.io.Serial;
import java.io.Serializable;


/**
 * 윈도우 집계 결과 모델.
 * 5분 Tumbling Window 기준으로 이벤트 타입별 집계값을 담는다.
 */
public class AggregatedResult implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;

    private String eventType; // PAYMENT, TRANSFER, WITHDRAWAL
    private String windowStart; // 윈도우 시작 시각 (ISO 8601)
    private String windowEnd;   // 윈도우 종료 시각 (ISO 8601)
    private long transactionCount; // 거래 건수
    private double totalAmount; // 거래 총액
    private double avgAmount; // 거래 평균액
    private double maxAmount; // 최대 거래 금액
    private double minAmount; // 최소 거래 금액

    public AggregatedResult() {
    }

    public AggregatedResult(String eventType, String windowStart, String windowEnd, long count,
                            double total, double avg, double max, double min) {
        this.eventType = eventType;
        this.windowStart = windowStart;
        this.windowEnd = windowEnd;
        this.transactionCount = count;
        this.totalAmount = total;
        this.avgAmount = avg;
        this.maxAmount = max;
        this.minAmount = min;
    }

    public String getEventType() {
        return eventType;
    }

    public void setEventType(String eventType) {
        this.eventType = eventType;
    }

    public String getWindowStart() {
        return windowStart;
    }

    public void setWindowStart(String windowStart) {
        this.windowStart = windowStart;
    }

    public String getWindowEnd() {
        return windowEnd;
    }

    public void setWindowEnd(String windowEnd) {
        this.windowEnd = windowEnd;
    }

    public long getTransactionCount() {
        return transactionCount;
    }

    public void setTransactionCount(long transactionCount) {
        this.transactionCount = transactionCount;
    }

    public double getTotalAmount() {
        return totalAmount;
    }

    public void setTotalAmount(double totalAmount) {
        this.totalAmount = totalAmount;
    }

    public double getAvgAmount() {
        return avgAmount;
    }

    public void setAvgAmount(double avgAmount) {
        this.avgAmount = avgAmount;
    }

    public double getMaxAmount() {
        return maxAmount;
    }

    public void setMaxAmount(double maxAmount) {
        this.maxAmount = maxAmount;
    }

    public double getMinAmount() {
        return minAmount;
    }

    public void setMinAmount(double minAmount) {
        this.minAmount = minAmount;
    }

    @Override
    public String toString() {
        return String.format("AggregatedResult{type=%s, window=[%s, %s], count=%d, " +
                        "total=%.2f, avg=%.2f, max=%.2f, min=%.2f}",
                eventType, windowStart, windowEnd, transactionCount,
                totalAmount, avgAmount, maxAmount, minAmount);
    }

    /**
     * Json serialization (kafka 싱크용)
     */
    public String toJson() {
        return String.format("{\"event_type\":\"%s\", \"window_start\":\"%s\", \"window_end\":\"%s\", \"transaction_count\":%d, " +
                        "\"total_amount\":%.0f, \"avg_amount\":%.0f, \"max_amount\":%.0f, \"min_amount\":%.0f}",
                eventType, windowStart, windowEnd, transactionCount,
                totalAmount, avgAmount, maxAmount, minAmount);
    }
}
