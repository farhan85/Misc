#include <stdlib.h>
#include <stdio.h>

// http://www.purposeful.co.uk/software/gopt
#include <gopt.h>
#include <gsl/gsl_poly.h>


struct option options[5] = {
    { .short_name = 'a', .long_name = "x1",   .flags = GOPT_ARGUMENT_REQUIRED },
    { .short_name = 'b', .long_name = "x2",   .flags = GOPT_ARGUMENT_REQUIRED },
    { .short_name = 'c', .long_name = "x3",   .flags = GOPT_ARGUMENT_REQUIRED },
    { .short_name = 'h', .long_name = "help", .flags = GOPT_ARGUMENT_FORBIDDEN },
    { .flags = GOPT_LAST }
};
#define OPT_A 0
#define OPT_B 1
#define OPT_C 2
#define OPT_HELP 3


void print_usage(char *progname)
{
    printf("Usage: %s [-a|--x1 <num>] [-b|--x2 <num>] [-c|--x3 <num>] [-h|--help]\n", progname);
    printf("\n");
    printf("Solves the quadratic equation ax^2 + bx +c = 0\n");
    printf("\n");
    printf("Program arguments:\n");
    printf("  a, x1    Coefficient of x^2 [default: 1]\n");
    printf("  b, x2    Coefficient of x [default: 2]\n");
    printf("  c, x3    Coefficient of x^0 (i.e. the constant) [default: 0.5]\n");
    printf("  h, help  Displays this help\n");
    printf("\n");
    printf("Examples:\n");
    printf("  // Solve the equation x^2 - 6x -16 = 0\n");
    printf("  > %s -b -6 -c -16\n", progname);
    printf("  Solving for: (1.00)x^2 + (-6.00)x + (-16.00) = 0\n");
    printf("  Found 2 roots: -2.00, 8.00\n");
}

void solve_quadratic(double a, double b, double c)
{
    double x0, x1;
    int num_roots;

    printf("Solving for: (%.2f)x^2 + (%.2f)x + (%.2f) = 0\n", a, b, c);
    num_roots = gsl_poly_solve_quadratic(a, b, c, &x0, &x1);

    switch (num_roots) {
        case 0:
            printf("Quadratic equation has no solutions\n");
            break;
        case 1:
            printf("Found 1 root: x = %.2f\n", x0);
            break;
        case 2:
            printf("Found 2 roots: x = %.2f, %.2f\n", x0, x1);
            break;
        default:
            printf("Invalid number of roots: %d\n", num_roots);
            break;
    }
}


int main(int argc, char **argv)
{
    double a, b, c;

    argc = gopt(argv, options);
    if (options[OPT_HELP].count)
    {
        print_usage(argv[0]);
        exit(EXIT_SUCCESS);
    }

    a = options[OPT_A].argument ? atof(options[OPT_A].argument) : 1;
    b = options[OPT_B].argument ? atof(options[OPT_B].argument) : 2;
    c = options[OPT_C].argument ? atof(options[OPT_C].argument) : 0.5;

    solve_quadratic(a, b, c);
    return 0;
}
