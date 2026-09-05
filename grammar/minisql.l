%option noyywrap yylineno caseless
%{
#include "minisql_parser.h"
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <io.h>
extern int _fileno(FILE *);
#define fileno _fileno
#endif
static char *copy_text(const char *s) { size_t n = strlen(s) + 1; char *p = (char*)malloc(n); if (p) memcpy(p, s, n); return p; }
%}
%%
"SELECT"                    return SELECT;
"FROM"                      return FROM;
"WHERE"                     return WHERE;
"DISTINCT"                  return DISTINCT;
"SUM"                       return SUM;
"COUNT"                     return COUNT;
"AVG"                       return AVG;
"MIN"                       return MIN;
"MAX"                       return MAX;
"AND"                       return AND;
"OR"                        return OR;
"ORDER"                     return ORDER;
"BY"                        return BY;
"ASC"                       return ASC;
"DESC"                      return DESC;
"LIMIT"                     return LIMIT;
">="|"<="|"!="|"<>"|"=="|"="|">"|"<" return COMPARE;
[0-9]+(\.[0-9]+)?            { yylval.text = copy_text(yytext); return VALUE; }
\'([^\'\\]|\\.)*\'            { yylval.text = copy_text(yytext); return VALUE; }
\"([^\"\\]|\\.)*\"          { yylval.text = copy_text(yytext); return VALUE; }
[A-Za-z_][A-Za-z0-9_]*      { yylval.text = copy_text(yytext); return IDENTIFIER; }
"--"[^\n]*                  ;
[ \t\r\n]+                  ;
.                           return yytext[0];
%%
