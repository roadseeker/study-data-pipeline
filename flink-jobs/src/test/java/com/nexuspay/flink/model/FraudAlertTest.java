package com.nexuspay.flink.model;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class FraudAlertTest {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Test
    @DisplayName("toJson은 이상거래 알림을 Kafka 싱크용 JSON으로 직렬화한다")
    void toJsonReturnsExpectedPayload() throws Exception {
        FraudAlert alert = new FraudAlert();
        alert.setAlertId("ALERT-20260419-0001");
        alert.setRuleId("RULE-002");
        alert.setRuleDescription("단건 500만원 초과 거래");
        alert.setUserId(1001);
        alert.setSeverity("HIGH");
        alert.setTriggerEventId("evt-20260419-9001");
        alert.setTriggerAmount(7500000.0);
        alert.setEventCount(1);
        alert.setDetectedAt("2026-04-19T09:30:00Z");

        JsonNode json = objectMapper.readTree(alert.toJson());

        assertThat(json.get("alert_id").asText()).isEqualTo("ALERT-20260419-0001");
        assertThat(json.get("rule_id").asText()).isEqualTo("RULE-002");
        assertThat(json.get("rule_description").asText()).isEqualTo("단건 500만원 초과 거래");
        assertThat(json.get("user_id").asInt()).isEqualTo(1001);
        assertThat(json.get("severity").asText()).isEqualTo("HIGH");
        assertThat(json.get("trigger_event_id").asText()).isEqualTo("evt-20260419-9001");
        assertThat(json.get("trigger_amount").asDouble()).isEqualTo(7500000.0);
        assertThat(json.get("event_count").asInt()).isEqualTo(1);
        assertThat(json.get("detected_at").asText()).isEqualTo("2026-04-19T09:30:00Z");
    }
}
