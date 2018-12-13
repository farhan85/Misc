/**
 * Tries to solve the tsp225.tsp file.
 */

#include <stdlib.h>

#include "args_parser.h"
#include "load_file.h"
#include "print_routes.h"
#include "sim_anneal.h"

node_t *tsp_cities = NULL;        // Array of TSP cities.
unsigned int tsp_cities_len = 0;  // Length of TSP cities array.


int main(int argc, char **argv)
{
    program_args_t program_args;
    route_t tsp_solution;
    int retval;

    retval = parse_args(argc, argv, &program_args);
    if (retval == -1) { return 0; }
    if (retval !=  0) { return 1; }

    retval = verify_args(program_args);
    if (retval !=  0) { return 1; }

    printf("Loading TSP data from: %s\n", program_args.fname);
    retval = load_cities(program_args.fname, &tsp_cities, &tsp_cities_len);
    if (retval != 0) {
        printf("Error loading cities: %d\n", retval);
        return 1;
    }

    printf("Num Cities: %u\n", tsp_cities_len);
    printf("\n");

    tsp_solution.len = tsp_cities_len;
    tsp_solution.id = malloc(tsp_cities_len * sizeof(unsigned int));

    sim_anneal_solve_tsp(tsp_cities, tsp_cities_len, &tsp_solution);

    //printf("--------------- GNU plot edges.dat ---------------\n");
    //print_route_gnuplot(stdout, tsp_cities, tsp_cities_len);
    //printf("--------------------------------------------------\n");
    print_route_with_cities(&tsp_solution, tsp_cities);

    free_route(tsp_solution);
    free(tsp_cities);
    free_program_args(program_args);
    return  0;
}
