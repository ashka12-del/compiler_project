from __future__ import annotations

import ast
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
PROCESS_TIMEOUT_SECONDS = 10
EMBEDDED_QUERY_RE = re.compile(
    r'\bquery\s*"((?:\\.|[^"\\])*)"\s*into\s+([A-Za-z_]\w*)\s*;', re.I
)


def _strip_line_comments(source: str, marker: str) -> str:
    """Replace line comments with spaces while preserving strings and offsets."""
    result = list(source)
    quote = None
    escaped = False
    index = 0
    while index < len(source):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in "\"'":
            quote = char
            index += 1
            continue
        if source.startswith(marker, index):
            while index < len(source) and source[index] not in "\r\n":
                result[index] = " "
                index += 1
            continue
        index += 1
    return "".join(result)


def _validate_with_bison(source: str, parser_name: str, suffix: str) -> tuple[bool, str]:
    parser = ROOT / "bin" / parser_name
    if not parser.exists():
        return False, f"[Toolchain] Missing {parser.name}. Run build_parsers.bat first.\n"
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as handle:
        handle.write(source)
        source_path = Path(handle.name)
    try:
        try:
            checked = subprocess.run(
                [str(parser), str(source_path)], capture_output=True, text=True,
                timeout=PROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return False, f"[Toolchain] {parser.name} timed out.\n"
        return checked.returncode == 0, checked.stdout + checked.stderr
    finally:
        source_path.unlink(missing_ok=True)


def detect_mode(source: str, filename: str | Path = "") -> str:
    path = Path(filename) if filename else None
    if path and path.suffix.lower() == ".sql":
        return "MiniSQL"
    uncommented = _strip_line_comments(source, "//")
    if EMBEDDED_QUERY_RE.search(uncommented):
        return "Embedded C+SQL"
    if re.match(r"\s*SELECT\b", _strip_line_comments(source, "--"), re.I):
        return "MiniSQL"
    return "MiniC"


def _compare(left: str, operator: str, right: str) -> bool:
    right = right.strip()
    if len(right) >= 2 and right[0] == right[-1] and right[0] in "\"'":
        try:
            right = ast.literal_eval(right)
        except (SyntaxError, ValueError):
            right = right[1:-1]
    try:
        a, b = float(left), float(right)
    except (TypeError, ValueError):
        a, b = str(left), str(right)
    return {"=": a == b, "==": a == b, "!=": a != b, "<>": a != b,
            ">": a > b, "<": a < b, ">=": a >= b, "<=": a <= b}[operator]


SELECT_RE = re.compile(
    r"\s*SELECT\s+(?P<distinct>DISTINCT\s+)?(?P<projection>.+?)\s+FROM\s+"
    r"(?P<table>[A-Za-z_]\w*)"
    r"(?:\s+WHERE\s+(?P<where>.*?)(?=\s+ORDER\s+BY|\s+LIMIT|\s*;?\s*$))?"
    r"(?:\s+ORDER\s+BY\s+(?P<order>[A-Za-z_]\w*)(?:\s+(?P<direction>ASC|DESC))?)?"
    r"(?:\s+LIMIT\s+(?P<limit>[0-9]+))?\s*;?\s*",
    re.I | re.S,
)
WHERE_TOKEN_RE = re.compile(
    r"\s*(>=|<=|!=|<>|==|=|>|<|\(|\)|\bAND\b|\bOR\b|"
    r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|[0-9]+(?:\.[0-9]+)?|[A-Za-z_]\w*)",
    re.I,
)
AGGREGATE_RE = re.compile(r"(SUM|COUNT|AVG|MIN|MAX)\s*\(\s*(\*|[A-Za-z_]\w*)\s*\)", re.I)


class SqlSemanticError(ValueError):
    pass


def _column_name(columns: list[str], requested: str) -> str:
    matches = [column for column in columns if column.lower() == requested.lower()]
    if len(matches) != 1:
        raise SqlSemanticError(f"unknown or ambiguous column: {requested}")
    return matches[0]


def _where_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    position = 0
    while position < len(text):
        match = WHERE_TOKEN_RE.match(text, position)
        if not match:
            if text[position:].strip():
                raise SqlSemanticError(f"invalid WHERE expression near: {text[position:].strip()}")
            break
        tokens.append(match.group(1))
        position = match.end()
    return tokens


