#ifndef SIM_ANNEAL_H
#define SIM_ANNEAL_H

#include "structs.h"

void sim_anneal_solve_tsp(node_t *cities, unsigned int num_cities, route_t *tsp_solution);

#endif
