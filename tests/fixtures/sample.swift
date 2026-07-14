import Foundation

struct Greeting {
    let name: String
    let age: Int
    
    func message() -> String {
        return "Hello, \(name)! You are \(age) years old."
    }
}

let g = Greeting(name: "World", age: 25)
print(g.message())
