#ifndef ARGS_PARSER_H
#define ARGS_PARSER_H

#include "structs.h"

void print_usage(const char *progname);
int parse_args(int argc, char **argv, program_args_t *program_args);
int verify_args(program_args_t program_args);

#endif
