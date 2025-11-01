# Copyright (c) 2025 Roman Drebotiy
# Licensed under the Apache License 2.0 (see LICENSE file)

import os
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
    def __init__(self, fname: str, fargs: list[float | dict[str, float]], command_counter: int):
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
    result = {}
    for i in range(len(params)):
        if isinstance(args[i], dict):
            for ind in args[i]:
                result[f"{params[i]}#{ind}"] = args[i][ind]
        else:
            result[params[i]] = args[i]
    return result


def get_val(var, mem: dict[str, float]) -> float | dict[str, float] | None:
    if "#" not in var:
        if get_array_len(var, mem) == 0:
            if var in mem:
                return mem[var]
            try:
                return float(var)
            except ValueError:
                return None
        arr_vals = {}
        for k in mem:
            if k.startswith(f"{var}#"):
                _, ind = k.split("#")
                arr_vals[ind] = mem[k]
        return arr_vals
    parts = var.split("#")
    indices = parts[1].split(":")
    indices_actual = ":".join([str(int(get_val(i, mem))) for i in indices])
    ind = f"{parts[0]}#{indices_actual}"
    if ind in mem:
        return mem[ind]
    return None


def set_val(var, mem: dict[str, float], val: float):
    if "#" not in var:
        mem[var] = float(val)
        return
    parts = var.split("#")
    indices = parts[1].split(":")
    indices_actual = ":".join([str(int(get_val(i, mem))) for i in indices])
    mem[f"{parts[0]}#{indices_actual}"] = float(val)


def get_array_len(var, mem: dict[str, float]) -> int | list[int]:
    max_ind = []
    for k in mem:
        if k.startswith(f"{var}#"):
            _, ind = k.split("#")
            indices = [int(i) for i in ind.split(":")]
            if not max_ind:
                max_ind = indices
            else:
                max_ind = [max(indices[i], max_ind[i]) for i in range(len(max_ind))]
    if len(max_ind) > 1:
        return max_ind
    if len(max_ind) == 1:
        return max_ind[0]
    return 0


def get_output(var: str, curr: StackFrame) -> str:
    val = get_val(var, curr.local_vars)
    output = ""
    if isinstance(val, dict):
        arr_len = get_array_len(var, curr.local_vars)
        if isinstance(arr_len, int):
            arr_len = [arr_len]
        if len(arr_len) == 1:
            row = ""
            for j in range(1, arr_len[0] + 1):
                v = val.get(f"{j}")
                row += f"{v:5.2f} " if v else "    _"
            output += f"{row}\n"
        elif len(arr_len) == 2:
            for i in range(1, arr_len[0] + 1):
                row = ""
                for j in range(1, arr_len[1] + 1):
                    v = val.get(f"{i}:{j}")
                    row += f"{v:5.2f} " if v else "    _"
                output += f"{row}\n"
        else:
            for ind in val:
                output += f"{var}#{ind} => {val[ind]}\n"
    else:
        output = f"{val}"
    return output

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
            val = float(input(f"provide float value for variable [{cm[1]}] >> "))
            set_val(cm[1], curr.local_vars, val)
        elif cm[0] == "FREAD":
            path = cm[2].replace("\\", os.sep)
            with open(path, "r") as f:
                lines = f.readlines()
            arr = [[float(el) for el in l.strip().split()] for l in lines if l]
            if len(arr) == 1:
                if len(arr[0]) == 1:
                    set_val(cm[1], curr.local_vars, arr[0][0])
                else:
                    for i in range(len(arr[0])):
                        set_val(f"{cm[1]}#{i+1}", curr.local_vars, arr[0][i])
            elif len(arr) > 1:
                for i in range(len(arr)):
                    for j in range(len(arr[i])):
                        set_val(f"{cm[1]}#{i+1}:{j+1}", curr.local_vars, arr[i][j])
        elif cm[0] == "WRITE":
            print(get_output(cm[1], curr))
        elif cm[0] == "FWRITE":
            path = cm[2].replace("\\", os.sep)
            output = get_output(cm[1], curr)
            with open(path, "w") as f:
                f.write(output)
        elif cm[0] == "TEXT":
            print(cm[1].replace("_", " "))
        elif cm[0] == "LEN":
            arr_len = get_array_len(cm[1], curr.local_vars)
            if isinstance(arr_len, list):
                for i in range(len(arr_len)):
                    set_val(f"{cm[2]}#{i+1}", curr.local_vars, arr_len[i])
            else:
                set_val(cm[2], curr.local_vars, arr_len)
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
            cond_val = get_val(cm[1], curr.local_vars)
            if cond_val is None or (isinstance(cond_val, float) and cond_val < 0):
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
                        if isinstance(res, dict):
                            for ind in res:
                                set_val(f"{caller_res_var}#{ind}", call_stack[-2].local_vars, res[ind])
                        else:
                            set_val(caller_res_var, call_stack[-2].local_vars, res)
                call_stack[-2].command_counter += 1
            call_stack.pop()
            break
        curr.command_counter += 1
    if curr.command_counter > funcs[curr.fname].end_pos:
        if len(call_stack) > 1:
            call_stack[-2].command_counter += 1
        call_stack.pop()
