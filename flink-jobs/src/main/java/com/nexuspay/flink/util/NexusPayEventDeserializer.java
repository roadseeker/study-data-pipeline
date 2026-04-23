package com.nexuspay.flink.util;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import com.nexuspay.flink.model.NexusPayEvent;

import java.io.Serial;
import java.io.Serializable;

/**
 * Kafka에서 수신한 JSON 바이트를 NexusPayEvent POJO로 변환.
 * NiFi 표준 스키마의 snake_case 필드명을 Java camelCase에 매핑.
 */
public class NexusPayEventDeserializer implements DeserializationSchema<NexusPayEvent>, Serializable {
    @Serial
    private static final long serialVersionUID = 1L;
    private transient ObjectMapper mapper;

    private ObjectMapper getMapper() {
        if (mapper == null) {
            mapper = new ObjectMapper();
            mapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
            mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        }
        return mapper;
    }

    @Override
    public NexusPayEvent deserialize(byte[] message) {
        try {
            return getMapper().readValue(message, NexusPayEvent.class);
        } catch (Exception e) {
            // 역직렬화 실패 시 null 반환 → .filter()로 제거
            return null;
        }
    }

    @Override
    public boolean isEndOfStream(NexusPayEvent event) {
        return false;  // 무한 스트림
    }

    @Override
    public TypeInformation<NexusPayEvent> getProducedType() {
        return TypeInformation.of(NexusPayEvent.class);
    }
}
