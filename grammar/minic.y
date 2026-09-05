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
%token INT FLOAT CHAR VOID MAIN IF ELSE WHILE DO FOR BREAK CONTINUE
%token PRINTF SCANF RETURN
%token EQ_OP REL_OP LOGICAL_AND LOGICAL_OR INC DEC
%token <text> NUMBER FLOAT_NUMBER IDENTIFIER STRING CHAR_LITERAL
%right '='
%left LOGICAL_OR
%left LOGICAL_AND
%left EQ_OP
%left REL_OP
%left '+' '-'
%left '*' '/' '%'
%right '!' UMINUS ADDRESS
%nonassoc LOWER_THAN_ELSE
%nonassoc ELSE
%%
program: external_list ;
external_list: external_declaration | external_list external_declaration ;
external_declaration: function_definition | declaration ';' ;

function_definition: type_specifier function_name '(' parameters_opt ')' block ;
function_name: IDENTIFIER | MAIN ;
parameters_opt: %empty | VOID | parameter_list ;
parameter_list: parameter | parameter_list ',' parameter ;
parameter: type_specifier declarator ;

type_specifier: INT | FLOAT | CHAR | VOID ;
declaration: type_specifier init_declarator_list ;
init_declarator_list: init_declarator | init_declarator_list ',' init_declarator ;
init_declarator: declarator | declarator '=' assignment_expression ;
declarator: IDENTIFIER | IDENTIFIER '[' expression_opt ']' ;

block: '{' statements '}' ;
statements: %empty | statements statement ;
statement:
      declaration ';'
    | expression_opt ';'
    | PRINTF '(' arguments_opt ')' ';'
    | SCANF '(' argument_list ')' ';'
    | IF '(' expression ')' statement %prec LOWER_THAN_ELSE
    | IF '(' expression ')' statement ELSE statement
    | WHILE '(' expression ')' statement
    | DO statement WHILE '(' expression ')' ';'
    | FOR '(' for_initializer ';' expression_opt ';' expression_opt ')' statement
    | RETURN expression_opt ';'
    | BREAK ';'
    | CONTINUE ';'
    | block
    ;
for_initializer: %empty | declaration | expression ;
expression_opt: %empty | expression ;
arguments_opt: %empty | argument_list ;
argument_list: assignment_expression | argument_list ',' assignment_expression ;

expression: assignment_expression | expression ',' assignment_expression ;
assignment_expression:
      logical_or_expression
    | unary_expression '=' assignment_expression
    ;
logical_or_expression:
      logical_and_expression
    | logical_or_expression LOGICAL_OR logical_and_expression
    ;
logical_and_expression:
      equality_expression
    | logical_and_expression LOGICAL_AND equality_expression
    ;
equality_expression:
      relational_expression
    | equality_expression EQ_OP relational_expression
    ;
relational_expression:
      additive_expression
    | relational_expression REL_OP additive_expression
    ;
additive_expression:
      multiplicative_expression
    | additive_expression '+' multiplicative_expression
    | additive_expression '-' multiplicative_expression
    ;
multiplicative_expression:
      unary_expression
    | multiplicative_expression '*' unary_expression
    | multiplicative_expression '/' unary_expression
    | multiplicative_expression '%' unary_expression
    ;
unary_expression:
      postfix_expression
    | '!' unary_expression
    | '-' unary_expression %prec UMINUS
    | '+' unary_expression %prec UMINUS
    | '&' unary_expression %prec ADDRESS
    ;
postfix_expression:
      primary_expression
    | postfix_expression '[' expression ']'
    | postfix_expression '(' arguments_opt ')'
    | postfix_expression INC
    | postfix_expression DEC
    ;
primary_expression:
      NUMBER | FLOAT_NUMBER | IDENTIFIER | STRING | CHAR_LITERAL | '(' expression ')'
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
