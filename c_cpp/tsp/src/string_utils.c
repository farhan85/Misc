#include <stdbool.h>
#include <stddef.h>
#include <string.h>

#include "string_utils.h"

bool starts_with(const char *a, const char *b)
{
    return strncmp(a, b, strlen(b)) == 0;
}

bool str_eq(const char *a, const char *b)
{
    unsigned int len_a = strlen(a);
    unsigned int len_b = strlen(b);
    return (len_a == len_b) && (strncmp(a, b, len_b) == 0);
}

void strip_new_line(char* str)
{
    size_t length = strlen(str);
    while ((length > 0) && (str[length - 1] == '\n'))
    {
        --length;
        str[length] ='\0';
    }
}
