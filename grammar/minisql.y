%{
#include <stdio.h>
#include <stdlib.h>
extern int yylex(void);
extern int yylineno;
extern FILE *yyin;
static int errors = 0;
void yyerror(const char *message);
%}
%union { char *text; }
%token SELECT FROM WHERE SUM COMPARE
%token <text> IDENTIFIER VALUE
%%
query: SELECT projection FROM IDENTIFIER WHERE IDENTIFIER COMPARE VALUE optional_semicolon {
    free($4); free($6); free($8);
};
projection: IDENTIFIER { free($1); } | SUM '(' IDENTIFIER ')' { free($3); } ;
optional_semicolon: %empty | ';' ;
%%
void yyerror(const char *message) {
    fprintf(stderr, "[MiniSQL parser] line %d: %s\n", yylineno, message);
    errors++;
}
int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "Usage: minisql_parser <source.sql>\n"); return 2; }
    yyin = fopen(argv[1], "rb");
    if (!yyin) { fprintf(stderr, "[MiniSQL parser] cannot open %s\n", argv[1]); return 2; }
    int result = yyparse(); fclose(yyin);
    if (result || errors) return 1;
    puts("[MiniSQL Flex/Bison] syntax accepted");
    return 0;
}

