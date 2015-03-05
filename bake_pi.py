#!/usr/bin/env python

from __future__ import print_function

from multiprocessing import Process, Queue, Value
from collections import namedtuple, defaultdict
from decimal import Decimal, getcontext, InvalidOperation
from random import uniform


# Size of the queue for randomly generated points
# Useful for when points are generated faster than they are tested
POINTS_QUEUE_THRESHOLD = 1e5

# Number of tested points saved by a tester worker before they are returned
TESTER_QUEUE_THRESHOLD = 1e4


# Clean way of representing a point
Point = namedtuple('Point', ('x', 'y'))

# Initial precision (expanded as needed...very slowly)
getcontext().prec = 8


def random_point():
    """
    Generate a random point uniformly distributed between (-1, -1) and (1, 1).
    """
    return Decimal(uniform(-1, 1))


def generate_points(queue):
    """
    Generate points (run in a separate process) until queue is full.
    """
    while True:
        queue.put(Point(random_point(), random_point()))

        while queue.full():
            pass


def sum_results(queue, hits, trials):
    """
    Aggregate the hits and trials counts from tester processes.
    """
    while True:
        (new_hits, new_trials) = queue.get()

        with hits.get_lock(), trials.get_lock():
            hits.value += new_hits
            trials.value += new_trials


# Cache the frequently used power function
power = getcontext().power


def in_circle(point):
    """
    Test if point is within a circle centered at the origin with radius 1.
    """
    return (power(point.x, 2) + power(point.y, 2)) < 1


def test_points(points, results):
    """
    Test point location and temporarily store the result (returned via queue
    to the counter process) - run in a separate process.
    """
    while True:
        hits, trials = 0, 0

        while True:
            point = points.get()
            trials += 1

            if in_circle(point):
                hits += 1

            if trials == TESTER_QUEUE_THRESHOLD:
                results.put((hits, trials))
                break


# four is cached since it is used to frequently
four = Decimal(4)


def calculate_pi(hits, trials):
    """
    Calculate pi from monte carlo simulation results.
    """
    try:
        with hits.get_lock(), trials.get_lock():
            # Ratio must be scaled by area of circle (coef) / area of square
            return four * (Decimal(hits.value) / Decimal(trials.value))

    except InvalidOperation:
        return Decimal(0)


def print_pi(hits, trials):
    """
    Print approximated pi to stdout in a way that it can be updated. Also,
    update the precision of Decimal if the approxmation is approaching
    the current max precision.
    """
    calculated_pi = str(calculate_pi(hits, trials))

    new_similar_digits = defaultdict(int)

    if print_pi.last_pi:
        for i, (c, l) in enumerate(zip(calculated_pi, print_pi.last_pi)):
            if c == l:
                new_similar_digits[i] = print_pi.similar_digits[i] + 1
            else:
                if (getcontext().prec / 2) < (i - 1):
                    getcontext().prec *= 2

                break

    print_pi.similar_digits, print_pi.last_pi = \
        new_similar_digits, calculated_pi

    print('\r{}'.format(calculated_pi), end='')


print_pi.last_pi, print_pi.similar_digits = None, defaultdict(int)


if __name__ == '__main__':
    hits, trials = Value('i', 0), Value('i', 0)
    points, results = Queue(POINTS_QUEUE_THRESHOLD), Queue()

    generator = Process(target=generate_points, args=(points,))
    counter = Process(target=sum_results, args=(results, hits, trials))
    tester = Process(target=test_points, args=(points, results))

    generator.start()
    tester.start()
    counter.start()

    try:
        while True:
            print_pi(hits, trials)

    except KeyboardInterrupt:
        print('')

    finally:
        generator.terminate()
        tester.terminate()
        counter.terminate()
