# MiniC + MiniSQL Editor

A Windows code editor and compiler based on the supplied PRD and presentation. The language syntax is implemented with Flex lexer files and Bison grammar files. The editor uses Python's built-in Tkinter interface, and the MiniC backend uses GCC.

## Included features

- New, Open, Save, and Save As for `.mc` and `.sql` files
- Unsaved-change indicator and confirmation
- MiniC, MiniSQL, and embedded C+SQL detection
- Syntax highlighting for supported keywords, strings, numbers, and comments
- Compile and Compile/Run actions
- Integrated output and diagnostics console
- CSV-backed `SELECT ... FROM ... WHERE ...` execution
- `SUM(column)` for the embedded acceptance example
- Real Flex/Bison syntax validation for both languages
- Correct MiniC `print("text");` and `print(integer);` output through GCC

## Flex and Bison files

- `grammar/minic.l` - MiniC lexer
- `grammar/minic.y` - MiniC Bison grammar
- `grammar/minisql.l` - MiniSQL lexer
- `grammar/minisql.y` - MiniSQL Bison grammar
- `build_parsers.bat` - generates C sources and builds both parser executables

The required Windows Flex/Bison executables are included under `tools/winflexbison`. Generated parser source goes to `generated`, and parser executables go to `bin`.

## Start on Windows

Double-click `run_editor.bat`, or open a terminal in this folder and run:

```powershell
python app.py
```

Python 3 and GCC must be available on `PATH`. During Python installation, keep the optional Tcl/Tk component enabled and select **Add Python to PATH**. The editor needs no third-party Python packages.

`run_editor.bat` automatically builds the Flex/Bison parsers if they are missing. You can rebuild them manually by running `build_parsers.bat`.

## Run tests

```powershell
python -m unittest -v test_core.py
```

## Try the examples

Open a file from `examples` and select **Run** or press **F5**. Keep `students.csv` in the same directory as the SQL or embedded source file.

## Supported subset

MiniC is compiled through GCC after translating `print(value);` into a C `printf` call. MiniSQL supports one table and one `WHERE` condition with `=`, `!=`, `<>`, `>`, `<`, `>=`, or `<=`. Embedded mode supports one statement in this form:

```c
query "SELECT SUM(marks) FROM students WHERE marks > 40" into total;
```

This is intentionally a course-project editor, not a full IDE or full ANSI C/SQL implementation.
