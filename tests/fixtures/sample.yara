rule Hello {
    strings:
        $g = "Hello"
    condition:
        $g
}
