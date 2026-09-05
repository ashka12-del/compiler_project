int add(int a, int b) {
    return a + b;
}

int main() {
    int values[3];
    int total = 0;

    for (int i = 0; i < 3; i++) {
        values[i] = i + 1;
        total = add(total, values[i]);
    }

    do {
        total++;
    } while (total < 7);

    printf("total = %d\n", total);
    return 0;
}
