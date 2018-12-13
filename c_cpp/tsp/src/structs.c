#include <stdlib.h>

#include "structs.h"

void free_program_args(program_args_t program_args)
{
    free(program_args.progname);
    free(program_args.fname);
}

void free_route(route_t route)
{
    free(route.id);
}

void route_copy(route_t *source, route_t *dest)
{
    unsigned int i;
    for (i = 0; i < source->len; ++i) {
        dest->id[i] = source->id[i];
    }
}

void* route_copy_of(route_t *route)
{
    unsigned int i;

    route_t *new_route = malloc(sizeof(route_t));
    new_route->len = route->len;
    new_route->id = malloc(route->len * sizeof(unsigned int));
    for (i = 0; i < route->len; ++i) {
        new_route->id[i] = route->id[i];
    }
    return new_route;
}

void route_destroy(route_t *route)
{
    free_route(*route);
    free(route);
}

