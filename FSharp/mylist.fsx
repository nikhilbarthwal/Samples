open System.Collections.Generic

type ListBuilder() =
    member _.Yield(x) =
        let dotnetList = new List<_>()
        do dotnetList.Add(x)
        dotnetList
    member _.YieldFrom(list) = list
    member _.Zero() = new List<_>()
    member _.Combine(list1: List<_>, list2) =
        list1.AddRange(list2)
        list1 // 'return'
    member _.For(xs, body) =
        let list = new List<_>()
        for x in xs do
            list.Add(body x)
        list // 'return'

    member _.Delay(f) = f ()

let myList = ListBuilder()

// ------

// [1; 2]
myList {
    yield 1
    yield 2
}

// [1; 2]
myList {
    1    // 'yield'
    2    // 'yield'
}

// [1; 3]
myList {
    1      // 'yield'
    if false then
        2  // 'yield'
    3      // 'yield'
}

// [1; 2; 3; 4]
myList {
    1
    yield! myList {2; 3}
    4
}

// [2; 4; 6; 8]
myList {
    for i in 1..4 do
        yield i * 2
}

// [2; 3; 3; 4]
myList {
    for i in 1..2 do
        for j in 1..2 do
            i + j
}
