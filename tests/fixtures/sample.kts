data class Greeting(val name: String, val age: Int)

fun greet(g: Greeting): String {
    return "Hello, ${g.name}! You are ${g.age} years old."
}

fun main() {
    val g = Greeting("World", 25)
    println(greet(g))
}
