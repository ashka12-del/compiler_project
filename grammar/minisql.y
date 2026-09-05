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
%token SELECT FROM WHERE DISTINCT SUM COUNT AVG MIN MAX
%token AND OR ORDER BY ASC DESC LIMIT COMPARE
%token <text> IDENTIFIER VALUE
%left OR
%left AND
%%
query: select_statement optional_semicolon ;
select_statement:
    SELECT distinct_opt projection_list FROM IDENTIFIER where_opt order_opt limit_opt
    ;
distinct_opt: %empty | DISTINCT ;
projection_list: '*' | projection_items ;
projection_items: projection | projection_items ',' projection ;
projection: IDENTIFIER | aggregate '(' aggregate_argument ')' ;
aggregate: SUM | COUNT | AVG | MIN | MAX ;
aggregate_argument: IDENTIFIER | '*' ;
where_opt: %empty | WHERE boolean_expression ;
boolean_expression:
      predicate
    | '(' boolean_expression ')'
    | boolean_expression AND boolean_expression
    | boolean_expression OR boolean_expression
    ;
predicate: IDENTIFIER COMPARE VALUE ;
order_opt: %empty | ORDER BY IDENTIFIER direction_opt ;
direction_opt: %empty | ASC | DESC ;
limit_opt: %empty | LIMIT VALUE ;
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
