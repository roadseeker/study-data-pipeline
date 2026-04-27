"""
데이터 품질 검증 모듈
- YAML 규칙 기반 자동 검증
- 검증 결과 리포트 생성
- critical 위반 레코드 격리, warning 위반 레코드 플래그
"""
import yaml
from datetime import datetime, timedelta
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class QualityResult:
    """단일 규칙의 검증 결과"""
    rule_id: str
    rule_name: str
    severity: str
    total_records: int
    passed_records: int
    failed_records: int
    pass_rate: float
    details: str = ""


@dataclass
class QualityReport:
    """전체 품질 검증 리포트"""
    processing_date: str
    total_input_records: int
    total_output_records: int
    quarantined_records: int
    flagged_records: int
    results: List[QualityResult] = field(default_factory=list)
    generated_at: str = ""

    def summary(self) -> str:
        lines = [
            "=" * 70,
            f"[데이터 품질 검증 리포트]",
            f"  처리 일자: {self.processing_date}",
            f"  생성 시각: {self.generated_at}",
            "=" * 70,
            f"  입력 레코드:  {self.total_input_records:>10,}건",
            f"  출력 레코드:  {self.total_output_records:>10,}건",
            f"  격리 레코드:  {self.quarantined_records:>10,}건 (critical 위반)",
            f"  플래그 레코드: {self.flagged_records:>10,}건 (warning 위반)",
            "-" * 70,
        ]
        for r in self.results:
            status = "✓ PASS" if r.pass_rate >= 0.99 else "✗ FAIL"
            lines.append(
                f"  [{r.rule_id}] {r.rule_name}: "
                f"{r.failed_records:,}건 위반 "
                f"({r.pass_rate:.2%}) [{r.severity}] {status}"
            )
        lines.append("=" * 70)
        return "\n".join(lines)


