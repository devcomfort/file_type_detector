"""Pinned identity for the isolated Tika operating-system comparison."""

SCHEMA_VERSION = 1
EXPERIMENT = "tika-os-conformance"
TIKA_VERSION = "3.3.3"
TIKA_SHA512 = (
    "3c6e62e864e32af234832ec6d928bbc58692d3ddd60564cd8c80dee7e161653d6efc"
    "ba373b6cc9468c778010bea92bdee5ca75ab24f01923480bec1b29b573fd"
)
TIKA_URL = (
    "https://repo.maven.apache.org/maven2/org/apache/tika/tika-app/"
    f"{TIKA_VERSION}/tika-app-{TIKA_VERSION}.jar"
)
MODES = ("content", "named", "wrong_pdf", "wrong_txt")
