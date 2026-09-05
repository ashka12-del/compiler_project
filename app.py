from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from core import compile_or_run, detect_mode


class Editor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MiniC + MiniSQL Editor")
        self.geometry("1100x760")
        self.minsize(760, 520)
        self.file: Path | None = None
        self.dirty = False
        self.after_id = None
        self._style()
        self._menu()
        self._layout()
        self.new_file(force=True)

    def _style(self):
        self.configure(bg="#181818")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#181818")
        style.configure("TButton", padding=(12, 7), background="#333333", foreground="#ffffff")
        style.map("TButton", background=[("active", "#0e639c")])
        style.configure("TLabel", background="#007acc", foreground="#ffffff", padding=(8, 4))

    def _menu(self):
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save)
        file_menu.add_command(label="Save As...", command=self.save_as)
        file_menu.add_separator(); file_menu.add_command(label="Exit", command=self.close)
        edit_menu = tk.Menu(menu, tearoff=False)
        for label, event in [("Undo", "<<Undo>>"), ("Cut", "<<Cut>>"), ("Copy", "<<Copy>>"), ("Paste", "<<Paste>>")]:
            edit_menu.add_command(label=label, command=lambda e=event: self.source.event_generate(e))
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=lambda: self.source.tag_add("sel", "1.0", "end-1c"))
        build_menu = tk.Menu(menu, tearoff=False)
        build_menu.add_command(label="Compile", accelerator="F6", command=lambda: self.build(False))
        build_menu.add_command(label="Compile and Run", accelerator="F5", command=lambda: self.build(True))
        build_menu.add_command(label="Clear Output", command=self.clear_output)
        menu.add_cascade(label="File", menu=file_menu); menu.add_cascade(label="Edit", menu=edit_menu); menu.add_cascade(label="Build", menu=build_menu)
        self.config(menu=menu)
        self.bind("<Control-n>", lambda _: self.new_file()); self.bind("<Control-o>", lambda _: self.open_file())
        self.bind("<Control-s>", lambda _: self.save()); self.bind("<F5>", lambda _: self.build(True)); self.bind("<F6>", lambda _: self.build(False))
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _layout(self):
        toolbar = ttk.Frame(self); toolbar.pack(fill="x", padx=8, pady=8)
        for text, action in [("New", self.new_file), ("Open", self.open_file), ("Save", self.save), ("Compile", lambda: self.build(False)), ("Run", lambda: self.build(True)), ("Clear", self.clear_output)]:
            ttk.Button(toolbar, text=text, command=action).pack(side="left", padx=(0, 6))
        pane = ttk.Panedwindow(self, orient="vertical"); pane.pack(fill="both", expand=True, padx=8)
        editor_frame = ttk.Frame(pane); output_frame = ttk.Frame(pane)
        self.source = tk.Text(editor_frame, undo=True, wrap="none", bg="#1e1e1e", fg="#d4d4d4", insertbackground="white", selectbackground="#264f78", font=("Consolas", 12), padx=12, pady=10)
        sy = ttk.Scrollbar(editor_frame, command=self.source.yview); sx = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.source.xview)
        self.source.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.source.grid(row=0, column=0, sticky="nsew"); sy.grid(row=0, column=1, sticky="ns"); sx.grid(row=1, column=0, sticky="ew")
        editor_frame.rowconfigure(0, weight=1); editor_frame.columnconfigure(0, weight=1)
        self.output = tk.Text(output_frame, height=10, state="disabled", wrap="word", bg="#181818", fg="#d4d4d4", insertbackground="white", font=("Consolas", 10), padx=10, pady=8)
        oy = ttk.Scrollbar(output_frame, command=self.output.yview); self.output.configure(yscrollcommand=oy.set)
        self.output.grid(row=0, column=0, sticky="nsew"); oy.grid(row=0, column=1, sticky="ns")
        output_frame.rowconfigure(0, weight=1); output_frame.columnconfigure(0, weight=1)
        pane.add(editor_frame, weight=4); pane.add(output_frame, weight=1)
        self.status = ttk.Label(self, text="Mode: MiniC"); self.status.pack(fill="x", side="bottom")
        self.source.bind("<<Modified>>", self.changed); self.source.bind("<KeyRelease>", lambda _: self.update_status()); self.source.bind("<ButtonRelease-1>", lambda _: self.update_status())
        colors = {"keyword": "#c586c0", "sql": "#4ec9b0", "string": "#ce9178", "number": "#b5cea8", "comment": "#6a9955"}
        for tag, color in colors.items(): self.source.tag_configure(tag, foreground=color)
        self.source.tag_configure("keyword", font=("Consolas", 12, "bold")); self.source.tag_configure("sql", font=("Consolas", 12, "bold"))

    def changed(self, _=None):
        if self.source.edit_modified():
            self.dirty = True; self.refresh_title(); self.source.edit_modified(False)
            if self.after_id: self.after_cancel(self.after_id)
            self.after_id = self.after(160, self.highlight)

    def highlight(self):
        text = self.source.get("1.0", "end-1c")
        for tag in ("keyword", "sql", "string", "number", "comment"): self.source.tag_remove(tag, "1.0", "end")
        patterns = {
            "keyword": r"\b(?:int|float|char|void|if|else|while|do|for|break|continue|print|printf|scanf|return|query|into)\b",
            "sql": r"\b(?:SELECT|DISTINCT|FROM|WHERE|AND|OR|SUM|COUNT|AVG|MIN|MAX|ORDER|BY|ASC|DESC|LIMIT|SCAN|FILTER|SORT|PROJECT)\b",
            "string": r'"(?:\\.|[^"\\])*"',
            "number": r"\b\d+(?:\.\d+)?\b",
            "comment": r"//[^\n]*|--[^\n]*|/\*.*?\*/",
        }
        for tag, pattern in patterns.items():
            flags = re.I if tag == "sql" else re.S if tag == "comment" else 0
            for match in re.finditer(pattern, text, flags):
                self.source.tag_add(tag, f"1.0+{match.start()}c", f"1.0+{match.end()}c")
        self.update_status()

    def refresh_title(self):
        name = self.file.name if self.file else "Untitled.mc"
        self.title(f"{name}{' *' if self.dirty else ''} - MiniC + MiniSQL Editor")

    def update_status(self):
        line, column = self.source.index("insert").split(".")
        mode = detect_mode(self.source.get("1.0", "end-1c"), self.file or "")
        self.status.configure(text=f"Mode: {mode}    Line {line}, Column {int(column)+1}")

    def write_output(self, text: str, clear=False):
        self.output.configure(state="normal")
        if clear: self.output.delete("1.0", "end")
        self.output.insert("end", text); self.output.see("end"); self.output.configure(state="disabled")

    def clear_output(self): self.write_output("", clear=True)

    def confirm(self):
        if not self.dirty: return True
        answer = messagebox.askyesnocancel("Unsaved changes", "Save changes before continuing?")
        return answer is False or (answer is True and self.save())

    def new_file(self, force=False):
        if not force and not self.confirm(): return
        self.file = None; self.source.delete("1.0", "end"); self.source.insert("1.0", "int main() {\n    print(0);\n    return 0;\n}\n")
        self.dirty = False; self.source.edit_modified(False); self.write_output("MiniC + MiniSQL Editor ready.\n", clear=True); self.refresh_title(); self.highlight()

    def open_file(self):
        if not self.confirm(): return
        name = filedialog.askopenfilename(filetypes=[("MiniC and MiniSQL", "*.mc *.sql"), ("All files", "*.*")])
        if not name: return
        self.file = Path(name)
        try: content = self.file.read_text(encoding="utf-8-sig")
        except OSError as exc: messagebox.showerror("Open error", str(exc)); return
        self.source.delete("1.0", "end"); self.source.insert("1.0", content); self.dirty = False; self.source.edit_modified(False)
        self.write_output(f"[Editor] Opened {self.file}\n", clear=True); self.refresh_title(); self.highlight()

    def save(self):
        if not self.file: return self.save_as()
        try: self.file.write_text(self.source.get("1.0", "end-1c"), encoding="utf-8")
        except OSError as exc: messagebox.showerror("Save error", str(exc)); return False
        self.dirty = False; self.source.edit_modified(False); self.refresh_title(); self.write_output(f"[Editor] Saved {self.file}\n")
        return True

    def save_as(self):
        name = filedialog.asksaveasfilename(defaultextension=".mc", filetypes=[("MiniC", "*.mc"), ("MiniSQL", "*.sql"), ("All files", "*.*")])
        if not name: return False
        self.file = Path(name); return self.save()

    def build(self, run: bool):
        if not self.file and not self.save_as(): return
        if self.dirty and not self.save(): return
        stdin_text = ""
        if run and re.search(r"\bscanf\s*\(", self.source.get("1.0", "end-1c")):
            entered = simpledialog.askstring(
                "Program input",
                "Enter scanf input (separate multiple values with spaces):",
                parent=self,
            )
            if entered is None: return
            stdin_text = entered + "\n"
        self.write_output("[Editor] Running...\n" if run else "[Editor] Compiling...\n", clear=True)
        try: result = compile_or_run(self.source.get("1.0", "end-1c"), self.file, run, stdin_text)
        except FileNotFoundError:
            self.write_output("[Toolchain] GCC was not found on PATH. Install GCC or add it to PATH.\n"); return
        except Exception as exc:
            self.write_output(f"[Editor] Unexpected error: {exc}\n"); return
        self.write_output(result.output + ("[Editor] Completed successfully.\n" if result.success else "[Editor] Failed.\n"))

    def close(self):
        if self.confirm(): self.destroy()


if __name__ == "__main__":
    Editor().mainloop()
