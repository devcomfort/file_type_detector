# Sample Ruby file
class Greeting
  attr_reader :name, :age

  def initialize(name, age)
    @name = name
    @age = age
  end

  def message
    "Hello, #{@name}! You are #{@age} years old."
  end
end

g = Greeting.new("World", 25)
puts g.message
