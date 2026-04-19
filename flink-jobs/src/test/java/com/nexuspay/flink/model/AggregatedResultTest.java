package com.nexuspay.flink.model;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class AggregatedResultTest {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Test
    @DisplayName("toJson은 집계 결과를 Kafka 싱크용 JSON으로 직렬화한다")
    void toJsonReturnsExpectedPayload() throws Exception {
        AggregatedResult result = new AggregatedResult(
                "PAYMENT",
                "2026-04-18T10:00:00Z",
                "2026-04-18T10:05:00Z",
                3L,
                45000.0,
                15000.0,
                20000.0,
                10000.0
        );

        JsonNode json = objectMapper.readTree(result.toJson());

        assertThat(json.get("event_type").asText()).isEqualTo("PAYMENT");
        assertThat(json.get("window_start").asText()).isEqualTo("2026-04-18T10:00:00Z");
        assertThat(json.get("window_end").asText()).isEqualTo("2026-04-18T10:05:00Z");
        assertThat(json.get("transaction_count").asLong()).isEqualTo(3L);
        assertThat(json.get("total_amount").asDouble()).isEqualTo(45000.0);
        assertThat(json.get("avg_amount").asDouble()).isEqualTo(15000.0);
        assertThat(json.get("max_amount").asDouble()).isEqualTo(20000.0);
        assertThat(json.get("min_amount").asDouble()).isEqualTo(10000.0);
    }
}
