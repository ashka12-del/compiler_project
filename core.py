from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Result:
    success: bool
    mode: str
    output: str


ROOT = Path(__file__).resolve().parent


def _validate_with_bison(source: str, parser_name: str, suffix: str) -> tuple[bool, str]:
    parser = ROOT / "bin" / parser_name
    if not parser.exists():
        return False, f"[Toolchain] Missing {parser.name}. Run build_parsers.bat first.\n"
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as handle:
        handle.write(source)
        source_path = Path(handle.name)
    try:
        checked = subprocess.run([str(parser), str(source_path)], capture_output=True, text=True)
        return checked.returncode == 0, checked.stdout + checked.stderr
    finally:
        source_path.unlink(missing_ok=True)


def detect_mode(source: str, filename: str | Path = "") -> str:
    path = Path(filename) if filename else None
    if path and path.suffix.lower() == ".sql":
        return "MiniSQL"
    if re.search(r"\bquery\s*\"", source, re.I):
        return "Embedded C+SQL"
    if re.match(r"\s*SELECT\b", source, re.I):
        return "MiniSQL"
    return "MiniC"


def _compare(left: str, operator: str, right: str) -> bool:
    right = right.strip().rstrip(";").strip("\"'")
    try:
        a, b = float(left), float(right)
    except ValueError:
        a, b = left, right
    return {"=": a == b, "==": a == b, "!=": a != b, "<>": a != b,
            ">": a > b, "<": a < b, ">=": a >= b, "<=": a <= b}[operator]


def run_sql(sql: str, source_file: Path) -> tuple[bool, str, int]:
    match = re.fullmatch(
        r"\s*SELECT\s+(.+?)\s+FROM\s+([A-Za-z_]\w*)\s+WHERE\s+"
        r"([A-Za-z_]\w*)\s*(>=|<=|!=|<>|==|=|>|<)\s*(.+?)\s*;?\s*",
        sql, re.I | re.S,
    )
    if not match:
        return False, "[MiniSQL parser] line 1: expected SELECT <column> FROM <table> WHERE <column> <op> <value>;\n", 0
    projection, table, condition_column, operator, wanted = map(str.strip, match.groups())
    csv_path = source_file.parent / f"{table}.csv"
    if not csv_path.exists():
        return False, f"[MiniSQL runtime] table file not found: {csv_path}\n", 0
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or condition_column not in rows[0]:
        return False, f"[MiniSQL semantic] unknown column: {condition_column}\n", 0
    aggregate = re.fullmatch(r"SUM\s*\(\s*([A-Za-z_]\w*)\s*\)", projection, re.I)
    projected = aggregate.group(1) if aggregate else projection
    if projected not in rows[0]:
        return False, f"[MiniSQL semantic] unknown column: {projected}\n", 0
    selected = [row for row in rows if _compare(row[condition_column], operator, wanted)]
    plan = f"[MiniSQL] Plan: SCAN {table} -> FILTER {condition_column} {operator} {wanted.rstrip(';')} -> PROJECT {projection}\n"
    if aggregate:
        total = sum(int(float(row[projected])) for row in selected)
        return True, plan + f"SUM({projected}) = {total}\n", total
    values = "\n".join(row[projected] for row in selected)
    return True, plan + f"{projected}\n--------------------\n{values}\n({len(selected)} rows)\n", 0


def _compile_minic(source: str, run: bool, mode: str) -> Result:
    valid, parser_output = _validate_with_bison(source, "minic_parser.exe", ".mc")
    if not valid:
        return Result(False, mode, parser_output)
    def translate_print(match: re.Match) -> str:
        value = match.group(1).strip()
        if re.fullmatch(r'"(?:\\.|[^"\\])*"', value):
            return f'printf("%s\\n", {value});'
        return f'printf("%d\\n", (int)({value}));'
    translated = re.sub(r"\bprint\s*\(([^;]+)\)\s*;", translate_print, source)
    c_source = "#include <stdio.h>\n" + translated
    build_dir = Path(tempfile.gettempdir()) / "minic_minisql_editor"
    build_dir.mkdir(exist_ok=True)
    c_file, exe_file = build_dir / "program.c", build_dir / "program.exe"
    c_file.write_text(c_source, encoding="utf-8")
    built = subprocess.run(["gcc", "-std=c11", "-Wall", str(c_file), "-o", str(exe_file)], capture_output=True, text=True)
    if built.returncode:
        return Result(False, mode, "[MiniC code generator]\n" + built.stdout + built.stderr)
    output = parser_output + "[MiniC] Semantic -> IR -> Codegen: successful\n"
    if not run:
        return Result(True, mode, output + f"Executable: {exe_file}\n")
    executed = subprocess.run([str(exe_file)], capture_output=True, text=True)
    return Result(executed.returncode == 0, mode, output + "[Program output]\n" + executed.stdout + executed.stderr)


def compile_or_run(source: str, filename: str | Path, run: bool = True) -> Result:
    source_file = Path(filename)
    mode = detect_mode(source, source_file)
    if mode == "MiniSQL":
        valid, parser_output = _validate_with_bison(source, "minisql_parser.exe", ".sql")
        if not valid:
            return Result(False, mode, "[Detector] MiniSQL\n" + parser_output)
        ok, output, _ = run_sql(source, source_file)
        return Result(ok, mode, "[Detector] MiniSQL\n" + parser_output + output)
    if mode == "Embedded C+SQL":
        embedded = re.search(r'query\s*"([\s\S]*?)"\s*into\s+([A-Za-z_]\w*)\s*;', source, re.I)
        if not embedded:
            return Result(False, mode, '[Embedded parser] expected query "..." into variable;\n')
        valid, parser_output = _validate_with_bison(embedded.group(1), "minisql_parser.exe", ".sql")
        if not valid:
            return Result(False, mode, "[Detector] Embedded C+SQL\n" + parser_output)
        ok, sql_output, scalar = run_sql(embedded.group(1), source_file)
        if not ok:
            return Result(False, mode, "[Detector] Embedded C+SQL\n" + sql_output)
        source = source[:embedded.start()] + f"{embedded.group(2)} = {scalar};" + source[embedded.end():]
        result = _compile_minic(source, run, mode)
        result.output = "[Detector] Embedded C+SQL\n" + parser_output + sql_output + result.output
        return result
    result = _compile_minic(source, run, mode)
    result.output = "[Detector] MiniC\n" + result.output
    return result
