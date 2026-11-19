import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Base64;
import java.util.stream.Collectors;
import org.apache.tika.detect.DefaultDetector;
import org.apache.tika.io.TikaInputStream;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.TikaCoreProperties;
import org.apache.tika.mime.MimeTypes;

/**
 * Interactive file-type probe for TikaInferencer.
 *
 * <p>Reads one file path per line from stdin, detects each file with its real
 * filename as the metadata hint, and writes one Base64 TSV line per request:
 * {@code ok\tmime\text1,ext2} or {@code error\tstacktrace}. Stdout is UTF-8.
 * The JVM stays alive so callers pay startup cost once.
 */
public class TikaDetect {
    private static String encode(String value) {
        return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    public static void main(String[] args) throws Exception {
        System.setOut(new PrintStream(System.out, true, StandardCharsets.UTF_8));
        DefaultDetector detector = new DefaultDetector();
        MimeTypes repository = MimeTypes.getDefaultMimeTypes();
        BufferedReader reader =
            new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String line;
        while ((line = reader.readLine()) != null) {
            Path path = Path.of(line);
            Metadata metadata = new Metadata();
            metadata.set(TikaCoreProperties.RESOURCE_NAME_KEY, path.getFileName().toString());
            try (TikaInputStream input = TikaInputStream.get(path)) {
                String mime = detector.detect(input, metadata).toString();
                String extensions = repository.forName(mime).getExtensions().stream()
                    .collect(Collectors.joining(","));
                System.out.println("ok\t" + encode(mime) + "\t" + encode(extensions));
            } catch (Exception error) {
                StringWriter trace = new StringWriter();
                error.printStackTrace(new PrintWriter(trace));
                System.out.println("error\t" + encode(trace.toString()));
            }
            System.out.flush();
        }
    }
}
