# Copyright (c) 2025 Roman Drebotiy
# Licensed under the Apache License 2.0 (see LICENSE file)

from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description="Vuzh++ compiler")

parser.add_argument(
    "input",
    help="Full path to the .vu file"
)

parser.add_argument(
    "output",
    nargs="?",
    help="Full path to the output .vuc file (optional)"
)

parser.add_argument(
    "--tail",
    action="store_true",
    help="Enable tail recursion optimization"
)

args = parser.parse_args()

fn = args.input
fn_out = args.output if args.output is not None else f"{fn}c"

TAIL_RECURSION_OPTIMIZATION_ENABLED = args.tail


if Path(fn).suffix != ".vu":
    raise Exception("Input file should have .vu extension")

if Path(fn_out).suffix != ".vuc":
    raise Exception("Output file should have .vuc extension")


with open(fn, "r") as f:
    lines = f.readlines()

src = "".join([l for l in lines if not l.strip().startswith("//")])

for s in ["\n", " ", "\t"]:
    src = src.replace(s, "")


def tokenize():
    start = 0
    pos = 0
    res = []
    markers = list(";,>=+-*/()[]{}")
    while pos < len(src):
        if src[pos] in markers:
            if start != pos:
                res.append(src[start:pos])
            res.append(src[pos])
            start = pos + 1
        pos += 1
    return res


tokens = tokenize()
ind = 0
commands = []


class Node:
    def __init__(self, token, res_var, l=None, r=None):
        self.token = token
        self.res_var = res_var
        self.l = l
        self.r = r
        self.mark = 0
        self.inverse = False


def priority(t: str) -> int:
    return {
        "+": 1,
        "-": 1,
        "*": 2,
        "/": 2
    }.get(t, -1)


def get_command(l, r, o, res):
    cmd = {
        "+": "ADD",
        "-": "SUB",
        "*": "MUL",
        "/": "DIV"
    }.get(o)

    return f"{cmd} {l} {r} {res}"


def is_op(t: str) -> bool:
    return priority(t) > 0


def gen_comm(args, ops, cnt):
    rhs = args.pop()
    lhs = args.pop()
    op = ops.pop()
    tmp = f"t{cnt}"
    args.append(Node(op, tmp, lhs, rhs))


def compile_expr_to_tree():
    global ind
    ops = []
    args = []
    cnt = 0
    while tokens[ind] not in [";", "]"]:
        token = tokens[ind]
        if is_op(token):
            while len(ops) > 0 and is_op(ops[-1]) and priority(ops[-1]) > priority(token):
                gen_comm(args, ops, cnt)
                cnt += 1
            ops.append(token)
        elif token == "(":
            ops.append(token)
        elif token == ")":
            while len(ops) > 0 and ops[-1] != "(":
                gen_comm(args, ops, cnt)
                cnt += 1
            ops.pop()
        else:
            args.append(Node(token, token))
        ind += 1
    while len(ops) > 0:
        gen_comm(args, ops, cnt)
        cnt += 1
    return args[0]


def mark_tree(root: Node):
    if not root.l:
        return
    mark_tree(root.l)
    mark_tree(root.r)
    root.mark = max(root.l.mark, root.r.mark)\
        if root.l.mark != root.r.mark\
        else root.l.mark + 1


def assign_vars(root: Node, vars: list[str]):
    if not root.l:
        return
    if root.l.mark == root.r.mark:
        assign_vars(root.l, vars[1:])
        assign_vars(root.r, vars[:-1])
    else:
        if root.l.mark < root.r.mark:
            root.l, root.r = root.r, root.l
            root.inverse = True
        assign_vars(root.l, vars)
        assign_vars(root.r, vars[:root.r.mark])
    root.res_var = vars[-1]


def optimize_tree(tree: Node):
    mark_tree(tree)
    tmp_vars = [f"t{i}" for i in range(tree.mark)]
    assign_vars(tree, tmp_vars)
    return tree


def convert_tree_to_cmd_list(root):
    if not root.l:
        return
    convert_tree_to_cmd_list(root.l)
    convert_tree_to_cmd_list(root.r)
    l, r = root.l.res_var, root.r.res_var
    if root.inverse:
        l, r = r, l
    commands.append(get_command(l, r, root.token, root.res_var))


def is_const_operator_condition():
    if tokens[ind+1] == "]":
        try:
            float(tokens[ind])
            return True
        except Exception:
            return False
    return False


def handle_operator():
    global ind
    is_loop = tokens[ind] == "while"
    loop_return_pos = len(commands)
    ind += 2
    if is_const_operator_condition():
        res_var = tokens[ind]
        ind += 3
    else:
        res_var = handle_expression()
        ind += 2
    gotoifnot_pos = len(commands)
    commands.append(f"GOTOIFNOT {res_var} _")
    handle_block()
    ind += 1
    if is_loop:
        commands.append(f"GOTO {loop_return_pos}")
    commands[gotoifnot_pos] = commands[gotoifnot_pos].replace("_", str(len(commands)))


