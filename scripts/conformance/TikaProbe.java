import java.io.BufferedReader;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.List;
import java.util.stream.Collectors;
import org.apache.tika.detect.DefaultDetector;
import org.apache.tika.io.TikaInputStream;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.TikaCoreProperties;
import org.apache.tika.mime.MimeTypes;

/** Strict UTF-8 TSV protocol; variable text is Base64, including full errors. */
public class TikaProbe {
    private static String encode(String value) {
        return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    public static void main(String[] args) throws Exception {
        System.setOut(new PrintStream(System.out, true, StandardCharsets.UTF_8));
        if (args.length != 1) {
            throw new IllegalArgumentException("expected manifest path");
        }
        System.out.println("runtime\t" + encode(System.getProperty("java.version"))
            + "\t" + encode(System.getProperty("java.runtime.version"))
            + "\t" + encode(System.getProperty("java.vendor")));
        DefaultDetector detector = new DefaultDetector();
        MimeTypes repository = MimeTypes.getDefaultMimeTypes();
        try (BufferedReader reader = Files.newBufferedReader(Path.of(args[0]), StandardCharsets.UTF_8)) {
            String line;
            while ((line = reader.readLine()) != null) {
                String[] fields = line.split("\t", -1);
                if (fields.length != 2 || fields[0].isEmpty() || fields[1].isEmpty()) {
                    throw new IllegalArgumentException("malformed manifest row");
                }
                String id = fields[0];
                Path path = Path.of(fields[1]);
                for (String mode : List.of("content", "named", "wrong_pdf", "wrong_txt")) {
                    // Never reuse metadata: content detection must receive no filename hint.
                    Metadata metadata = new Metadata();
                    if (!mode.equals("content")) {
                        String name = mode.equals("named") ? path.getFileName().toString()
                            : mode.equals("wrong_pdf") ? "payload.pdf" : "payload.txt";
                        metadata.set(TikaCoreProperties.RESOURCE_NAME_KEY, name);
                    }
                    long start = System.nanoTime();
                    try (TikaInputStream input = TikaInputStream.get(path)) {
                        String mime = detector.detect(input, metadata).toString();
                        String extensions = repository.forName(mime).getExtensions().stream()
                            .map(TikaProbe::encode).collect(Collectors.joining(","));
                        System.out.println("observation\t" + id + "\t" + mode + "\tok\t"
                            + encode(mime) + "\t" + extensions + "\t\t"
                            + (System.nanoTime() - start));
                    } catch (Exception error) {
                        StringWriter trace = new StringWriter();
                        error.printStackTrace(new PrintWriter(trace));
                        System.out.println("observation\t" + id + "\t" + mode
                            + "\terror\t\t\t" + encode(trace.toString()) + "\t"
                            + (System.nanoTime() - start));
                    }
                }
            }
        }
    }
}
