"""
데이터 품질 검증 모듈
- YAML 규칙 기반 자동 검증
- 검증 결과 리포트 생성
- critical 위반 레코드 격리, warning 위반 레코드 플래그
"""
import yaml
from datetime import datetime, timedelta
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from dataclasses import dataclass, field
from typing import List


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
            rule_type = rule["type"]

            if rule_type == "completeness":
                df, result = self._check_completeness(df, rule, total_input)
            elif rule_type == "uniqueness":
                df, result = self._check_uniqueness(df, rule, total_input)
            elif rule_type == "validity":
                df, result = self._check_validity(df, rule, total_input)
            elif rule_type == "timeliness":
                df, result = self._check_timeliness(df, rule, total_input, processing_date)
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
    @staticmethod
    def _apply_rule_result(df: DataFrame, rule, condition, total_records: int) -> tuple:
        #  전체 건수와 실패 건수를 한 번의 aggregation으로 계산
        stats = (
            df.select(
                # F.count(F.lit(1))는 모든 레코드에 대해 1을 반환하는 표현입니다. 따라서 전체 레코드 수를 계산할 때 사용됩니다.
                F.count(F.lit(1)).alias("total_count"),
                # 조건이 True인 경우 1, False인 경우 0으로 계산하여 실패 건수를 합산합니다.
                F.sum(F.when(condition, 1).otherwise(0)).alias("failed_count"),
            )
            .collect()[0]
        )
        # 실패 건수를 정수로 꺼낸다
        # or 0은 failed_count가 None인 경우를 대비한 안전장치입니다. 조건이 True인 레코드가 하나도 없으면 sum() 결과가 None이 될 수 있기 때문입니다.
        # total_records는 이미 validate() 메서드에서 계산된 전체 레코드 수입니다. 여기서는 total_records를 그대로 사용하여 passed_count를 계산합니다.
        failed_count = int(stats["failed_count"] or 0)
        passed_count = total_records - failed_count

        if rule["severity"] == "critical":
            df = df.withColumn(
                "_is_quarantined",
                F.when(condition, True).otherwise(F.col("_is_quarantined"))
            )
        else:
            df = df.withColumn(
                "_quality_flags",
                # condition이 True인 행이면
                # 기존 _quality_flags 배열 뒤에 현재 규칙 ID를 추가
                # 그렇지 않으면 기존 배열 유지
                F.when(
                    condition,
                    # F.concat(F.col("_quality_flags"), F.array(F.lit(rule["id"])))는 
                    # 현재 행의 _quality_flags 배열 뒤에 현재 규칙 ID를 새 배열 항목으로 붙여서, 
                    # 어떤 warning 규칙들을 위반했는지 누적 기록하는 코드입니다.
                    F.concat(F.col("_quality_flags"), F.array(F.lit(rule["id"])))
                ).otherwise(F.col("_quality_flags"))
            )

        result = QualityResult(
            rule_id=rule["id"], rule_name=rule["name"],
            severity=rule["severity"], total_records=0,
            passed_records=passed_count, failed_records=failed_count,
            # pass_rate=passed_count / max(passed_count + failed_count, 1)는 통과율을 계산하는 식입니다. 
            # 전체 건수(passed + failed)로 나누되, 전체 건수가 0일 때 0으로 나누는 오류를 막기 위해 분모를 최소 1로 보장합니다.
            pass_rate=passed_count / max(passed_count + failed_count, 1),
        )
        return df, result

    @staticmethod
    def _check_completeness(df, rule, total_records: int) -> tuple:
        """필수 필드 null 체크"""
        fields = rule["fields"]

        # condition: 각 row에 대해 어떻게 True/False를 계산할지 정의한 Spark 표현식
        # 1번 레코드 -> True/False
        # 2번 레코드 -> True/False
        # 3번 레코드 -> True/False
        # ...
        # 10000번 레코드 -> True/False
        condition = F.lit(False)
        for field_name in fields:
            if field_name in df.columns:
                # 필수 필드 중 하나라도 null이면 실패라는 규칙이므로 OR 조건으로 누적
                condition = condition | F.col(field_name).isNull()

        return QualityChecker._apply_rule_result(df, rule, condition, total_records)

    @staticmethod
    def _check_uniqueness(df, rule, total_records: int) -> tuple:
        """중복 체크"""
        key_fields = rule["key_fields"] # key_fields: ["tx_id"]

        # 중복 건수 계산

        # groupBy(...).count()를 실행하면 Spark가 자동으로 count라는 이름의 컬럼을 만듭니다. 
        # 이 컬럼에는 각 그룹의 레코드 수가 들어갑니다. 
        # filter(F.col("count") > 1)을 통해 count가 1보다 큰 그룹, 즉 중복된 그룹만 남깁니다.
        dup_df = df.groupBy(key_fields).count().filter(F.col("count") > 1)
        # collect()[0][0]은 Spark 집계 결과를 파이썬으로 가져온 후, 
        # 첫 번째 행의 첫 번째 컬럼 값을 꺼내는 표현입니다. 즉 1행 1열 집계 결과에서 실제 숫자 하나만 추출할 때 자주 사용합니다.
        dup_count = dup_df.agg(F.sum(F.col("count") - 1)).collect()[0][0] or 0

        # 중복 제거: 최신 레코드 유지
        if rule.get("strategy") == "keep_latest":
            # Window 함수를 사용하여 각 그룹 내에서 kafka_timestamp 기준으로 내림차순 정렬한 후, 
            # row_number()를 통해 각 레코드에 순번을 매깁니다.
            w = Window.partitionBy(key_fields).orderBy(F.col("kafka_timestamp").desc())
            # row_number()가 1보다 큰 레코드는 중복 레코드이므로 _is_quarantined 플래그를 True로 설정하여 격리합니다.
            df = df.withColumn("_row_num", F.row_number().over(w))
            df = df.withColumn(
                "_is_quarantined",
                F.when(F.col("_row_num") > 1, True).otherwise(F.col("_is_quarantined"))
            )
            # 중복 레코드 식별을 위한 임시 컬럼 제거
            df = df.drop("_row_num")

        passed_count = total_records - int(dup_count)
        result = QualityResult(
            rule_id=rule["id"], rule_name=rule["name"],
            severity=rule["severity"], total_records=0, # total_records는 validate() 메서드에서 계산된 전체 레코드 수로 나중에 업데이트됩니다.
            passed_records=passed_count, failed_records=int(dup_count),
            pass_rate=passed_count / max(passed_count + int(dup_count), 1),
        )
        return df, result

    # 이 코드는 유효성 규칙의 형태에 따라 위반 조건식을 만드는 부분입니다. 
    # allowed_values가 있으면 허용값 목록 밖의 값을, 
    # min_value와 max_value가 있으면 범위를 벗어난 값을, 
    # min_value만 있으면 최솟값보다 작은 값을 위반으로 판단합니다. 조건이 없으면 모든 행을 정상으로 봅니다.
    @staticmethod
    def _check_validity(df, rule, total_records: int) -> tuple:
        """유효성 체크 (허용값 또는 범위)"""
        field_name = rule["field"] # field: "tx_type" field: "amount" field: "status"

        if "allowed_values" in rule:
            # isin()은 컬럼의 값이 allowed_values 배열에 포함되어 있는지 여부를 체크하는 Spark 함수입니다.
            # allowed_values에 없는 값이 위반이므로, isin() 결과에 NOT 연산을 적용하여 condition을 만듭니다.
            # 각 레코드마다 True 또는 False로 평가되는 Spark 조건식입니다.
            condition = ~F.col(field_name).isin(rule["allowed_values"]) 
        # min_value와 max_value가 모두 있는 경우, 둘 중 하나라도 벗어나면 위반이므로 OR 조건으로 결합합니다.
        elif "min_value" in rule and "max_value" in rule:
            condition = (
                (F.col(field_name) < rule["min_value"]) |
                (F.col(field_name) > rule["max_value"])
            )
        # min_value만 있는 경우, min_value보다 작은 값이 위반입니다.
        elif "min_value" in rule:
            condition = F.col(field_name) < rule["min_value"]
        else:
            condition = F.lit(False)

        # null은 별도 규칙에서 처리하므로 여기서는 제외
        condition = condition & F.col(field_name).isNotNull()
        return QualityChecker._apply_rule_result(df, rule, condition, total_records)

    @staticmethod
    def _check_timeliness(df, rule, total_records: int, processing_date: str) -> tuple:
        """적시성 체크"""
        field_name = rule["field"]
        max_delay = rule["max_delay_hours"]
        processing_dt = datetime.fromisoformat(f"{processing_date}T23:59:59")
        cutoff = processing_dt - timedelta(hours=max_delay)

        condition = (
            (F.col(field_name) < F.lit(cutoff)) & 
            F.col(field_name).isNotNull()
        )
        return QualityChecker._apply_rule_result(df, rule, condition, total_records)
