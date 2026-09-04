int main() {
    int total;
    query "SELECT SUM(marks) FROM students WHERE marks > 40" into total;
    if (total > 100) {
        print(total);
    } else {
        print(0);
    }
    return 0;
}

