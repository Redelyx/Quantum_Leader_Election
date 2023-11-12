from netqasm.sdk.classical_communication.message import StructuredMessage
from netqasm.runtime.application import default_app_instance
from netqasm.sdk import EPRSocket, Qubit
from netqasm.sdk.external import NetQASMConnection, Socket, simulate_application, get_qubit_state
from netqasm.sdk.toolbox import set_qubit_state

import math
from math import sqrt
from utils import Game, DEBUG, PRINT

game = None

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
    global game
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
    winner = game.winner
    if PRINT:
        print(f"WCF: {p1} vs {p2} with probability {coeff}. Winner is {winner}")
    return winner

