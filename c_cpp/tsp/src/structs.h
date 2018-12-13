#ifndef STRUCTS_H
#define STRUCTS_H

typedef struct {
    char *progname;
    unsigned int progname_len;
    char *fname;
    unsigned int fname_len;
} program_args_t;

typedef struct {
    unsigned int id;
    double x;
    double y;
} node_t;

typedef struct {
    unsigned int *id;
    unsigned int len;
} route_t;


void free_program_args(program_args_t program_args);
void free_route(route_t route);

void route_copy(route_t *source, route_t *dest);
void* route_copy_of(route_t *xp);
void route_destroy(route_t *xp);

#endif
