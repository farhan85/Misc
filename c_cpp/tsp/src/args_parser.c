#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "args_parser.h"
#include "structs.h"

void print_usage(const char *progname)
{
    printf("Usage: %s -f FILENAME\n", progname);
    printf("Searches for solutions to TSP problems using simulated annealing\n");
    printf("\n");
    printf("  ­f, ­­file FILENAME  Tsplib input file\n");
    printf("  ­h, ­­help           Show this help\n");
}

/**
 * Parses the program arguments and stores the results in the `program_args_t`
 * struct pointed to by `program_args`.
 *
 * \param argc Arg count.
 * \param argv String array of program args.
 * \param program_args Pointer to the struct where results should be saved.
 * \return 0 If the args were successfully parsed. -1 If we should exit the
 *         program with EXIT_SUCCESS (e.g. The user specified `--help`).
 *         -2 If there was a problem and the program should exit with EXIT_FAILURE.
 */
int parse_args(int argc, char **argv, program_args_t *program_args)
{
    int c, long_opt_idx;
    unsigned int len;
    const char *short_opt= "hf:";
    struct option long_opt[] = {
        {"help", no_argument,       NULL, 'h'},
        {"file", required_argument, NULL, 'f'},
        {NULL,   0,                 NULL, 0  }
    };

    // Initialise
    len = strlen(argv[0]);
    program_args->progname = malloc(len);
    strncpy(program_args->progname, argv[0], len);
    program_args->progname_len = len;

    program_args->fname = NULL;
    program_args->fname_len = 0;

    // Now parse the args
    while ((c = getopt_long(argc, argv, short_opt, long_opt, &long_opt_idx)) != -1) {
        switch (c) {
            case 'f':
                len = strlen(optarg);
                program_args->fname = malloc(len);
                strncpy(program_args->fname, optarg, len);
                program_args->fname_len = len;
                break;

            case 'h':
                print_usage(program_args->progname);
                return -1;

            case '?':
                // getopt_long already printed an error message
                print_usage(program_args->progname);
                return -2;

            default:
                fprintf(stderr, "Invalid option: %c\n", c);
                print_usage(argv[0]);
                return -2;
        }
    }

    return 0;
}

int verify_args(program_args_t program_args)
{
    if (program_args.fname == NULL || program_args.fname_len == 0) {
        fprintf(stderr, "Missing fname\n");
        print_usage(program_args.progname);
        return -1;
    }
    return 0;
}
