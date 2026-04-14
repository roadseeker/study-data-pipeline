import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.time.OffsetDateTime
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

def flowFile = session.get()
if (!flowFile) return

try {
    // 읽기
    def is = session.read(flowFile)
    def jsonBytes
    try {
        jsonBytes = is.bytes
    } finally {
        is.close()
    }

    // 변환: "2026-04-14T13:03:10.713212+00:00" → "2026-04-14T13:03:10Z"
    def json = new JsonSlurper().parse(jsonBytes)
    def raw = json.timestamp?.toString()?.trim()

    if (raw) {
        try {
            json.timestamp = OffsetDateTime
                .parse(raw, DateTimeFormatter.ISO_OFFSET_DATE_TIME)
                .atZoneSameInstant(ZoneOffset.UTC)
                .format(DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'"))
        } catch (Exception inner) {
            log.warn("timestamp 파싱 실패: ${raw} → ${inner.message}")
        }
    }

    // 쓰기
    def os = session.write(flowFile)
    try {
        os.write(JsonOutput.toJson(json).getBytes("UTF-8"))
    } finally {
        os.close()
    }

    session.transfer(flowFile, REL_SUCCESS)

} catch (Exception e) {
    log.error("timestamp UTC 정규화 실패", e)
    session.transfer(flowFile, REL_FAILURE)
}
