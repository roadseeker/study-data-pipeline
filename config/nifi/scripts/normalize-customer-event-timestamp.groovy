import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import org.apache.nifi.processor.io.StreamCallback
import java.nio.charset.StandardCharsets
import java.time.LocalDateTime
import java.time.ZoneId
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

def flowFile = session.get()
if (!flowFile) return

// Assumption:
// The PostgreSQL updated_at value is interpreted as UTC.
// If the source DB stores local Korea time, change SOURCE_ZONE to ZoneId.of("Asia/Seoul").
def SOURCE_ZONE = ZoneId.of("UTC")
def INPUT_FORMATS = [
    DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSSSSS"),
    DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")
]

try {
    flowFile = session.write(flowFile, { inputStream, outputStream ->
        def json = new JsonSlurper().parse(
            inputStream.newReader(StandardCharsets.UTF_8.name())
        )

        if (json.event_timestamp instanceof String) {
            def rawTimestamp = json.event_timestamp
            LocalDateTime parsed = null

            for (formatter in INPUT_FORMATS) {
                try {
                    parsed = LocalDateTime.parse(rawTimestamp, formatter)
                    break
                } catch (Exception ignored) {
                    // Try the next format.
                }
            }

            if (parsed != null) {
                json.event_timestamp = parsed
                    .atZone(SOURCE_ZONE)
                    .withZoneSameInstant(ZoneOffset.UTC)
                    .format(DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'"))
            }
        }

        outputStream.write(
            JsonOutput.toJson(json).getBytes(StandardCharsets.UTF_8)
        )
    } as StreamCallback)

    flowFile = session.putAttribute(flowFile, "event_timestamp.normalized", "true")
    session.transfer(flowFile, REL_SUCCESS)
} catch (Exception e) {
    log.error("DB event_timestamp UTC 정규화 실패", e)
    session.transfer(flowFile, REL_FAILURE)
}
