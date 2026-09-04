import tempfile
import unittest
from pathlib import Path

from core import compile_or_run, detect_mode


class CompilerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        (self.directory / "students.csv").write_text("name,marks\nAsha,90\nNabil,70\nRafi,85\n", encoding="utf-8")

    def tearDown(self): self.temp.cleanup()

    def test_detection(self):
        self.assertEqual(detect_mode("int main(){}", "a.mc"), "MiniC")
        self.assertEqual(detect_mode("SELECT name FROM students WHERE marks > 80;", "a.sql"), "MiniSQL")
        self.assertEqual(detect_mode('int main(){query "SELECT name FROM students WHERE marks > 80" into x;}', "a.mc"), "Embedded C+SQL")

    def test_sql(self):
        result = compile_or_run("SELECT name FROM students WHERE marks > 80;", self.directory / "query.sql")
        self.assertTrue(result.success); self.assertIn("Asha", result.output); self.assertIn("Rafi", result.output)

    def test_minic(self):
        result = compile_or_run("int main(){int x=2;while(x<5){x=x+1;}print(x);return 0;}", self.directory / "sum.mc")
        self.assertTrue(result.success); self.assertIn("5", result.output)

    def test_string_output(self):
        result = compile_or_run('int main(){print("Ashka");return 0;}', self.directory / "hello.mc")
        self.assertTrue(result.success); self.assertIn("[Program output]\nAshka\n", result.output)

    def test_embedded(self):
        source = 'int main(){int total;query "SELECT SUM(marks) FROM students WHERE marks > 80" into total;print(total);return 0;}'
        result = compile_or_run(source, self.directory / "report.mc")
        self.assertTrue(result.success); self.assertIn("175", result.output)


if __name__ == "__main__": unittest.main(verbosity=2)
