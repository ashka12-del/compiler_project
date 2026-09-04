%option noyywrap yylineno caseless
%{
#include "minisql_parser.h"
#include <stdlib.h>
#include <string.h>
static char *copy_text(const char *s) { size_t n = strlen(s) + 1; char *p = (char*)malloc(n); if (p) memcpy(p, s, n); return p; }
%}
%%
"SELECT"                    return SELECT;
"FROM"                      return FROM;
"WHERE"                     return WHERE;
"SUM"                       return SUM;
">="|"<="|"!="|"<>"|"=="|"="|">"|"<" return COMPARE;
[0-9]+(\.[0-9]+)?            { yylval.text = copy_text(yytext); return VALUE; }
\'([^\'\\]|\\.)*\'            { yylval.text = copy_text(yytext); return VALUE; }
\"([^\"\\]|\\.)*\"          { yylval.text = copy_text(yytext); return VALUE; }
[A-Za-z_][A-Za-z0-9_]*      { yylval.text = copy_text(yytext); return IDENTIFIER; }
"--"[^\n]*                  ;
[ \t\r\n]+                  ;
.                           return yytext[0];
%%
