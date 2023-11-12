import sys
import time 
from utils import DEBUG
from weakCoinFlip import weak_coin_flip

def quantumLeaderElection(players, num=1, den=2):
    tmp = players.copy()
    while len(tmp) > 1:
        if DEBUG: print(tmp)
        p1 = tmp[0]
        p2 = tmp[1]
        w = weak_coin_flip(p1, p2, num/den)
        num+=1
        den+=1
        if w==p1:
            tmp.remove(p2)
        else:
            tmp.remove(p1)
    return tmp[0]

if __name__ == "__main__":
    p_name = "lin"
    times = 1
    mem_timings = []
    players = [[],[]]

    if len(sys.argv) == 1:
        nParties = input("Number of parties:")
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

    print(f"\n\n----- Start {p_name} -----")
    for i in range(times):
        print(f"\n----- Run n. {i+1}/{times+1} -----")
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

    if times>1:
        probs = []
        for i in range(len(players[0])):
            prob = float(players[1][i]/times)
            probs.append(prob)
        print(f"Nodes victory probabilities: {probs}.")

        sum = 0
        for i in range(times):
            sum += mem_timings[i]
        medium_time = sum/times
        print(f"Medium execution time: {medium_time}.")