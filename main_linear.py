from netqasm.logging.glob import get_netqasm_logger
from netqasm.runtime.application import default_app_instance
from netqasm.sdk import EPRSocket, Qubit
from netqasm.sdk.classical_communication.message import StructuredMessage
from netqasm.sdk.external import NetQASMConnection, Socket, simulate_application
from netqasm.sdk.toolbox import set_qubit_state

import sys
import math
from math import sqrt
from utils import Game, DEBUG, PRINT

import time 

logger = get_netqasm_logger()

games = []

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

def run_sender(sender, receiver, coeff = 1/2):
    # Create a socket to send classical information
    socket = Socket(sender, receiver)

    # Create a EPR socket for entanglement generation
    epr_socket = EPRSocket(receiver)

    # Initialize the connection to the backend
    epr_socket = EPRSocket(receiver)
    with NetQASMConnection(sender, epr_sockets=[epr_socket]) as sender:
        # Create a qubit to teleport
        q = Qubit(sender)

        theta = 2 * math.acos(sqrt(coeff))
        phi = 0

        set_qubit_state(q, phi, theta)

        # Create EPR pairs
        epr = epr_socket.create_keep()[0]

        # Teleport
        q.cnot(epr)
        q.H()
        m1 = q.measure()
        m2 = epr.measure()

    socket.send_structured(StructuredMessage("Corrections", (int(m1), int(m2))))

def run_receiver(receiver, sender):
    global games
    winner = -1

    # Create a socket to recv classical information
    socket = Socket(receiver, sender)
    # Setup a connection to QNodeOS (quantum node controller)
    epr_socket = EPRSocket(sender)
    with NetQASMConnection(receiver, epr_sockets=[epr_socket]) as receiver_conn:
        epr = epr_socket.recv_keep()[0]
        receiver_conn.flush()

        # Get the corrections
        m1, m2 = socket.recv_structured().payload
        if m2 == 1:
            epr.X()
        if m1 == 1:
            epr.Z()

        receiver_conn.flush()

        m=epr.measure()

    if m == 0:
        winner = sender
    else:
        winner = receiver

    game = Game([sender, receiver], winner)
    if DEBUG: print(f"WCF: Winner is {winner}")
    games.append(game)


def post_function(backend):
    if DEBUG: print("--------")

def weak_coin_flip(p1, p2, coeff):
    if DEBUG: print(f"WCF: {p1} vs {p2} with probability {coeff}")
    def wcf_sender():
        run_sender(p1, p2, coeff)
    def wcf_receiver():
        run_receiver(p2, p1)

    app_instance = default_app_instance(
        [
            (p1, wcf_sender),
            (p2, wcf_receiver),
        ]
    )
    simulate_application(
        app_instance,
        use_app_config=False,
        post_function=post_function,
        enable_logging=False,
    )
    winner = games[len(games)-1].winner
    if PRINT:
        print(f"WCF: {p1} vs {p2} with probability {coeff}. Winner is {winner}")
    return winner

if __name__ == "__main__":
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

    for i in range(times):
        print(f"\n----- Run n. {i+1} -----")
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
            myfile.write(f"{nParties} - lin: {str(final_time)}\n")

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