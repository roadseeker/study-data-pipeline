package com.nexuspay.flink.util;


import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.kafka.clients.producer.ProducerConfig;

import java.util.Properties;

/**
 * Exactly-once Kafka 싱크 빌더.
 *
 * Kafka 트랜잭션 프로듀서를 사용하여 체크포인트와 연동된 2-Phase Commit을 수행한다.
 * 체크포인트 완료 시에만 Kafka 트랜잭션을 커밋하므로 중복 메시지가 발생하지 않는다.
 */
public class ExactlyOnceKafkaSinkBuilder {
    public static KafkaSink<String> build(String brokers, String topic, String transactionalIdPrefix) {

        Properties kafkaProps = new Properties();
        // Exactly-once를 위한 Kafka 프로듀서 설정.
        // Flink 프로듀서 측 트랜잭션 타임아웃은 브로커의 transaction.max.timeout.ms(기본 15분)보다
        // 반드시 작아야 한다. 경계값 충돌을 피하기 위해 10분으로 설정.
        kafkaProps.setProperty(ProducerConfig.TRANSACTION_TIMEOUT_CONFIG, "600000");  // 10분
        kafkaProps.setProperty(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
        kafkaProps.setProperty(ProducerConfig.ACKS_CONFIG, "all");
        kafkaProps.setProperty(ProducerConfig.RETRIES_CONFIG, "3");
        return KafkaSink.<String>builder()
                .setBootstrapServers(brokers)
                .setRecordSerializer(KafkaRecordSerializationSchema.builder()
                        .setTopic(topic)
                        .setValueSerializationSchema(new SimpleStringSchema())
                        .build())
                .setDeliveryGuarantee(org.apache.flink.connector.base.DeliveryGuarantee.EXACTLY_ONCE)
                .setTransactionalIdPrefix(transactionalIdPrefix)
                .setKafkaProducerConfig(kafkaProps)
                .build();
    }
}
