int main() {
    int i = 0;
    int total = 0;
    while (i <= 10) {
        total = total + i;
        i = i + 1;
    }
    if (total > 50) {
        print(total);
    } else {
        print(0);
    }
    return 0;
}