class _WhereEvaluator:
    def __init__(self, tokens: list[str], row: dict[str, str], columns: list[str]):
        self.tokens = tokens
        self.row = row
        self.columns = columns
        self.position = 0

    def evaluate(self) -> bool:
        result = self._or_expression()
        if self.position != len(self.tokens):
            raise SqlSemanticError(f"unexpected token in WHERE: {self.tokens[self.position]}")
        return result

    def _accept(self, value: str) -> bool:
        if self.position < len(self.tokens) and self.tokens[self.position].upper() == value:
            self.position += 1
            return True
        return False

    def _or_expression(self) -> bool:
        result = self._and_expression()
        while self._accept("OR"):
            right = self._and_expression()
            result = result or right
        return result

    def _and_expression(self) -> bool:
        result = self._primary()
        while self._accept("AND"):
            right = self._primary()
            result = result and right
        return result

    def _primary(self) -> bool:
        if self._accept("("):
            result = self._or_expression()
            if not self._accept(")"):
                raise SqlSemanticError("missing ')' in WHERE expression")
            return result
        if self.position + 2 >= len(self.tokens):
            raise SqlSemanticError("incomplete WHERE condition")
        requested, operator, wanted = self.tokens[self.position:self.position + 3]
        self.position += 3
        if operator not in {"=", "==", "!=", "<>", ">", "<", ">=", "<="}:
            raise SqlSemanticError(f"expected comparison operator after {requested}")
        column = _column_name(self.columns, requested)
        return _compare(self.row.get(column, ""), operator, wanted)


