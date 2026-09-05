int main() {
    int value;
    printf("Enter a number: ");
    scanf("%d", &value);

    if (value >= 0) {
        printf("double = %d\n", value * 2);
    } else {
        printf("negative input\n");
    }
    return 0;
}
