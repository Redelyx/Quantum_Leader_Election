from netqasm.logging.glob import get_netqasm_logger
from netqasm.runtime.application import default_app_instance
from netqasm.sdk import EPRSocket, Qubit
from netqasm.sdk.classical_communication.message import StructuredMessage
from netqasm.sdk.external import NetQASMConnection, Socket, simulate_application
from netqasm.sdk.toolbox import set_qubit_state

import math
import time 
from multiprocessing import Pool, Process, Queue
from math import sqrt
from utils import greatest_power_of_two, Game, PRINT

logger = get_netqasm_logger()

games = []

n_rounds = 0

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
    if PRINT: print(f"WCF: Winner is {winner}")
    games.append(game)


def post_function(backend):
    if PRINT: print("--------")

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
    if PRINT: print(players)
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
    else:
        q = []
        q.append(Queue())
        q.append(Queue())
        for i in range(2):
            p = Process(target=distributor, args=(i, players, t, q))
            p.start()
        w1, w2 = q[0].get(), q[1].get()
        return qleTournament([w1,w2], t/n_players)

def weak_coin_flip(p1, p2, coeff):
    global n_rounds
    if PRINT: print(f"WCF: {p1} vs {p2} with probability {coeff}")
    n_rounds += 1
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
    print(f"WCF: {p1} vs {p2} with probability {coeff}. Winner is {winner}")
    return winner

if __name__ == "__main__":
    nParties = input("Number of parties:")
    players = []
    for num in range(1, int(nParties)+1):
        label = ""
        while num > 0:
            num, remainder = divmod(num - 1, 26)
            label = chr(65 + remainder) + label
        players.append(label)
    print(players)

    start_time = time.time()
    
    w = quantumLeaderElection(players)

    finish_time = time.time()

    print(f"The winner is {w}! Total WCF rounds: {n_rounds}")
    print("--- Execution time: %s seconds ---" % (finish_time - start_time))