import math
import random


def get_clusters(subs, include_comments=False):
    lines = sorted(line for line in subs if not line.is_comment or include_comments)
    i = 0

    while i < len(lines):
        start = lines[i].start
        end = lines[i].end
        cluster_lines = [lines[i]]

        while True:
            i += 1
            if i < len(lines) and lines[i].start <= end:
                end = max(end, lines[i].end)
                cluster_lines.append(lines[i])
            else:
                break

        yield start, end, cluster_lines


def discretize(clusters, unit=100):
    times = []

    for start, end, _ in clusters:
        times.extend(range(start//unit, end//unit))

    return times

def simulated_annealing_solver(x0, move, objective, t0, iterations, decay):
    t = t0
    x, fx = x0, objective(x0)
    bestx, bestfx = x, fx

    for i in range(iterations):
        newx = move(x, t)
        newfx = objective(newx)
        delta = (newfx - fx)**2

        if newfx < fx or math.exp(-delta/t) > random.random():
            x, fx = newx, newfx # keep the new state

            if fx < bestfx:
                bestx, bestfx = x, fx

        yield i, t, x, fx
        t *= decay

    yield None, None, bestx, bestfx

def solver_driver(ref_subs, subs, unit, t0, decay, iterations):
    ref_times = set(discretize(get_clusters(ref_subs), unit))
    times = set(discretize(get_clusters(subs), unit))

    x0 = 0
    move = lambda x, t: random.gauss(x, t)
    objective = lambda delta: len(ref_times ^ set(t+delta//unit for t in times))

    for data in simulated_annealing_solver(x0, move, objective, t0, iterations=iterations, decay=decay):
        yield data
