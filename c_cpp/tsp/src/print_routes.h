#ifndef PRINT_ROUTES_H
#define PRINT_ROUTES_H

#include <stdio.h>
#include "structs.h"

void print_route(const route_t *route);
void print_route_with_cities(const route_t *route, const node_t *cities);
void print_route_gnuplot(FILE *fp, const node_t *cities, unsigned int num_cities);

#endif
