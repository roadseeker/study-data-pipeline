import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import org.apache.nifi.processor.io.StreamCallback
import java.nio.charset.StandardCharsets
import java.util.TimeZone

def flowFile = session.get()
if (!flowFile) return

try {
    flowFile = session.write(flowFile, { inputStream, outputStream ->

        // JSON 데이터를 읽어들이고 event_timestamp 필드가 "yyyy-MM-dd" 형식의 문자열인 경우 
        // UTC 시간으로 변환하여 ISO 8601 형식으로 저장으로 변경
        def json = new JsonSlurper().parse(
            inputStream.newReader(StandardCharsets.UTF_8.name())
        )

        if (json.event_timestamp instanceof String &&
                json.event_timestamp ==~ /\d{4}-\d{2}-\d{2}/) {
                    def date = Date.parse("yyyy-MM-dd", json.event_timestamp)
                    json.event_timestamp = date.format(
                        "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        TimeZone.getTimeZone("UTC")
                    )
        }

        outputStream.write(
            JsonOutput.toJson(json).getBytes(StandardCharsets.UTF_8)
        )
    } as StreamCallback)

    flowFile = session.putAttribute(flowFile, "event_timestamp.normalized", "true")
    session.transfer(flowFile, REL_SUCCESS)
} catch (Exception e) {
    log.error("event_timestamp UTC 정규화 실패", e)
    session.transfer(flowFile, REL_FAILURE)
}
