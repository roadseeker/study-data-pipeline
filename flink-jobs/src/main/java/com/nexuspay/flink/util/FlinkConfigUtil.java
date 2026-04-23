package com.nexuspay.flink.util;

import org.apache.flink.core.execution.CheckpointingMode;
import org.apache.flink.configuration.CheckpointingOptions;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.environment.CheckpointConfig;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

/**
 * Flink 실행 환경 공통 설정 유틸리티.
 * 모든 잡에서 동일한 Exactly-once 체크포인트 설정을 적용한다.
 */
public class FlinkConfigUtil {

    /** 체크포인트 저장 경로(호스트 바인드 마운트). docker-compose.yml 설정과 일치시킬 것. */
    private static final String CHECKPOINT_STORAGE_URI = "file:///opt/flink/checkpoints";

    /**
     * Exactly-once 체크포인트 설정 적용.
     *
     * @param env Flink 실행 환경
     * @param checkpointIntervalMs 체크포인트 주기 (밀리초)
     */
    public static void configureExactlyOnce(StreamExecutionEnvironment env, long checkpointIntervalMs) {

        // 1. 체크포인트 저장소: 파일 시스템 (JobManager 메모리 기본값은 장애 복구 불가)
        Configuration configuration = new Configuration();
        configuration.set(CheckpointingOptions.CHECKPOINT_STORAGE, "filesystem");
        configuration.set(CheckpointingOptions.CHECKPOINTS_DIRECTORY, CHECKPOINT_STORAGE_URI);
        env.configure(configuration);

        // 2. 체크포인트 모드: EXACTLY_ONCE
        env.enableCheckpointing(checkpointIntervalMs, CheckpointingMode.EXACTLY_ONCE);

        CheckpointConfig cpConfig = env.getCheckpointConfig();

        // 3. 체크포인트 타임아웃: 2분 (대규모 상태에서도 충분한 시간)
        cpConfig.setCheckpointTimeout(120_000);

        // 4. 최소 간격: 체크포인트 간 최소 30초 간격
        cpConfig.setMinPauseBetweenCheckpoints(30_000);

        // 5. 동시 체크포인트: 1개만 허용 (리소스 경합 방지)
        cpConfig.setMaxConcurrentCheckpoints(1);

        // 6. 연속 실패 허용: 3회까지 허용 후 잡 실패
        cpConfig.setTolerableCheckpointFailureNumber(3);

        // 7. Unaligned Checkpoint: 백프레셔 상황에서도 체크포인트 진행
        cpConfig.enableUnalignedCheckpoints();


    }

    /**
     * 재시작 전략 설정.
     * 장애 발생 시 최대 3회 재시작, 재시작 간 10초 대기.
     *
     * Flink 2.2 실습에서는 재시작 전략을 클러스터/잡 설정으로 관리한다.
     * 명시적 Java API 설정이 필요한 경우 Flink 버전에 맞는 configuration option으로 확장한다.
     */
    public static void configureRestartStrategy(StreamExecutionEnvironment env) {
        // no-op: Day 4에서는 체크포인트 복구 검증에 집중한다.
    }
}
