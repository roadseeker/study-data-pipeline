package com.nexuspay.flink.model;


import java.io.Serial;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

/**
 * 이상거래 탐지 알림 모델.
 * <p>
 * 탐지 규칙:
 *   RULE-001: 동일 사용자 1분 내 3건 이상 연속 거래
 *   RULE-002: 단건 500만원 초과 거래
 *   RULE-003: 동일 사용자 1분 내 거래 금액 합계 1,000만원 초과
 */
public class FraudAlert implements java.io.Serializable{
    @Serial
    private static final long serialVersionUID = 1L;

    /** 이상거래 알림 고유 식별자 */
    private String alertId;

    /** 탐지 규칙 식별자 */
    private String ruleId;

    /** 탐지 규칙 설명 */
    private String ruleDescription;

    /** 이상거래가 발생한 사용자 식별자 */
    private Integer userId;

    /** 알림 심각도 수준 */
    private String severity; // HIGH, MEDIUM, LOW

    /** 탐지를 유발한 대표 이벤트 식별자 */
    private String triggerEventId;

    /** 탐지를 유발한 대표 거래 금액 */
    private double triggerAmount;

    /** 탐지 조건에 포함된 이벤트 건수 */
    private int eventCount;

    /** 이상거래 탐지 시각 */
    private String detectedAt;


    public FraudAlert() {}

    public FraudAlert(String ruleId, String description,
                      Integer userId, String severity, String triggerEventId,
                      double amount, int count) {
        this.alertId = "ALERT-" + System.currentTimeMillis();
        this.ruleId = ruleId;
        this.ruleDescription = description;
        this.userId = userId;
        this.severity = severity;
        this.triggerEventId = triggerEventId;
        this.triggerAmount = amount;
        this.eventCount = count;
        this.detectedAt = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'")
                .withZone(ZoneOffset.UTC)
                .format(Instant.now());
    }

    // Getter and Setter methods
    public String getAlertId() {
        return alertId;
    }

    public void setAlertId(String alertId) {
        this.alertId = alertId;
    }

    public String getRuleId() {
        return ruleId;
    }

    public void setRuleId(String ruleId) {
        this.ruleId = ruleId;
    }

    public String getRuleDescription() {
        return ruleDescription;
    }

    public void setRuleDescription(String ruleDescription) {
        this.ruleDescription = ruleDescription;
    }

    public Integer getUserId() {
        return userId;
    }

    public void setUserId(Integer userId) {
        this.userId = userId;
    }

    public String getSeverity() {
        return severity;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }

    public String getTriggerEventId() {
        return triggerEventId;
    }

    public void setTriggerEventId(String triggerEventId) {
        this.triggerEventId = triggerEventId;
    }

    public double getTriggerAmount() {
        return triggerAmount;
    }

    public void setTriggerAmount(double triggerAmount) {
        this.triggerAmount = triggerAmount;
    }

    public int getEventCount() {
        return eventCount;
    }

    public void setEventCount(int eventCount) {
        this.eventCount = eventCount;
    }

    public String getDetectedAt() {
        return detectedAt;
    }

    public void setDetectedAt(String detectedAt) {
        this.detectedAt = detectedAt;
    }

    @Override
    public String toString() {
        return String.format("[%s] %s | user=%d, severity=%s,amount=%.0f, events=%d",
                ruleId, ruleDescription, userId, severity, triggerAmount, eventCount);
    }

    public String toJson() {
        return String.format("{\"alert_id\":\"%s\", \"rule_id\":\"%s\", \"rule_description\":\"%s\", " +
                        "\"user_id\":%d, \"severity\":\"%s\", \"trigger_event_id\":\"%s\", \"trigger_amount\":%.0f, \"event_count\":%d, \"detected_at\":\"%s\"}",
                alertId, ruleId, ruleDescription, userId, severity, triggerEventId, triggerAmount, eventCount, detectedAt);
    }
}
