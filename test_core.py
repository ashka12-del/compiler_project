import tempfile
import unittest
from pathlib import Path

from core import compile_or_run, detect_mode, run_sql


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
        self.assertEqual(detect_mode('// query "SELECT SUM(marks) FROM students WHERE marks > 80" into x;\nint main(){}', "a.mc"), "MiniC")

    def test_sql(self):
        result = compile_or_run("SELECT name FROM students WHERE marks > 80;", self.directory / "query.sql")
        self.assertTrue(result.success); self.assertIn("Asha", result.output); self.assertIn("Rafi", result.output)

    def test_sql_comments_are_accepted_at_runtime(self):
        sql = "-- top-level comment\nSELECT name FROM students WHERE marks > 80; -- trailing comment"
        result = compile_or_run(sql, self.directory / "query.sql")
        self.assertTrue(result.success); self.assertIn("Asha", result.output)

    def test_minic(self):
        result = compile_or_run("int main(){int x=2;while(x<5){x=x+1;}print(x);return 0;}", self.directory / "sum.mc")
        self.assertTrue(result.success); self.assertIn("5", result.output)

    def test_string_output(self):
        result = compile_or_run('int main(){print("Ashka");return 0;}', self.directory / "hello.mc")
        self.assertTrue(result.success); self.assertIn("[Program output]\nAshka\n", result.output)

    def test_string_output_can_contain_semicolon(self):
        result = compile_or_run('int main(){print("A;B");return 0;}', self.directory / "hello.mc")
        self.assertTrue(result.success); self.assertIn("[Program output]\nA;B\n", result.output)

    def test_embedded(self):
        source = 'int main(){int total;query "SELECT SUM(marks) FROM students WHERE marks > 80" into total;print(total);return 0;}'
        result = compile_or_run(source, self.directory / "report.mc")
        self.assertTrue(result.success); self.assertIn("175", result.output)

    def test_embedded_non_scalar_query_is_rejected(self):
        source = 'int main(){int total;query "SELECT name FROM students WHERE marks > 80" into total;return 0;}'
        result = compile_or_run(source, self.directory / "report.mc")
        self.assertFalse(result.success)
        self.assertIn("requires one scalar aggregate", result.output)

    def test_embedded_query_supports_escaped_quotes(self):
        source = 'int main(){int total;query "SELECT SUM(marks) FROM students WHERE name = \\"Asha\\"" into total;print(total);return 0;}'
        result = compile_or_run(source, self.directory / "report.mc")
        self.assertTrue(result.success); self.assertIn("[Program output]\n90\n", result.output)

    def test_empty_csv_keeps_its_schema(self):
        (self.directory / "empty.csv").write_text("name,marks\n", encoding="utf-8")
        ok, output, _ = run_sql(
            "SELECT name FROM empty WHERE marks > 80;", self.directory / "query.sql"
        )
        self.assertTrue(ok); self.assertIn("(0 rows)", output)

    def test_sum_rejects_non_numeric_data(self):
        (self.directory / "bad.csv").write_text("name,marks\nAsha,N/A\n", encoding="utf-8")
        ok, output, _ = run_sql(
            "SELECT SUM(marks) FROM bad WHERE name = 'Asha';", self.directory / "query.sql"
        )
        self.assertFalse(ok); self.assertIn("SUM requires numeric values", output)

    def test_sum_of_no_matching_rows_is_zero(self):
        ok, output, total = run_sql(
            "SELECT SUM(marks) FROM students WHERE marks > 100;", self.directory / "query.sql"
        )
        self.assertTrue(ok); self.assertEqual(total, 0); self.assertIn("SUM(marks) = 0", output)

    def test_for_do_while_function_array_and_printf(self):
        source = r'''
int add(int a, int b) { return a + b; }
int main() {
    int values[3];
    int total = 0;
    for (int i = 0; i < 3; i++) {
        values[i] = i + 1;
        total = total + values[i];
    }
    do { total++; } while (total < 7);
    printf("%d\n", add(total, 1));
    return 0;
}
'''
        result = compile_or_run(source, self.directory / "structures.mc")
        self.assertTrue(result.success, result.output); self.assertIn("[Program output]\n8\n", result.output)

    def test_scanf_receives_program_input(self):
        source = 'int main(){int x;scanf("%d", &x);printf("%d\\n", x * 2);return 0;}'
        result = compile_or_run(source, self.directory / "input.mc", stdin_text="21\n")
        self.assertTrue(result.success, result.output); self.assertIn("[Program output]\n42\n", result.output)

    def test_user_defined_print_function(self):
        source = '''void print(int x){
            printf("%d", x);
        }
        int main(){
            print(5);
        }'''
        result = compile_or_run(source, self.directory / "custom_print.mc")
        self.assertTrue(result.success, result.output); self.assertIn("[Program output]\n5", result.output)

    def test_for_break_continue_and_logic(self):
        source = '''int main(){
            int total=0;
            for(int i=0;i<6;i++){
                if(i==2) continue;
                if(i>3 && total>=4) break;
                total=total+i;
            }
            printf("%d\\n",total);return 0;
        }'''
        result = compile_or_run(source, self.directory / "flow.mc")
        self.assertTrue(result.success, result.output); self.assertIn("[Program output]\n4\n", result.output)

    def test_sql_multiple_columns_order_and_limit(self):
        sql = "SELECT name, marks FROM students ORDER BY marks DESC LIMIT 2;"
        result = compile_or_run(sql, self.directory / "query.sql")
        self.assertTrue(result.success, result.output)
        self.assertIn("name | marks", result.output)
        self.assertLess(result.output.index("Asha | 90"), result.output.index("Rafi | 85"))
        self.assertNotIn("Nabil | 70", result.output)

    def test_sql_distinct_star_and_boolean_where(self):
        (self.directory / "people.csv").write_text(
            "name,city,age\nA,Dhaka,20\nB,Dhaka,25\nC,Khulna,30\n", encoding="utf-8"
        )
        sql = "SELECT DISTINCT city FROM people WHERE age >= 20 AND (city = 'Dhaka' OR city = 'Khulna');"
        result = compile_or_run(sql, self.directory / "query.sql")
        self.assertTrue(result.success, result.output)
        self.assertIn("Dhaka", result.output); self.assertIn("Khulna", result.output)
        star = compile_or_run("SELECT * FROM people LIMIT 1;", self.directory / "query.sql")
        self.assertTrue(star.success, star.output); self.assertIn("name | city | age", star.output)

    def test_sql_aggregate_family(self):
        sql = "SELECT COUNT(*), AVG(marks), MIN(marks), MAX(marks) FROM students;"
        result = compile_or_run(sql, self.directory / "query.sql")
        self.assertTrue(result.success, result.output)
        self.assertIn("COUNT(*)", result.output); self.assertIn("3 |", result.output)
        self.assertIn("70 | 90", result.output)

    def test_embedded_count(self):
        source = 'int main(){int total;query "SELECT COUNT(*) FROM students WHERE marks >= 80" into total;printf("%d\\n",total);return 0;}'
        result = compile_or_run(source, self.directory / "report.mc")
        self.assertTrue(result.success, result.output); self.assertIn("[Program output]\n2\n", result.output)


if __name__ == "__main__": unittest.main(verbosity=2)
