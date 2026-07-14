// Sample TypeScript file
interface Greeting {
    name: string;
    age: number;
}

function greet({ name, age }: Greeting): string {
    return `Hello, ${name}! You are ${age} years old.`;
}

const user: Greeting = { name: 'World', age: 25 };
console.log(greet(user));
