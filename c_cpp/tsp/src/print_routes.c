#include <stdio.h>

#include "print_routes.h"
#include "structs.h"

void print_route(const route_t *route)
{
    unsigned int i;
    for (i = 0; i < route->len; i++) {
        printf("%3d\n", route->id[i]);
    }
}

void print_route_with_cities(const route_t *route, const node_t *cities)
{
    unsigned int i, city_id;
    for (i = 0; i < route->len; i++) {
        city_id = route->id[i];
        printf("%3d %3.2f %3.2f\n", city_id, cities[city_id].x, cities[city_id].y);
    }
}

void print_route_gnuplot(FILE *fp, const node_t *cities, unsigned int num_cities)
{
    unsigned int i;
    for (i = 0; i < num_cities; i++) {
        fprintf(fp, "%3.2f %3.2f %3d\n", cities[i].x, cities[i].y, cities[i].id);
    }
}
