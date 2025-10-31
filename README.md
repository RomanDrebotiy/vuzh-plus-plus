# Vuzh++ programming language

<div align="center">
  <img src="Vuzh++_logo.png" width="200">
</div>

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
Save your code in `.vu` file (for example in the same folder where compiler is located) and then pass it to the compiler:
```bash
python vuzh++compiler.py my_src_code.vu
```
It will create `my_src_code.vuc` file, which you can run on the VM:
```bash
python vuzh++vm.py my_src_code.vuc
```

**(!)** You can find some code sample in the repo to explore the syntax.

## Syntax highlighting in VS Code

There is extension available in the folder `vsc_syntax_highlighting_extension`. For the simplest case just execute command to run VS Code with provided full path to that folder. For example on Windows:
```bash
code --extensionDevelopmentPath="<FULL_PATH_TO_THIS_FOLDER>\vsc_syntax_highlighting_extension"
```

## Notes

Language is created for educational purposes.

Currently, it lacks error handling and syntax checks with hints.


*Copyright (c) 2025 Roman Drebotiy*

*Licensed under the Apache License 2.0 (see LICENSE file)*