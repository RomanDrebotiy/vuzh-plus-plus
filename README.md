# Vuzh++

<img src="Vuzh++_logo.png" width="200">

A tiny compiled programming language created for student learning.

Source code is compiled to the intermediate low-level language, which is then interpreted by a virtual machine.

Supports:
- variables
- expressions
- loops
- conditional blocks
- functions
- arrays
- expression temporary variable number optimization
- input/output from the console
- only one type: float

## Compilation
Save your code in .vu file (for example in the same folder where compiler is located) and then pass it to the compiler:
```bash
python vuzh++compiler.py my_src_code.vu
```
It will create `my_src_code.vuc` file, which you can run on the VM:
```bash
python vuzh++vm.py my_src_code.vuc
```

**(!)** You can find some code sample in the repo to explore the syntax.

## Notes

Language is created for educational purposes.

Currently, it lacks error handling and syntax checks with hints.


*Copyright (c) 2025 Roman Drebotiy*

*Licensed under the Apache License 2.0 (see LICENSE file)*