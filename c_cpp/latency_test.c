/**
 * Measures connection establishment and data transfer latency to the given
 * IP/port destination.
 */

#include <argp.h>
#include <arpa/inet.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static char prog_desc[] =
"Tests the latency to a destination IP.\
\vMeasures the connection setup time or round-trip time (of a successfull connection) \
to a destination IP";

/**
 * Program args struct used by parse_opt.
 */
struct prog_args
{
    char *dest_ip;
    int dest_port;
    bool measure_conn_setup_time;
    bool measure_rtt;
    int num_attempts;
};

static struct argp_option arg_options[] = {
    {"conn",         'c', 0,      0, "Measure connection setup time only"},
    {"rtt",          'r', 0,      0, "Measure RTT time only"},
    {"num-attempts", 'n', "NUM",  0, "Num attempts to make the specified measurements"},
    {"ip",           'i', "IP",   0, "Destination IP"},
    {"port",         'p', "PORT", 0, "Destination Port"},
    {NULL}
};

/**
 * Returns the difference between the given times in microseconds.
 */
long timeval_diff_us(struct timeval *start, struct timeval *end)
{
    return ((end->tv_sec - start->tv_sec)*1000000L + end->tv_usec) - start->tv_usec;
}

/**
 * Opens a TCP connection to the given ip/port and returns the connection
 * time (in microseconds) in the `connection_time` parameter.
 */
int open_tcp_connection(char *ip, int port, long *connection_time)
{
    int sock;
    struct timeval start_ts, end_ts;

    // Create socket
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        fprintf(stderr, "Could not create socket\n");
        perror("Error");
        return -1;
    }

    // Create address
    struct sockaddr_in dest_addr;
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(port);
    dest_addr.sin_addr.s_addr = inet_addr(ip);

    // Connect to server
    gettimeofday(&start_ts, NULL);
    if (connect(sock, (struct sockaddr *) &dest_addr, sizeof(dest_addr)) < 0) {
        fprintf(stderr, "Could not connect to %s:%d\n", ip, port);
        perror("Error");
        return -1;
    }
    gettimeofday(&end_ts, NULL);
    *connection_time = timeval_diff_us(&start_ts, &end_ts);

    return sock;
}

/**
 * Measures the average time taken to establish a connection.
 */
void measure_connection_time(char *ip, int port, int num_attempts)
{
    int sock;
    int i, num_successful_attempts;
    long connection_time = 0, curr_connection_time = 0;
    struct timespec wait_time = { .tv_sec = 0.5, .tv_nsec = 0 };

    printf("Attempting to establish connection %d times\n", num_attempts);
    for (i = 0; i < num_attempts; i++) {
        sock = open_tcp_connection(ip, port, &curr_connection_time);
        if (sock > 0) {
            connection_time += curr_connection_time;
            num_successful_attempts++;
            close(sock);
        }
        nanosleep(&wait_time, NULL);
    }

    printf("Avg connection time: %f us\n", ((float)connection_time)/num_successful_attempts);
}

/**
 * Measures the time it takes to send/recive data on open connections.
 */
void measure_round_trip_time(char *ip, int port, int num_attempts)
{
    int sock, retval, i, num_received_responses;
    long connection_time;
    struct timeval start_ts, end_ts;
    char to_send = 'A'; // The char (1 byte) to send
    char ack;
    long timediff;

    sock = open_tcp_connection(ip, port, &connection_time);
    if (sock < 0) {
        return;
    }
    printf("Connection establishment time: %ld us\n", connection_time);

    struct timeval timeout;
    timeout.tv_sec = 2;
    timeout.tv_usec = 0;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    printf("Sending %d messages (1 byte each) and waiting for responses\n", num_attempts);
    timediff = 0;
    num_received_responses = 0;
    for(i = 0; i < num_attempts; i++) {
	gettimeofday(&start_ts, NULL);
	send(sock, &to_send, sizeof(char), 0);
	retval = recv(sock, &ack, sizeof(char), 0);
	if (retval == -1) {
            fprintf(stderr, "Did not receive a response\n");
	    perror("Error");
	} else {
	    gettimeofday(&end_ts, NULL);
            timediff += timeval_diff_us(&start_ts, &end_ts);
            num_received_responses++;
	}
    }

    printf("RTT: %f us\n",((float)timediff)/num_received_responses);
    close(sock);
}

int validate_args(struct argp_state *state)
{
    struct prog_args *prog_args = state->input;
    if (!prog_args->dest_ip) {
        argp_error(state, "Destination IP not given");
    }
}

/**
 * Parses a single program arg option.
 */
static int parse_opt(int key, char *arg, struct argp_state *state)
{
    struct prog_args *prog_args = state->input;
    switch (key) {
        case 'c':
            prog_args->measure_conn_setup_time = true;
            prog_args->measure_rtt = false;
            break;
        case 'i':
            if (!arg) {
                argp_error(state, "error");
            }
            prog_args->dest_ip = arg;
            break;
        case 'n':
            prog_args->num_attempts = atoi(arg);
            break;
        case 'p':
            prog_args->dest_port = atoi(arg);
            break;
        case 'r':
            prog_args->measure_conn_setup_time = false;
            prog_args->measure_rtt = true;
            break;
        case ARGP_KEY_END:
            validate_args(state);
            break;
        default:
          return ARGP_ERR_UNKNOWN;
    }
    return 0;
}

/**
 * Parses the program args.
 */
int parse_args(int argc, char *argv[], struct prog_args* prog_args)
{
    /* Default values */
    prog_args->dest_ip = NULL;
    prog_args->dest_port = 0;
    prog_args->measure_conn_setup_time = false;
    prog_args->measure_rtt = false;
    prog_args->num_attempts = 0;

    struct argp argp_config = { arg_options, parse_opt, 0, prog_desc };
    return argp_parse(&argp_config, argc, argv, 0, 0, prog_args);
}

int main(int argc, char *argv[])
{
    int ret;
    struct prog_args prog_args;
    ret = parse_args(argc, argv, &prog_args);
    if (ret != 0) {
        fprintf(stderr, "Error parsing args. Return value: %d\n", ret);
        return ret;
    }

    printf("Destination server: %s:%d\n", prog_args.dest_ip, prog_args.dest_port);

    if (prog_args.measure_conn_setup_time) {
        measure_connection_time(prog_args.dest_ip, prog_args.dest_port, prog_args.num_attempts);
    } else if (prog_args.measure_rtt) {
        measure_round_trip_time(prog_args.dest_ip, prog_args.dest_port, prog_args.num_attempts);
    }
    return 0;
}
