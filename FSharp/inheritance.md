**Original:**

```
class Base:
    protected F1
    protected F2
    public F3
    public F4

class DerivedA: Base
    public FA1
    public FA2

class DerivedB: Base
    public FB1
    public FB2
```
___

**New Design:**

```
interface BaseInput:
    public F1
    public F2

class Base(BaseInput):
    public F3
    public F4

internal DerivedInputA(p1, p2): BaseInput
    public FA1
    public FA2
    public F1
    public F2

internal DerivedInputB(q1, q2): BaseInput
    public FB1
    public FB2
    public F1
    public F2

class DerivedA(p1, p2):
    private input(p1, p2): DerivedInputA
    public FA1 = input.FA1
    public FA2 = input.FA2
    public property Base(input)
    // Add F3 and F4 if needed

class DerivedB(input: DerivedInputB)
    private input(p1, p2): DerivedInputB
    public FB1 = input.FB1
    public FB2 = input.FB2
    public property Base(input)
    // Add F3 and F4 if needed
```