class QualityChecker:
    """데이터 품질 검증기"""
    # __init__()는 파이썬에서 객체가 생성될 때 자동으로 실행되는 초기화 메서드이다.
    # rules_path 매개변수로 품질 규칙이 정의된 YAML 파일의 경로를 받는다. 기본값은 "config/quality_rules.yaml"이다.
    def __init__(self, rules_path: str = "config/quality_rules.yaml"):
        with open(rules_path, "r") as f:
            # 파이썬에서는 self.rules = ...처럼 처음 할당하는 순간 객체 속성이 동적으로 생성됩니다
            self.rules = yaml.safe_load(f)["rules"] # YAML 파일에서 "rules" 키 아래에 있는 규칙 목록을 읽어서 self.rules 속성에 저장한다. 이후 이 객체의 다른 메서드에서 self.rules를 참조하여 검증 로직을 수행할 수 있다.

    # 결과를 튜플로 반환하는 validate() 메서드 정의. 
    # 입력으로는 검증할 DataFrame과 처리 일자를 문자열로 받는다. 
    # 반환값은 (clean_df, quarantine_df, report) 형태의 튜플이다.
    # tuple은 파이썬의 여러 값을 한 번에 묶는 자료형입니다. 여기서는 세 가지 값을 하나의 묶음으로 반환하기 위해 튜플을 사용합니다.
    # 받을 때도 clean_df, quarantine_df, report = checker.validate(df, "2026-04-27")처럼 튜플 언패킹을 통해 각각의 값을 개별 변수로 쉽게 사용할 수 있습니다.
    def validate(self, df: DataFrame, processing_date: str) -> tuple: 
        """
        DataFrame에 품질 규칙을 적용한다.
        Returns:
            (clean_df, quarantine_df, report)
            - clean_df: 품질 통과 레코드 (warning 플래그 포함)
            - quarantine_df: critical 위반으로 격리된 레코드
            - report: QualityReport 객체
        """
        total_input = df.count()
        results = []

        # 품질 플래그 컬럼 초기화
        df = df.withColumn("_quality_flags", F.array())
        df = df.withColumn("_is_quarantined", F.lit(False))

        for rule in self.rules:
            rule_id = rule["id"]
            severity = rule["severity"]
            rule_type = rule["type"]

            if rule_type == "completeness":
                df, result = self._check_completeness(df, rule)
            elif rule_type == "uniqueness":
                df, result = self._check_uniqueness(df, rule)
            elif rule_type == "validity":
                df, result = self._check_validity(df, rule)
            elif rule_type == "timeliness":
                df, result = self._check_timeliness(df, rule)
            else:
                continue

            result.total_records = total_input
            results.append(result)

        # 격리 vs 정상 분리
        quarantine_df = df.filter(F.col("_is_quarantined") == True)
        clean_df = df.filter(F.col("_is_quarantined") == False)

        # _quality_flags 배열을 쉼표 구분 문자열로 변환
        clean_df = clean_df.withColumn(
            "quality_flags",
            F.when(F.size("_quality_flags") > 0,
                   F.concat_ws(",", "_quality_flags"))
            .otherwise(F.lit(None))
        )
        # is_anomaly 플래그 설정
        clean_df = clean_df.withColumn(
            "is_anomaly",
            F.size("_quality_flags") > 0
        )
        # 임시 컬럼 제거
        clean_df = clean_df.drop("_quality_flags", "_is_quarantined")
        quarantine_df = quarantine_df.drop("_quality_flags", "_is_quarantined")

        quarantine_count = quarantine_df.count()
        clean_count = clean_df.count()
        flagged_count = clean_df.filter(F.col("is_anomaly") == True).count()

        report = QualityReport(
            processing_date=processing_date,
            total_input_records=total_input,
            total_output_records=clean_count,
            quarantined_records=quarantine_count,
            flagged_records=flagged_count,
            results=results,
            generated_at=datetime.now().isoformat(),
        )

        return clean_df, quarantine_df, report

    # 앞의 _는 **“이 메서드는 내부용(private 성격)이다”**라는 관례입니다. 
    # 실제로는 외부에서도 호출할 수 있지만, 개발자들에게 이 메서드는 클래스 내부에서만 사용하기 위한 것임을 알리는 역할을 합니다.
    def _check_completeness(self, df, rule) -> tuple:
        """필수 필드 null 체크"""
        fields = rule["fields"]
        condition = F.lit(False)
        for field_name in fields:
            if field_name in df.columns:
                condition = condition | F.col(field_name).isNull()

        failed_count = df.filter(condition).count()
        passed_count = df.count() - failed_count

        if rule["severity"] == "critical":
            df = df.withColumn(
                "_is_quarantined",
                F.when(condition, True).otherwise(F.col("_is_quarantined"))
            )
        else:
            df = df.withColumn(
                "_quality_flags",
                F.when(condition,
                       F.concat(F.col("_quality_flags"), F.array(F.lit(rule["id"]))))
                .otherwise(F.col("_quality_flags"))
            )

        result = QualityResult(
            rule_id=rule["id"], rule_name=rule["name"],
            severity=rule["severity"], total_records=0,
            passed_records=passed_count, failed_records=failed_count,
            pass_rate=passed_count / max(passed_count + failed_count, 1),
        )
        return df, result

    def _check_uniqueness(self, df, rule) -> tuple:
        """중복 체크"""
        key_fields = rule["key_fields"]
        from pyspark.sql.window import Window

        # 중복 건수 계산
        dup_df = df.groupBy(key_fields).count().filter(F.col("count") > 1)
        dup_count = dup_df.agg(F.sum(F.col("count") - 1)).collect()[0][0] or 0

        # 중복 제거: 최신 레코드 유지
        if rule.get("strategy") == "keep_latest":
            w = Window.partitionBy(key_fields).orderBy(F.col("kafka_timestamp").desc())
            df = df.withColumn("_row_num", F.row_number().over(w))
            df = df.withColumn(
                "_is_quarantined",
                F.when(F.col("_row_num") > 1, True).otherwise(F.col("_is_quarantined"))
            )
            df = df.drop("_row_num")

        passed_count = df.count() - int(dup_count)
        result = QualityResult(
            rule_id=rule["id"], rule_name=rule["name"],
            severity=rule["severity"], total_records=0,
            passed_records=passed_count, failed_records=int(dup_count),
            pass_rate=passed_count / max(passed_count + int(dup_count), 1),
        )
        return df, result

    def _check_validity(self, df, rule) -> tuple:
        """유효성 체크 (허용값 또는 범위)"""
        field_name = rule["field"]

        if "allowed_values" in rule:
            condition = ~F.col(field_name).isin(rule["allowed_values"])
        elif "min_value" in rule and "max_value" in rule:
            condition = (
                (F.col(field_name) < rule["min_value"]) |
                (F.col(field_name) > rule["max_value"])
            )
        elif "min_value" in rule:
            condition = F.col(field_name) < rule["min_value"]
        else:
            condition = F.lit(False)

        # null은 별도 규칙에서 처리하므로 여기서는 제외
        condition = condition & F.col(field_name).isNotNull()
        failed_count = df.filter(condition).count()
        passed_count = df.count() - failed_count

        if rule["severity"] == "critical":
            df = df.withColumn(
                "_is_quarantined",
                F.when(condition, True).otherwise(F.col("_is_quarantined"))
            )
        else:
            df = df.withColumn(
                "_quality_flags",
                F.when(condition,
                       F.concat(F.col("_quality_flags"), F.array(F.lit(rule["id"]))))
                .otherwise(F.col("_quality_flags"))
            )

        result = QualityResult(
            rule_id=rule["id"], rule_name=rule["name"],
            severity=rule["severity"], total_records=0,
            passed_records=passed_count, failed_records=failed_count,
            pass_rate=passed_count / max(passed_count + failed_count, 1),
        )
        return df, result

    def _check_timeliness(self, df, rule) -> tuple:
        """적시성 체크"""
        field_name = rule["field"]
        max_delay = rule["max_delay_hours"]
        cutoff = datetime.now() - timedelta(hours=max_delay)

        condition = F.col(field_name) < F.lit(cutoff)
        failed_count = df.filter(condition & F.col(field_name).isNotNull()).count()
        passed_count = df.count() - failed_count

        df = df.withColumn(
            "_quality_flags",
            F.when(condition & F.col(field_name).isNotNull(),
                   F.concat(F.col("_quality_flags"), F.array(F.lit(rule["id"]))))
            .otherwise(F.col("_quality_flags"))
        )

        result = QualityResult(
            rule_id=rule["id"], rule_name=rule["name"],
            severity=rule["severity"], total_records=0,
            passed_records=passed_count, failed_records=failed_count,
            pass_rate=passed_count / max(passed_count + failed_count, 1),
        )
        return df, result
