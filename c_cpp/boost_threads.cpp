/*
g++ boost_threads.cpp -I/path/to/boost/ -L/path/to/boost/lib -lboost_thread -lpthread -lboost_chrono
*/

#include <boost/chrono.hpp>
#include <boost/random/mersenne_twister.hpp>
#include <boost/random/uniform_int_distribution.hpp>
#include <boost/thread.hpp>
#include <iostream>

using std::cout;
using std::endl;

void worker(int thread_id, boost::mutex& mutex, const boost::function<int(void)>& random_num) {
    mutex.lock();
    cout << "Thread " << thread_id << " - starting" << endl;
    mutex.unlock();

    mutex.lock();
    int wait_time = random_num();
    cout << "Thread " << thread_id << " - waiting for " << wait_time << " seconds" << endl;
    mutex.unlock();

    boost::this_thread::sleep_for(boost::chrono::seconds(wait_time));
}

int main(void) {
    boost::random::mt19937 gen(std::time(0));
    boost::random::uniform_int_distribution<> dist(5, 10);
    auto random_num = [&dist, &gen]() -> int { return dist(gen); };

    boost::mutex mutex;
    boost::thread_group threads;
    for (int i = 0; i < 5; ++i) {
        boost::thread *t = new boost::thread(worker, i, boost::ref(mutex), boost::ref(random_num));
        threads.add_thread(t);
    }

    mutex.lock();
    cout << "Main Thread - Waiting for threads to finish" << endl;
    mutex.unlock();

    threads.join_all();
    cout << "Main Thread - Done" << endl;

    return 0;
}
