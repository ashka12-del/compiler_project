%{
#include <stdio.h>
#include <stdlib.h>
extern int yylex(void);
extern int yylineno;
extern FILE *yyin;
static int errors = 0;
void yyerror(const char *message);
%}
%union { int number; char *text; }
%token INT MAIN IF ELSE WHILE PRINT RETURN COMPARE
%token <number> NUMBER
%token <text> IDENTIFIER STRING
%left '+' '-'
%left '*' '/'
%%
program: INT MAIN '(' ')' block ;
block: '{' statements '}' ;
statements: %empty | statements statement ;
statement:
      INT IDENTIFIER optional_initializer ';' { free($2); }
    | IDENTIFIER '=' expression ';'           { free($1); }
    | PRINT '(' printable ')' ';'
    | IF '(' condition ')' block
    | IF '(' condition ')' block ELSE block
    | WHILE '(' condition ')' block
    | RETURN expression ';'
    | block
    ;
optional_initializer: %empty | '=' expression ;
printable: expression | STRING { free($1); } ;
condition: expression | expression COMPARE expression ;
expression:
      NUMBER
    | IDENTIFIER              { free($1); }
    | '(' expression ')'
    | expression '+' expression
    | expression '-' expression
    | expression '*' expression
    | expression '/' expression
    ;
%%
void yyerror(const char *message) {
    fprintf(stderr, "[MiniC parser] line %d: %s\n", yylineno, message);
    errors++;
}
int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "Usage: minic_parser <source.mc>\n"); return 2; }
    yyin = fopen(argv[1], "rb");
    if (!yyin) { fprintf(stderr, "[MiniC parser] cannot open %s\n", argv[1]); return 2; }
    int result = yyparse(); fclose(yyin);
    if (result || errors) return 1;
    puts("[MiniC Flex/Bison] syntax accepted");
    return 0;
}

