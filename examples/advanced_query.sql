SELECT name, marks
FROM students
WHERE marks >= 70 AND (name != 'Nabil' OR marks > 80)
ORDER BY marks DESC
LIMIT 10;
