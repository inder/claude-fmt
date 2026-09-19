| Feature | `var` | `let` | `const` |
| --- | --- | --- | --- |
| Scope | Function | Block `{}` | Block `{}` |
| Hoisting | Hoisted, initialized to `undefined` | Hoisted, but in the Temporal Dead Zone (TDZ) until declared | Hoisted, but in the TDZ until declared |
| Re-declare in same scope | ✅ Allowed | ❌ SyntaxError | ❌ SyntaxError |
| Re-assign | ✅ Allowed | ✅ Allowed | ❌ TypeError |
| Must initialize at declaration | No | No | Yes |
| Creates global object property (top level) | Yes (`window.x`) | No | No |
| Loop closure behavior | One shared binding | New binding per iteration | New binding per iteration (e.g. `for...of`) |

| Example | Demonstrates |
| --- | --- |
| 1 | Scope |
| 2 | Hoisting / TDZ |
| 3 | Re-declaration and re-assignment |
| 4 | `const` objects are still mutable |
| 5 | Loop closures |

```js
// 1. Scope
function scopeDemo() {
  if (true) {
    var a = 1;
    let b = 2;
    const c = 3;
  }
  console.log(a); // 1: var ignores the block
  console.log(b); // ReferenceError: b is not defined
}

// 2. Hoisting / TDZ
console.log(x); // undefined
var x = 5;

console.log(y); // ReferenceError: Cannot access 'y' before initialization
let y = 5;

// 3. Re-declaration & re-assignment
var v = 1; var v = 2;     // OK
let l = 1; // let l = 2;  // SyntaxError: Identifier 'l' has already been declared
l = 2;                    // OK
const k = 1;
// k = 2;                 // TypeError: Assignment to constant variable
// const z;               // SyntaxError: Missing initializer in const declaration

// 4. const prevents rebinding, not mutation
const user = { name: "Ada" };
user.name = "Grace";      // OK, the object itself is mutable
// user = {};             // TypeError
Object.freeze(user);      // use this if you need immutability

// 5. Loop closures
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i)); // 3, 3, 3
for (let j = 0; j < 3; j++) setTimeout(() => console.log(j)); // 0, 1, 2
```

Rule of thumb: use `const` by default, use `let` when you need to reassign, and avoid `var`.
