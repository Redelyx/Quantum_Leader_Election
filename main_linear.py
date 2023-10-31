from netqasm.logging.glob import get_netqasm_logger
from netqasm.runtime.application import default_app_instance
from netqasm.sdk import EPRSocket, Qubit
from netqasm.sdk.classical_communication.message import StructuredMessage
from netqasm.sdk.external import NetQASMConnection, Socket, simulate_application
from netqasm.sdk.toolbox import set_qubit_state

import math
from math import sqrt
from utils import Game, PRINT

import time 

start_time = time.time()

logger = get_netqasm_logger()

games = []

n_rounds = 0

def quantumLeaderElection(players, num=1, den=2):
    while len(players) > 1:
        if PRINT: print(players)
        p1 = players[0]
        p2 = players[1]
        w = weak_coin_flip(p1, p2, num/den)
        num+=1
        den+=1
        if w==p1:
            players.remove(p2)
        else:
            players.remove(p1)
    return players[0]

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

def weak_coin_flip(p1, p2, coeff):
    global n_rounds
    if PRINT: print(f"WCF: {p1} vs {p2} with probability {coeff}")
    n_rounds+=1
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