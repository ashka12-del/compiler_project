# MiniC + MiniSQL Editor

A Windows teaching IDE for a deliberately small C-like language, a CSV-backed SQL subset, and one embedded SQL statement. Flex performs lexical analysis, Bison validates syntax, Python coordinates execution, Tkinter provides the editor, and GCC compiles translated MiniC.

## Requirements and commands

- Windows 10/11
- Python 3.10 or newer with Tcl/Tk (`python` or the Windows `py -3` launcher)
- GCC on `PATH` (for example MinGW-w64)

From Command Prompt or PowerShell in the project folder:

```bat
run_editor.bat
build_parsers.bat
python -m unittest -v test_core.py
```

If `python` is unavailable but the Python launcher is installed, use:

```bat
py -3 app.py
py -3 -m unittest -v test_core.py
```

`run_editor.bat` checks Python and GCC and builds either missing parser. In the editor, use **F6** to compile or **F5** to compile and run.

## Accepted MiniC structure

A translation unit may contain global declarations and user-defined functions. A runnable program needs `main`:

```c
int add(int a, int b) {
    return a + b;
}

int main() {
    int values[3];
    int total = 0;

    for (int i = 0; i < 3; i++) {
        values[i] = i + 1;
        total = total + values[i];
    }

    do { total++; } while (total < 7);
    printf("total = %d\n", add(total, 1));
    return 0;
}
```

Accepted MiniC constructs:

- Types: `int`, `float`, `char`, and `void`
- Global variables, function definitions, typed parameters, function calls, and `main`
- Declaration: `int name;`, `float value = 1.5;`, comma-separated declarations, and arrays such as `int values[10];`
- Assignment: `name = expression;`
- Arithmetic: `+`, `-`, `*`, `/`, `%`, unary `+`/`-`, integers, decimal numbers, variables, calls, indexing, and parentheses
- Conditions: `==`, `!=`, `>`, `<`, `>=`, `<=`, logical `&&`, `||`, and `!`
- Control flow: `if/else`, `while`, `do ... while`, `for`, `break`, `continue`, and nested blocks
- Increment/decrement: `value++` and `value--`
- Output: `print(integer_expression);` or `print("text");`
- `print` is not reserved: if the program defines its own `print` function, calls use that function instead of the convenience translation.
- Formatted output: `printf("format", arguments...);`
- Formatted input: `scanf("format", &variables...);` — the editor asks for space-separated input before running
- Return: `return expression;`
- Comments: `// line comment` and `/* block comment */`
- C preprocessor lines are passed through to GCC; `<stdio.h>` is automatically included

Not accepted yet: pointer declarations, structs, unions, enums, array initializers, multidimensional declarators, `switch`, `goto`, ternary `?:`, compound assignments such as `+=`, prefix `++value`, casts, or full C type qualifiers. GCC performs the final type and semantic checks. This is still MiniC, not full ISO C.

## Accepted MiniSQL structure

Each `.sql` file contains one `SELECT` query over one CSV-backed table. `WHERE`, sorting, and limiting are optional:

```sql
SELECT name, marks
FROM students
WHERE marks >= 70 AND (name != 'Nabil' OR marks > 80)
ORDER BY marks DESC
LIMIT 10;
```

Aggregate form:

```sql
SELECT COUNT(*), AVG(marks), MIN(marks), MAX(marks)
FROM students
WHERE marks >= 40;
```

Grammar summary:

```text
SELECT [DISTINCT] (* | item [, item ...])
FROM table
[WHERE condition [AND | OR condition ...]]
[ORDER BY column [ASC | DESC]]
[LIMIT non_negative_integer]
[;]

item := column | SUM(column) | COUNT(column | *) | AVG(column) | MIN(column) | MAX(column)
condition := column (= | == | != | <> | > | < | >= | <=) value | (condition)
```

- Keywords are case-insensitive.
- Identifiers start with a letter or `_` and then contain letters, digits, or `_`.
- Values may be numbers or single/double-quoted strings.
- `--` starts an SQL line comment.
- Table `students` maps to `students.csv` beside the `.sql` or `.mc` source file.
- The first CSV row must contain column names.
- `SUM` and `AVG` require numeric data. `MIN` and `MAX` support numeric or text data.
- Multiple aggregate items are accepted, but aggregate and ordinary columns cannot be mixed.
- CSV column lookup is case-insensitive and ambiguous duplicate names are rejected.

Not accepted yet: `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, joins, aliases, `GROUP BY`, `HAVING`, `LIKE`, `IN`, `NOT`, `NULL`, subqueries, or multiple statements.

## Embedded MiniC + MiniSQL structure

Embedded mode is detected in an `.mc` program containing this statement:

```c
query "SELECT SUM(marks) FROM students WHERE marks > 40" into total;
```

Complete example:

```c
int main() {
    int total;
    query "SELECT SUM(marks) FROM students WHERE marks > 40" into total;
    print(total);
    return 0;
}
```

Rules:

- Declare the target as an `int` before the query.
- The embedded query must contain exactly one numeric `SUM`, `COUNT`, `AVG`, `MIN`, or `MAX` projection because `into` accepts one scalar integer result.
- Keep the matching `.csv` file beside the `.mc` file.
- Escape a double quote inside the SQL string as `\"`.
- Only one embedded query statement is currently supported.

At compile/run time, the editor validates the SQL, reads the CSV, computes the scalar result, replaces the query statement with a C assignment, validates the resulting MiniC, translates `print`, and invokes GCC.

## Project layout

- `app.py` — Tkinter editor
- `core.py` — mode detection, SQL runtime, translation, and toolchain orchestration
- `grammar/minic.l`, `grammar/minic.y` — MiniC lexer/parser
- `grammar/minisql.l`, `grammar/minisql.y` — MiniSQL lexer/parser
- `generated/` — generated C parser sources
- `bin/` — built parser executables
- `examples/` — sample MiniC, SQL, embedded source, and CSV data
- `test_core.py` — automated regression tests

## Recommended next features

Implement these in order:

1. Add semantic analysis with a symbol table: undeclared variables, duplicate declarations, and type checking.
2. Replace regex translation with an AST produced by Bison; this prevents source-to-source edge cases and enables better line diagnostics.
3. Add SQL joins, `GROUP BY`, aliases, `LIKE`/`IN`, and transactional CSV-backed `INSERT`/`UPDATE`/`DELETE`.
4. Support multiple embedded scalar queries and map SQL diagnostics back to the original `.mc` line.
5. Add editor line numbers, clickable diagnostics, find/replace, recent files, and configurable themes.
6. Add CI that rebuilds parsers and runs tests on every GitHub push; do not commit `__pycache__` or generated test artifacts.
7. Add a sandbox/resource policy for executed programs (time, memory, and output limits) before accepting untrusted source code.

This remains a course-project compiler/editor, not an ANSI C compiler or a database server.
