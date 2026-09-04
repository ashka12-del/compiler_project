@echo off
setlocal
cd /d "%~dp0"
if not exist generated mkdir generated
if not exist bin mkdir bin

set "FLEX=tools\winflexbison\win_flex.exe"
set "BISON=tools\winflexbison\win_bison.exe"

echo Building MiniC Flex/Bison parser...
"%BISON%" -d -o generated\minic_parser.c grammar\minic.y || goto :error
"%FLEX%" -o generated\minic_lexer.c grammar\minic.l || goto :error
gcc -std=c11 -Igenerated generated\minic_parser.c generated\minic_lexer.c -o bin\minic_parser.exe || goto :error

echo Building MiniSQL Flex/Bison parser...
"%BISON%" -d -o generated\minisql_parser.c grammar\minisql.y || goto :error
"%FLEX%" -o generated\minisql_lexer.c grammar\minisql.l || goto :error
gcc -std=c11 -Igenerated generated\minisql_parser.c generated\minisql_lexer.c -o bin\minisql_parser.exe || goto :error

echo Flex/Bison parsers built successfully.
exit /b 0

:error
echo Parser build failed.
exit /b 1

