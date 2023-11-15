import sys
import time 
from multiprocessing import Process, Queue
from math import sqrt
from utils import greatest_power_of_two, DEBUG
from weakCoinFlip import weak_coin_flip

def distributor(findex, players, index, q):
    if findex == 0:
        ps = qleTournament(players[:index])
        q[0].put(ps)
        return ps
    else:
        ps = quantumLeaderElection(players[index:])
        q[1].put(ps)
        return ps        

def qleTournament(players, coeff = 1/2, mem = None):
    if DEBUG: print(players)
    while len(players) > 1:
        tmp_list = []
        for i in range(0, len(players), 2):
            tmp = weak_coin_flip(players[i], players[i+1], coeff)
            tmp_list.append(tmp)
        players = tmp_list
    return players[0]

def quantumLeaderElection(players, mem = None):
    n_players = len(players)
    if n_players == 1:
        return players[0]
    t = greatest_power_of_two(n_players)
    if t==n_players:
        return qleTournament(players)
    
    q = [Queue(), Queue()]
    for i in range(2):
        p = Process(target=distributor, args=(i, players, t, q))
        p.start()
    w1, w2 = q[0].get(), q[1].get()
    return qleTournament([w1,w2], t/n_players)

if __name__ == "__main__":
    p_name = "log_p"
    times = 1
    mem_timings = []
    probs = []
    players = [[],[]]

    if len(sys.argv) == 1:
        nParties = input("Number of parties:")
        times = int(input("Number of runs: "))
    if len(sys.argv) > 1:
        nParties = sys.argv[1]
    if len(sys.argv) > 2:
        times = int(sys.argv[2])
        print(f"The QLE will be executed {times} time\s.")

    for num in range(1, int(nParties)+1):
        label = ""
        while num > 0:
            num, remainder = divmod(num - 1, 26)
            label = chr(65 + remainder) + label
        players[0].append(label)
        players[1].append(0)
    print(players[0])

    with open("probs.txt", "a") as f:
        f.write("\n-------------------\n")
        f.write(f"Nodes: {nParties}\n")

    print(f"\n\n----- Start {p_name} - nodes: {nParties} -----")
    for i in range(times):
        print(f"\n----- Run n. {i+1}/{times} -----")
        start_time = time.time()

        w = quantumLeaderElection(players[0])

        finish_time = time.time()

        index_w = players[0].index(w)
        players[1][index_w] += 1

        final_time = finish_time - start_time
        mem_timings.append(final_time)

        print(f"The winner is {w}!")
        print("--- Execution time: %s seconds ---" % final_time )
        with open("test.txt", "a") as myfile:
            myfile.write(f"{nParties} - {p_name}: {str(final_time)}\n")

        if i%100==99:
            probs = []
            for l in range(len(players[0])):
                prob = float(players[1][l]/i)
                probs.append(prob)
            print(f"Nodes victory probabilities: {probs}.")
            with open("probs.txt", "a") as f:
                f.write(f"Runs: {i} - Probs: {probs}\n")

    probs = []
    for l in range(len(players[0])):
        prob = float(players[1][l]/times)
        probs.append(prob)
    print(f"Nodes victory probabilities: {probs}.")
    with open("probs.txt", "a") as f:
        f.write(f"Runs: {i} - Probs: {probs}\n")
