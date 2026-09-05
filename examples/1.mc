int main() {
    int total;
    query "SELECT SUM(marks) FROM students WHERE marks > 40" into total;
    printf("%d\n", total);
    return 0;
}