def _number(value: str, function: str, column: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise SqlSemanticError(f"{function} requires numeric values in column: {column}") from exc


def _aggregate(function: str, requested: str, rows: list[dict[str, str]], columns: list[str]):
    function = function.upper()
    if requested == "*":
        if function != "COUNT":
            raise SqlSemanticError(f"{function}(*) is not supported; use a column")
        return len(rows)
    column = _column_name(columns, requested)
    values = [row.get(column, "") for row in rows]
    if function == "COUNT":
        return sum(value not in (None, "") for value in values)
    if not values:
        return 0 if function == "SUM" else None
    if function in {"SUM", "AVG"}:
        numbers = [_number(value, function, column) for value in values]
        result = sum(numbers, 0.0) if function == "SUM" else sum(numbers, 0.0) / len(numbers)
    else:
        try:
            numeric_values = [float(value) for value in values]
            result = min(numeric_values) if function == "MIN" else max(numeric_values)
        except (TypeError, ValueError):
            result = min(values) if function == "MIN" else max(values)
    return int(result) if isinstance(result, float) and result.is_integer() else result


def _sort_key(value: str):
    try:
        return 0, float(value)
    except (TypeError, ValueError):
        return 1, str(value).casefold()


def run_sql(sql: str, source_file: Path) -> tuple[bool, str, object]:
    sql = _strip_line_comments(sql, "--")
    match = SELECT_RE.fullmatch(sql)
    if not match:
        return False, "[MiniSQL runtime] unsupported SELECT structure.\n", 0
    projection = match.group("projection").strip()
    table = match.group("table")
    csv_path = source_file.parent / f"{table}.csv"
    if not csv_path.exists():
        return False, f"[MiniSQL runtime] table file not found: {csv_path}\n", 0
    try:
        with csv_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            rows = list(reader)
    except (OSError, csv.Error) as exc:
        return False, f"[MiniSQL runtime] could not read {csv_path.name}: {exc}\n", 0
    if not columns:
        return False, f"[MiniSQL semantic] table has no header columns: {csv_path.name}\n", 0
    try:
        where_text = match.group("where")
        if where_text:
            tokens = _where_tokens(where_text)
            selected = [row for row in rows if _WhereEvaluator(tokens, row, columns).evaluate()]
        else:
            selected = rows[:]
        order_name = match.group("order")
        if order_name:
            order_column = _column_name(columns, order_name)
            selected.sort(
                key=lambda row: _sort_key(row.get(order_column, "")),
                reverse=(match.group("direction") or "ASC").upper() == "DESC",
            )
        if match.group("limit") is not None:
            selected = selected[:int(match.group("limit"))]

        projections = columns if projection == "*" else [item.strip() for item in projection.split(",")]
        aggregates = [AGGREGATE_RE.fullmatch(item) for item in projections]
        if any(aggregates) and not all(aggregates):
            raise SqlSemanticError("aggregate and non-aggregate columns cannot be mixed")

        steps = [f"SCAN {table}"]
        if where_text:
            steps.append(f"FILTER {where_text.strip()}")
        if order_name:
            steps.append(f"SORT {order_name} {(match.group('direction') or 'ASC').upper()}")
        if match.group("limit") is not None:
            steps.append(f"LIMIT {match.group('limit')}")
        steps.append(f"PROJECT {projection}")
        plan = "[MiniSQL] Plan: " + " -> ".join(steps) + "\n"

        if all(aggregates):
            headers = [
                f"{aggregate.group(1).upper()}({aggregate.group(2)})"
                for aggregate in aggregates if aggregate
            ]
            values = [
                _aggregate(aggregate.group(1), aggregate.group(2), selected, columns)
                for aggregate in aggregates if aggregate
            ]
            rendered = ["NULL" if value is None else str(value) for value in values]
            if len(values) == 1:
                return True, plan + f"{headers[0]} = {rendered[0]}\n", values[0]
            return True, plan + " | ".join(headers) + "\n" + " | ".join(rendered) + "\n(1 row)\n", 0

        projected_columns = [_column_name(columns, item) for item in projections]
        result_rows = [tuple(row.get(column, "") for column in projected_columns) for row in selected]
        if match.group("distinct"):
            result_rows = list(dict.fromkeys(result_rows))
        header = " | ".join(projected_columns)
        body = "\n".join(" | ".join(values) for values in result_rows)
        return True, plan + header + "\n" + "-" * len(header) + "\n" + body + f"\n({len(result_rows)} rows)\n", 0
    except SqlSemanticError as exc:
        return False, f"[MiniSQL semantic] {exc}\n", 0


def _compile_minic(source: str, run: bool, mode: str, stdin_text: str = "") -> Result:
    valid, parser_output = _validate_with_bison(source, "minic_parser.exe", ".mc")
    if not valid:
        return Result(False, mode, parser_output)
    def translate_print(match: re.Match) -> str:
        value = match.group(1).strip()
        if re.fullmatch(r'"(?:\\.|[^"\\])*"', value):
            return f'printf("%s\\n", {value});'
        return f'printf("%d\\n", (int)({value}));'
    has_print_function = re.search(
        r"\b(?:void|int|float|char)\s+print\s*\(",
        _strip_line_comments(source, "//"),
    )
    translated = source if has_print_function else re.sub(
        r'\bprint\s*\(\s*((?:"(?:\\.|[^"\\])*")|(?:[^;"\']+))\s*\)\s*;',
        translate_print,
        source,
    )
    c_source = "#include <stdio.h>\n" + translated
    with tempfile.TemporaryDirectory(prefix="minic_minisql_") as directory:
        build_dir = Path(directory)
        c_file, exe_file = build_dir / "program.c", build_dir / "program.exe"
        c_file.write_text(c_source, encoding="utf-8")
        try:
            built = subprocess.run(
                ["gcc", "-std=c11", "-Wall", str(c_file), "-o", str(exe_file)],
                capture_output=True, text=True, timeout=PROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return Result(False, mode, "[MiniC code generator] GCC timed out.\n")
        if built.returncode:
            return Result(False, mode, "[MiniC code generator]\n" + built.stdout + built.stderr)
        output = parser_output + "[MiniC] Semantic -> IR -> Codegen: successful\n"
        if not run:
            return Result(True, mode, output + "Compilation completed successfully.\n")
        try:
            executed = subprocess.run(
                [str(exe_file)], input=stdin_text, capture_output=True, text=True,
                timeout=PROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return Result(False, mode, output + "[Program output]\nProgram timed out.\n")
        return Result(
            executed.returncode == 0, mode,
            output + "[Program output]\n" + executed.stdout + executed.stderr,
        )


def compile_or_run(
    source: str, filename: str | Path, run: bool = True, stdin_text: str = ""
) -> Result:
    source_file = Path(filename)
    mode = detect_mode(source, source_file)
    if mode == "MiniSQL":
        valid, parser_output = _validate_with_bison(source, "minisql_parser.exe", ".sql")
        if not valid:
            return Result(False, mode, "[Detector] MiniSQL\n" + parser_output)
        ok, output, _ = run_sql(source, source_file)
        return Result(ok, mode, "[Detector] MiniSQL\n" + parser_output + output)
    if mode == "Embedded C+SQL":
        embedded = EMBEDDED_QUERY_RE.search(_strip_line_comments(source, "//"))
        if not embedded:
            return Result(False, mode, '[Embedded parser] expected query "..." into variable;\n')
        try:
            sql = ast.literal_eval(f'"{embedded.group(1)}"')
        except (SyntaxError, ValueError):
            return Result(False, mode, "[Embedded parser] invalid escape sequence in SQL string.\n")
        if not re.match(r"\s*SELECT\s+(?:SUM|COUNT|AVG|MIN|MAX)\s*\(", sql, re.I):
            return Result(False, mode, "[Embedded semantic] INTO requires one scalar aggregate query.\n")
        valid, parser_output = _validate_with_bison(sql, "minisql_parser.exe", ".sql")
        if not valid:
            return Result(False, mode, "[Detector] Embedded C+SQL\n" + parser_output)
        ok, sql_output, scalar = run_sql(sql, source_file)
        if not ok:
            return Result(False, mode, "[Detector] Embedded C+SQL\n" + sql_output)
        if not isinstance(scalar, (int, float)) or (isinstance(scalar, float) and not scalar.is_integer()):
            return Result(False, mode, "[Embedded semantic] MiniC int target requires an integer aggregate result.\n")
        source = source[:embedded.start()] + f"{embedded.group(2)} = {scalar};" + source[embedded.end():]
        result = _compile_minic(source, run, mode, stdin_text)
        result.output = "[Detector] Embedded C+SQL\n" + parser_output + sql_output + result.output
        return result
    result = _compile_minic(source, run, mode, stdin_text)
    result.output = "[Detector] MiniC\n" + result.output
    return result
