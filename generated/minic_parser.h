/* A Bison parser, made by GNU Bison 3.8.2.  */

/* Bison interface for Yacc-like parsers in C

   Copyright (C) 1984, 1989-1990, 2000-2015, 2018-2021 Free Software Foundation,
   Inc.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <https://www.gnu.org/licenses/>.  */

/* As a special exception, you may create a larger work that contains
   part or all of the Bison parser skeleton and distribute that work
   under terms of your choice, so long as that work isn't itself a
   parser generator using the skeleton or a modified version thereof
   as a parser skeleton.  Alternatively, if you modify or redistribute
   the parser skeleton itself, you may (at your option) remove this
   special exception, which will cause the skeleton and the resulting
   Bison output files to be licensed under the GNU General Public
   License without this special exception.

   This special exception was added by the Free Software Foundation in
   version 2.2 of Bison.  */

/* DO NOT RELY ON FEATURES THAT ARE NOT DOCUMENTED in the manual,
   especially those whose name start with YY_ or yy_.  They are
   private implementation details that can be changed or removed.  */

#ifndef YY_YY_GENERATED_MINIC_PARSER_H_INCLUDED
# define YY_YY_GENERATED_MINIC_PARSER_H_INCLUDED
/* Debug traces.  */
#ifndef YYDEBUG
# define YYDEBUG 0
#endif
#if YYDEBUG
extern int yydebug;
#endif

/* Token kinds.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
  enum yytokentype
  {
    YYEMPTY = -2,
    YYEOF = 0,                     /* "end of file"  */
    YYerror = 256,                 /* error  */
    YYUNDEF = 257,                 /* "invalid token"  */
    INT = 258,                     /* INT  */
    FLOAT = 259,                   /* FLOAT  */
    CHAR = 260,                    /* CHAR  */
    VOID = 261,                    /* VOID  */
    MAIN = 262,                    /* MAIN  */
    IF = 263,                      /* IF  */
    ELSE = 264,                    /* ELSE  */
    WHILE = 265,                   /* WHILE  */
    DO = 266,                      /* DO  */
    FOR = 267,                     /* FOR  */
    BREAK = 268,                   /* BREAK  */
    CONTINUE = 269,                /* CONTINUE  */
    PRINTF = 270,                  /* PRINTF  */
    SCANF = 271,                   /* SCANF  */
    RETURN = 272,                  /* RETURN  */
    EQ_OP = 273,                   /* EQ_OP  */
    REL_OP = 274,                  /* REL_OP  */
    LOGICAL_AND = 275,             /* LOGICAL_AND  */
    LOGICAL_OR = 276,              /* LOGICAL_OR  */
    INC = 277,                     /* INC  */
    DEC = 278,                     /* DEC  */
    NUMBER = 279,                  /* NUMBER  */
    FLOAT_NUMBER = 280,            /* FLOAT_NUMBER  */
    IDENTIFIER = 281,              /* IDENTIFIER  */
    STRING = 282,                  /* STRING  */
    CHAR_LITERAL = 283,            /* CHAR_LITERAL  */
    UMINUS = 284,                  /* UMINUS  */
    ADDRESS = 285,                 /* ADDRESS  */
    LOWER_THAN_ELSE = 286          /* LOWER_THAN_ELSE  */
  };
  typedef enum yytokentype yytoken_kind_t;
#endif

/* Value type.  */
#if ! defined YYSTYPE && ! defined YYSTYPE_IS_DECLARED
union YYSTYPE
{
#line 10 "grammar\\minic.y"
 char *text;

#line 98 "generated\\minic_parser.h"

};
typedef union YYSTYPE YYSTYPE;
# define YYSTYPE_IS_TRIVIAL 1
# define YYSTYPE_IS_DECLARED 1
#endif


extern YYSTYPE yylval;


int yyparse (void);


#endif /* !YY_YY_GENERATED_MINIC_PARSER_H_INCLUDED  */
