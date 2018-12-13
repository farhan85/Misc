/**
 * Calculates if a given number is prime or not by using "The Sieve of Eratosthenes"
 * technique.
 *
 * \author Farhan Ahammed
 */

#include <errno.h>
#include <limits.h>
#include <math.h>
#include <stdlib.h>
#include <stdio.h>

// Windows
#include <sys/time.h>
// linux
#include <time.h>


#define ERROR_INCORRECT_ARGS          1
#define ERROR_STR_TO_NUM_CONV_FAILED  2
#define ERROR_MEMORY_NOT_ALLOCATED    3


/**
 * Returns an array of unsigned ints (bit array) with the first 'num' bits set to 1.
 *
 * eg. new_sieve(3)  =    7 =           0111b
 *     new_sieve(12) = 4095 = 1111 1111 1111b
 */
unsigned int* new_sieve(unsigned long num)
{
    unsigned int *sieve, i;
    unsigned long size;

    /* The size of the bit array */
    size = num/(sizeof(unsigned int)*CHAR_BIT) + 1;

    sieve = (unsigned int*)malloc((size)*sizeof(unsigned int));
    if (sieve == NULL)
    {
        printf("Error: Could not create the sieve\n");
        exit(ERROR_MEMORY_NOT_ALLOCATED);
    }
    /* Set all the bits in the array */
    for (i = 0; i < size; ++i)
    {
        sieve[i] = UINT_MAX;
    }

    return sieve;
}


/**
 * Returns 1 (true) if the specified number is a prime number, 0 (false)
 * otherwise.
 */
int is_prime(unsigned long num)
{
    unsigned int *sieve;
    char num_bit;
    unsigned long start_pos, i, ptr_size;
    ldiv_t qr;

    /* Edge cases */
    if ((num == 0) || (num == 1)) return 0;

    /* The sieve we'll use to determine if num is a prime or not. */
    sieve = new_sieve(num);
    ptr_size = sizeof(sieve[0])*CHAR_BIT;

    /* sieve[2] represents the number 2. We only have to find multiples/factors up to sqrt(num). */
    for (start_pos = 2; start_pos <= (unsigned long)sqrt(num); ++start_pos)
    {
        /* If this number is cleared, then so will all of its multiples, in which
           case there is nothing needed to be done. */
        qr = ldiv(start_pos, ptr_size);
        if (( sieve[qr.quot] & (1 << qr.rem) ) != 0) {
            /* Clear all numbers that are multiples of 'sieve[start_pos]' */
            for (i = start_pos; i <= num; i = i + start_pos)
            {
                qr = ldiv(i, ptr_size);
                sieve[qr.quot] &= ~(1 << qr.rem);

                if (i == num)
                {
                    /* We've cleared 'sieve[num]' we now know it's not a prime number */
                    break;
                }
            }

            if (i == num)
            {
                printf("Divisible by %lu\n", start_pos);
                /* We've cleared 'sieve[num]' we now know it's not a prime number */
                break;
            }
        }
    }

    /* Get the value of the bit at position 'num' */
    qr = ldiv(num, ptr_size);
    num_bit = ( sieve[qr.quot] & (1 << qr.rem) ) != 0;

    free(sieve);

    // 'num' is a prime if the bit 'sieve[num]' was still set.
    return num_bit;
}


void print_time(const char *heading, double time_ms)
{
    int ms, s, m, h;
    div_t qr;

    qr = div(time_ms, 1000);
    ms = qr.rem;
    qr = div(qr.quot, 60);
    s  = qr.rem;
    qr = div(qr.quot, 60);
    m  = qr.rem;
    h  = qr.quot;

    printf("%10s: %dh %2dm %2d.%03ds\n", heading, h, m, s, ms);
}


/**
 * Computes whether or not the given number is a prime number, displaying the
 * result on screen, including information on the computation time taken.
 */
void compute_prime(unsigned long num)
{
    int b_isprime;
    clock_t cpu_start, cpu_end;
    double cpu_diff;
    struct timeval real_start, real_end, real_diff;

    gettimeofday(&real_start, NULL);
    cpu_start = clock();
    b_isprime = is_prime(num);
    cpu_end = clock();
    gettimeofday(&real_end, NULL);

    if (b_isprime)
    {
        printf("%lu is a prime number\n", num);
    }
    else
    {
        printf("%lu is not a prime number\n", num);
    }
    printf("\n");

    cpu_diff = (double)(cpu_end - cpu_start);
    print_time("CPU Time", cpu_diff);

    /* Get overall time difference */
    if (real_start.tv_usec < real_end.tv_usec)
    {
        /* "Carry the 1" into the microseconds column so we can perform the subtraction. */
        real_diff.tv_usec += 1000000;
        real_diff.tv_sec -= 1;
    }
    real_diff.tv_sec = real_end.tv_sec - real_start.tv_sec;
    real_diff.tv_usec = real_end.tv_usec - real_start.tv_usec;
    print_time("Real Time", (double)real_diff.tv_sec*1000 + (double)real_diff.tv_usec/1000);
}


int main(int argc, char **argv)
{
    unsigned long num;

    if (argc < 2)
    {
        printf("Usage: %s <int>\n", argv[0]);
        return ERROR_INCORRECT_ARGS;
    }

    errno = 0;
    num = strtoul(argv[1], NULL, 10);

    if (errno != 0)
    {
        printf("ERROR. Could not convert %s to a long. errno:%d\n", argv[1], errno);
        return ERROR_STR_TO_NUM_CONV_FAILED;
    }

    compute_prime(num);

    return 0;
}
