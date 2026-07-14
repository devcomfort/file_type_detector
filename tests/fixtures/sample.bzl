def hello_library():
    native.genrule(
        name = "hello",
        outs = ["hello.txt"],
        cmd = "echo Hello > $@",
    )