def handle_call_command(res_var: str = None):
    global ind
    delta = 2 if res_var else 0
    func_name = tokens[ind + 2 + delta]
    start_args = end_args = ind + 4 + delta
    while tokens[end_args] != ")":
        end_args += 1
    func_args = "".join(tokens[start_args:end_args]).replace(",", " ")
    commands.append(f"CALL {func_name} {func_args} {res_var or '_'}")
    ind = end_args + 2


def handle_command():
    global ind
    if tokens[ind] in ["fread", "fwrite"]:
        commands.append(f"{tokens[ind].upper()} {tokens[ind+2]} {tokens[ind+4]}")
        ind += 6
    elif tokens[ind] in ["read", "write", "text"]:
        commands.append(f"{tokens[ind].upper()} {tokens[ind+2]}")
        ind += 4
    elif tokens[ind] == "return":
        if tokens[ind+2] == ";":
            commands.append(f"{tokens[ind].upper()}")
            ind += 3
        else:
            commands.append(f"{tokens[ind].upper()} {tokens[ind+2]}")
            ind += 4
    elif tokens[ind] == "call":
        handle_call_command()
    elif tokens[ind+2] == "call":
        res_var = tokens[ind]
        handle_call_command(res_var)
    elif tokens[ind+2] == "len":
        commands.append(f"{tokens[ind+2].upper()} {tokens[ind + 4]} {tokens[ind]}")
        ind += 6
    elif tokens[ind+3] == ";":
        commands.append(f"COPY {tokens[ind+2]} {tokens[ind]}")
        ind += 4
    else:
        res_var = tokens[ind]
        ind += 2
        handle_expression(res_var)
        ind += 1


def handle_expression(res_var: str = None) -> str:
    tree = compile_expr_to_tree()
    tree = optimize_tree(tree)
    convert_tree_to_cmd_list(tree)
    if res_var:
        parts = commands[-1].split()
        parts[-1] = res_var
        commands[-1] = " ".join(parts)
        return res_var
    return commands[-1].split()[-1]


def is_tail_recursion(func_name: str, func_start_pos: int):
    last_cmd = commands[-1].strip().split(" ")
    prev_cmd = commands[-2].strip().split(" ")
    tail = ((last_cmd[0] == "CALL" and last_cmd[1] == func_name)
            or (prev_cmd[0] == "CALL" and prev_cmd[1] == func_name
                and last_cmd[0] == "RETURN" and last_cmd[-1] == prev_cmd[-1]))
    if not tail:
        return False

    cnt = 0
    for i in range(func_start_pos, len(commands)):
        cmd = commands[i].strip().split(" ")
        if cmd[0] == "CALL" and cmd[1] == func_name:
            cnt += 1

    return cnt == 1


def handle_tail_recursion(func_name: str, func_args: str, func_body_start_pos: int):
    global commands
    call_cmd_ind = -1 if commands[-1].startswith("CALL") else -2
    call_cmd = commands[call_cmd_ind]
    commands = commands[:call_cmd_ind]
    if len(func_args) > 0:
        formal_args = func_args.split(" ")
        actual_args = call_cmd.split(" ")[2:-1]
        if len(formal_args) != len(actual_args):
            raise Exception(f"{func_name} call signature mismatch!")
        for actual, formal in zip(actual_args, formal_args):
            if actual != formal:
                commands.append(f"COPY {actual} {formal}")
    commands.append(f"GOTO {func_body_start_pos}")


def handle_function():
    global ind, commands
    start_args = end_args = ind + 4
    while tokens[end_args] != ")":
        end_args += 1
    func_args = "".join(tokens[start_args:end_args]).replace(",", " ").strip()
    func_name = tokens[ind+2]
    commands.append(f"FUNC {func_name} {func_args}")
    func_body_start_pos = len(commands)
    ind = end_args + 2
    handle_block()
    ind += 1
    if TAIL_RECURSION_OPTIMIZATION_ENABLED and is_tail_recursion(func_name, func_body_start_pos):
        handle_tail_recursion(func_name, func_args, func_body_start_pos)
    commands.append("ENDFUNC")


def handle_block():
    while ind < len(tokens):
        tk = tokens[ind]
        if tk == "}":
            break
        if tk in ["if", "while"]:
            handle_operator()
        elif tk == "func":
            handle_function()
        else:
            handle_command()


handle_block()


with open(fn_out, "w") as f:
    f.write("\n".join(commands))

print("Vuzh++: compilation finished.")