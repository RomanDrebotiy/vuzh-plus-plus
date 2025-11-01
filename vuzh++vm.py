# Copyright (c) 2025 Roman Drebotiy
# Licensed under the Apache License 2.0 (see LICENSE file)

import sys
from pathlib import Path


fn = sys.argv[1]

if Path(fn).suffix != ".vuc":
    raise Exception("Please provide .vuc file")

with open(fn, "r") as f:
    commands = [c.strip().split() for c in f.readlines()]


class FuncDef:
    def __init__(self, fparams: list[str], start_pos: int, end_pos: int):
        self.fparams = fparams
        self.start_pos = start_pos
        self.end_pos = end_pos


class StackFrame:
    def __init__(self, fname: str, fargs: list, command_counter: int):
        self.fname = fname
        self.fargs = fargs
        self.local_vars = {}
        self.command_counter = command_counter
        self.called = False


def get_funcs() -> dict[str, FuncDef]:
    name = ""
    fparams = []
    start_pos = 0
    func_map = {}
    for i in range(len(commands)):
        cm = commands[i]
        if cm[0] not in ["FUNC", "ENDFUNC"]:
            continue
        if cm[0] == "FUNC":
            name = cm[1]
            fparams = cm[2:]
            start_pos = i + 1
        if cm[0] == "ENDFUNC":
            func_map[name] = FuncDef(
                fparams=fparams,
                start_pos=start_pos,
                end_pos=i-1
            )
    return func_map


funcs = get_funcs()


if "main" not in funcs:
    raise Exception("main function is not defined")


call_stack = [
    StackFrame(
        fname="main",
        fargs=[],
        command_counter=funcs["main"].start_pos
    )
]


def prepare_args(params: list[str], args: list):
    if len(params) != len(args):
        raise Exception("Wrong param list")
    return {
        params[i]: args[i]
        for i in range(len(params))
    }


def get_val(var, mem: dict[str, float]):
    if "#" not in var:
        return mem[var] if var in mem else float(var)
    parts = var.split("#")
    return mem[f"{parts[0]}#{int(get_val(parts[1], mem))}"]


def set_val(var, mem: dict[str, float], val: float):
    if "#" not in var:
        mem[var] = float(val)
        return
    parts = var.split("#")
    mem[f"{parts[0]}#{int(get_val(parts[1], mem))}"] = float(val)


def get_array_len(var, mem: dict[str, float]) -> int:
    max_ind = 0
    for k in mem:
        if k.startswith(f"{var}#"):
            _, ind = k.split("#")
            max_ind = max(int(ind), max_ind)
    return int(max_ind)


def arithmetic_op(op: str, arg1: float, arg2: float) -> float:
    return {
        "ADD": lambda x, y: x + y,
        "SUB": lambda x, y: x - y,
        "MUL": lambda x, y: x * y,
        "DIV": lambda x, y: x / y
    }.get(op)(arg1, arg2)


while len(call_stack) > 0:
    curr = call_stack[-1]
    if not curr.called:
        curr.local_vars = prepare_args(funcs[curr.fname].fparams, curr.fargs)
    curr.called = True
    while curr.command_counter <= funcs[curr.fname].end_pos:
        cm = commands[curr.command_counter]
        if cm[0] == "READ":
            val = float(input(f"type {cm[1]} >> "))
            set_val(cm[1], curr.local_vars, val)
        elif cm[0] == "WRITE":
            print(get_val(cm[1], curr.local_vars))
        elif cm[0] == "TEXT":
            print(cm[1].replace("_", " "))
        elif cm[0] == "LEN":
            set_val(cm[2], curr.local_vars, get_array_len(cm[1], curr.local_vars))
        elif cm[0] == "COPY":
            set_val(cm[2], curr.local_vars, get_val(cm[1], curr.local_vars))
        elif cm[0] in ["ADD", "SUB", "MUL", "DIV"]:
            set_val(cm[3], curr.local_vars, arithmetic_op(
                cm[0],
                get_val(cm[1], curr.local_vars),
                get_val(cm[2], curr.local_vars)
            ))
        elif cm[0] == "GOTO":
            curr.command_counter = int(cm[1])
            continue
        elif cm[0] == "GOTOIFNOT":
            if get_val(cm[1], curr.local_vars) < 0:
                curr.command_counter = int(cm[2])
                continue
        elif cm[0] == "CALL":
            args = cm[2: -1]
            call_stack.append(
                StackFrame(
                    fname=cm[1],
                    fargs=[get_val(arg, curr.local_vars) for arg in cm[2: -1]],
                    command_counter=funcs[cm[1]].start_pos
                )
            )
            break
        elif cm[0] == "RETURN":
            if len(call_stack) > 1:
                if len(cm) > 1:
                    res = get_val(cm[1], curr.local_vars)
                    caller_res_var = commands[call_stack[-2].command_counter][-1]
                    if caller_res_var != "_":
                        set_val(caller_res_var, call_stack[-2].local_vars, res)
                call_stack[-2].command_counter += 1
            call_stack.pop()
            break
        curr.command_counter += 1
    if curr.command_counter > funcs[curr.fname].end_pos:
        if len(call_stack) > 1:
            call_stack[-2].command_counter += 1
        call_stack.pop()
