%option noyywrap yylineno
%{
#include "minic_parser.h"
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
"int"                       return INT;
"float"                     return FLOAT;
"char"                      return CHAR;
"void"                      return VOID;
"main"                      return MAIN;
"if"                        return IF;
"else"                      return ELSE;
"while"                     return WHILE;
"do"                        return DO;
"for"                       return FOR;
"break"                     return BREAK;
"continue"                  return CONTINUE;
"printf"                    return PRINTF;
"scanf"                     return SCANF;
"return"                    return RETURN;
"=="|"!="                    return EQ_OP;
">="|"<="|">"|"<"            return REL_OP;
"&&"                        return LOGICAL_AND;
"||"                        return LOGICAL_OR;
"++"                        return INC;
"--"                        return DEC;
[0-9]+\.[0-9]+([eE][+-]?[0-9]+)? { yylval.text = copy_text(yytext); return FLOAT_NUMBER; }
[0-9]+                      { yylval.text = copy_text(yytext); return NUMBER; }
\"([^\"\\]|\\.)*\"          { yylval.text = copy_text(yytext); return STRING; }
\'([^\'\\]|\\.)\'            { yylval.text = copy_text(yytext); return CHAR_LITERAL; }
[A-Za-z_][A-Za-z0-9_]*      { yylval.text = copy_text(yytext); return IDENTIFIER; }
"//"[^\n]*                  ;
"/*"([^*]|\*+[^*/])*\*+"/"  ;
^[ \t]*#[^\n]*              ;
[ \t\r\n]+                  ;
.                           return yytext[0];
%%
