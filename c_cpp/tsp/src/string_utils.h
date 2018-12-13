#ifndef STRING_UTILS_H
#define STRING_UTILS_H

#include <stdbool.h>

bool starts_with(const char *a, const char *b);
bool str_eq(const char *a, const char *b);
void strip_new_line(char* str);

#endif
