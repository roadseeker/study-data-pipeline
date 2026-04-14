import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import org.apache.nifi.processor.io.StreamCallback
import java.nio.charset.StandardCharsets
import java.time.LocalDate
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

def flowFile = session.get()
if (!flowFile) return

try {
    flowFile = session.write(flowFile, { inputStream, outputStream ->

        // 정산 원본 JSON에서 settlement_date 값을 읽어
        // UTC 기준 ISO 8601 문자열로 정규화한다.
        def json = new JsonSlurper().parse(
            inputStream.newReader(StandardCharsets.UTF_8.name())
        )

        if (json.settlement_date instanceof String &&
                json.settlement_date ==~ /\d{4}-\d{2}-\d{2}/) {
                    def date = LocalDate.parse(json.settlement_date)
                    json.settlement_date = date
                        .atStartOfDay(ZoneOffset.UTC)
                        .format(DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'"))
        }

        outputStream.write(
            JsonOutput.toJson(json).getBytes(StandardCharsets.UTF_8)
        )
    } as StreamCallback)

    flowFile = session.putAttribute(flowFile, "settlement_date.normalized", "true")
    session.transfer(flowFile, REL_SUCCESS)
} catch (Exception e) {
    log.error("settlement_date UTC 정규화 실패", e)
    session.transfer(flowFile, REL_FAILURE)
}
