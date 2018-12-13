/**
 * Uses Simulated Annealing to find solutions to the TSP.
 */

#include <math.h>
#include <string.h>
#include <stdio.h>

#include <gsl/gsl_math.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_rng.h>
#include <gsl/gsl_siman.h>

#include "print_routes.h"
#include "sim_anneal.h"
#include "structs.h"

/* set up parameters for this simulated annealing run */
#define N_TRIES 200             /* how many points do we try before stepping */
#define ITERS_FIXED_T 2000      /* how many iterations for each T? */
#define STEP_SIZE 1.0           /* max step size in random walk */
#define K 1.0                   /* Boltzmann constant */
#define T_INITIAL 5000.0        /* initial temperature */
#define MU_T 1.002              /* damping factor for temperature */
#define T_MIN 5.0e-1

gsl_siman_params_t params = {N_TRIES, ITERS_FIXED_T, STEP_SIZE, K, T_INITIAL,
                             MU_T, T_MIN};

// No need to recompute the same distance more than once
double **distance_matrix;

/* distance between two cities */
double dist_between_nodes(node_t c1, node_t c2)
{
    double dx = c1.x - c2.x;
    double dy = c1.y - c2.y;
    return sqrt((dx * dx) + (dy * dy));
}

void init_distance_matrix(node_t *tsp_cities, unsigned int num_cities)
{
    unsigned int i, j;
    double dist;

    distance_matrix = (double **)malloc(num_cities * sizeof(double *)); 
    for (i = 0; i < num_cities; ++i) {
        distance_matrix[i] = (double *)malloc(num_cities * sizeof(double)); 
    }

    for (i = 0; i < num_cities; ++i) {
        for (j = 0; j < num_cities; ++j) {
            if (i == j) {
                dist = 0;
            } else {
                dist = dist_between_nodes(tsp_cities[i], tsp_cities[j]);
            }
            distance_matrix[i][j] = dist;
        }
    }
}

void free_distance_matrix(unsigned int num_cities)
{
    unsigned int i;

    for (i = 0; i < num_cities; ++i) {
        free(distance_matrix[i]);
    }
    free(distance_matrix);
}

double dist_between_routes(void *solution1, void *solution2)
{
    route_t *route1 = (route_t *) solution1;
    route_t *route2 = (route_t *) solution2;
    double distance = 0;
    unsigned int i;

    for (i = 0; i < route1->len; ++i) {
        distance += ((route1->id[i] == route2->id[i]) ? 0 : 1);
    }

    return distance;
}

double energy_func_total_dist(void *xp)
{
    route_t *route = (route_t *) xp;
    double total_dist = 0;
    unsigned int i;

    for (i = 0; i < route->len; ++i) {
        total_dist += distance_matrix[route->id[i]][route->id[(i + 1) % route->len]];
    }

    return total_dist;
}

void rand_neighbour(const gsl_rng *r, void *xp, double step_size)
{
    int pos1, pos2, temp_id;
    route_t *route = (route_t *) xp;
    step_size = 0 ; /* prevent warnings about unused parameter */

    /* pick the two cities to swap in the route. Leave the first city fixed */
    pos1 = (gsl_rng_get(r) % (route->len - 1)) + 1;
    do {
        pos2 = (gsl_rng_get(r) % (route->len - 1)) + 1;
    } while (pos2 == pos1);

    temp_id = route->id[pos1];
    route->id[pos1] = route->id[pos2];
    route->id[pos2] = temp_id;
}

void gsl_print_route(void *xp)
{
    //print_route((route_t *) xp);
}

void gsl_route_copy(void *source, void *dest)
{
    route_copy((route_t *) source, (route_t *) dest);
}

void* gsl_route_copy_of(void *xp)
{
    return route_copy_of((route_t *) xp);
}

void gsl_route_destroy(void *xp)
{
    route_destroy((route_t *) xp);
}

void sim_anneal_solve_tsp(node_t *cities, unsigned int num_cities, route_t *tsp_solution)
{
    unsigned int i;

    gsl_rng *rng = gsl_rng_alloc(gsl_rng_env_setup());

    init_distance_matrix(cities, num_cities);

    for (i = 0; i < num_cities; ++i) {
        tsp_solution->id[i] = i;
    }

    gsl_siman_solve(rng, tsp_solution, energy_func_total_dist, rand_neighbour,
                    dist_between_routes, gsl_print_route, gsl_route_copy,
                    gsl_route_copy_of, gsl_route_destroy, 0, params);

    printf("Total distance: %f\n", energy_func_total_dist(tsp_solution));

    free_distance_matrix(num_cities);
    gsl_rng_free(rng);
}
