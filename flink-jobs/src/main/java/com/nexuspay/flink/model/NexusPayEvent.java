package com.nexuspay.flink.model;

import java.io.Serializable;


/**
 * Nexus Pay 표준 이벤트 모델.
 * Week 3 NiFi 스키마 표준화에서 정의한 nexuspay-standard-schema.avsc와 1:1 대응.
 *
 * 필드 매핑:
 *   event_id       — 이벤트 고유 ID
 *   event_type     — PAYMENT | TRANSFER | WITHDRAWAL | SETTLEMENT | CUSTOMER_UPDATE
 *   user_id        — 사용자 ID (파티션 키)
 *   amount         — 거래 금액 (결제·이체·출금·정산)
 *   currency       — 통화 코드 (KRW, USD 등)
 *   status         — 이벤트 상태
 *   data_source    — payment-api | settlement-csv | customer-db
 *   event_timestamp — 이벤트 발생 시각 (ISO 8601)
 *   schema_version — 스키마 버전
 */
public class NexusPayEvent {
    private static final long serialVersionUID = 1L;

    private String eventId;
    private String eventType;
    private Integer userId;
    private Double amount;
    private String currency;
    private String status;
    private String dataSource;
    private String eventTimestamp; // ISO 8601: "2026-04-07T14:30:00Z"
    private String schemaVersion; //
    // NiFi 표준 스키마의 추가 필드 (merchant, channel, 이상거래 플래그)
    private String merchantId;
    private String merchantName;
    private String merchantCategory;
    private String channel;
    private Boolean isSuspicious;

    //기본생성자 (Flink 직렬화 필수)
    public NexusPayEvent() {}

    // Getters & Setters


    public String getEventId() {
        return eventId;
    }

    public void setEventId(String eventId) {
        this.eventId = eventId;
    }

    public String getEventType() {
        return eventType;
    }

    public void setEventType(String eventType) {
        this.eventType = eventType;
    }

    public Integer getUserId() {
        return userId;
    }

    public void setUserId(Integer userId) {
        this.userId = userId;
    }

    public Double getAmount() {
        return amount;
    }

    public void setAmount(Double amount) {
        this.amount = amount;
    }

    public String getCurrency() {
        return currency;
    }

    public void setCurrency(String currency) {
        this.currency = currency;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getDataSource() {
        return dataSource;
    }

    public void setDataSource(String dataSource) {
        this.dataSource = dataSource;
    }

    public String getEventTimestamp() {
        return eventTimestamp;
    }

    public void setEventTimestamp(String eventTimestamp) {
        this.eventTimestamp = eventTimestamp;
    }

    public String getSchemaVersion() {
        return schemaVersion;
    }

    public void setSchemaVersion(String schemaVersion) {
        this.schemaVersion = schemaVersion;
    }

    public String getMerchantId() {
        return merchantId;
    }

    public void setMerchantId(String merchantId) {
        this.merchantId = merchantId;
    }

    public String getMerchantName() {
        return merchantName;
    }

    public void setMerchantName(String merchantName) {
        this.merchantName = merchantName;
    }

    public String getMerchantCategory() {
        return merchantCategory;
    }

    public void setMerchantCategory(String merchantCategory) {
        this.merchantCategory = merchantCategory;
    }

    public String getChannel() {
        return channel;
    }

    public void setChannel(String channel) {
        this.channel = channel;
    }

    public Boolean getSuspicious() {
        return isSuspicious;
    }

    public void setSuspicious(Boolean suspicious) {
        isSuspicious = suspicious;
    }

    /**
     * 이벤트 타임스탬프를 epoch milliseconds로 변환.
     * Watermark 할당에 사용
     */
    public long getEventTimeMillis() {
        try {
            return java.time.Instant.parse(this.eventTimestamp).toEpochMilli();
        } catch (Exception e) {
            // 파싱 실패 시 현재 시간 반환 (Side Output으로 별도 처리 권장)
            return System.currentTimeMillis();
        }
    }

    @Override
    public String toString() {
        return String.format("NexusPayEvent{id=%s, type=%s, user=%s, amount=%.0f, time=%s}",
                eventId, eventType, userId, amount, eventTimestamp);
    }

}
