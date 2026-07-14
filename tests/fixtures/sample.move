module sample::hello {
    public fun greet(): String {
        string::utf8(b"Hello")
    }
}
