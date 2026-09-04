%option noyywrap yylineno
%{
#include "minic_parser.h"
#include <stdlib.h>
#include <string.h>
static char *copy_text(const char *s) { size_t n = strlen(s) + 1; char *p = (char*)malloc(n); if (p) memcpy(p, s, n); return p; }
%}
%%
"int"                       return INT;
"main"                      return MAIN;
"if"                        return IF;
"else"                      return ELSE;
"while"                     return WHILE;
"print"                     return PRINT;
"return"                    return RETURN;
"=="|"!="|">="|"<="|">"|"<"  return COMPARE;
[0-9]+                      { yylval.number = atoi(yytext); return NUMBER; }
\"([^\"\\]|\\.)*\"          { yylval.text = copy_text(yytext); return STRING; }
[A-Za-z_][A-Za-z0-9_]*      { yylval.text = copy_text(yytext); return IDENTIFIER; }
"//"[^\n]*                  ;
[ \t\r\n]+                  ;
.                           return yytext[0];
%%
