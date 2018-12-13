/**
 * Tries to solve the tsp225.tsp file.
 */

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#include "load_file.h"
#include "structs.h"
#include "string_utils.h"

unsigned int load_cities(char *fname, node_t **cities, unsigned int *num_cities)
{
    FILE *f_tsp_data;
    char *line = NULL;
    size_t len = 0;
    ssize_t nread;
    bool reading_data = false;
    unsigned int retval, i, id;
    double x, y;

    f_tsp_data = fopen(fname, "r");
    if (f_tsp_data == NULL) {
        return 1;
    }

    *num_cities = 0;
    while ((nread = getline(&line, &len, f_tsp_data)) != -1) {
        // We should find the dimension key/value first
        if (starts_with(line, "DIMENSION")) {
            if (sscanf(line, "DIMENSION : %u", num_cities) == 0) {
                *num_cities = 0;
                retval = 2;
                goto cleanup;
            }
            *cities = (node_t *)malloc(*num_cities * sizeof(node_t));

        } else if (starts_with(line, "NODE_COORD_SECTION")) {
            reading_data = true;
            i = 0;

        } else if (starts_with(line, "EOF")) {
            reading_data = false;

        } else if (reading_data) {
            sscanf(line, "%u %lf %lf", &id, &x, &y);
            if (i < *num_cities) {
                (*cities)[i++] = (node_t){id, x, y};
            } else {
                fprintf(stderr, "Tried to add a city, but node array is full\n");
            }
        }
    }

    retval = 0;
cleanup:
    free(line);
    fclose(f_tsp_data);
    return retval;
}
