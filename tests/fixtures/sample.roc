app "sample"
    packages { pf: "https://github.com/roc-lang/basic-cli/releases/download/0.10.0/vKjCoDzYFP.zip" }
    imports [pf.Stdout]
    provides [main] to pf

main = Stdout.line "Hello"
