case class Greeting(name: String, age: Int)

object Main {
  def greet(g: Greeting): String =
    s"Hello, ${g.name}! You are ${g.age} years old."

  @main def main(): Unit =
    val g = Greeting("World", 25)
    println(greet(g))
}
