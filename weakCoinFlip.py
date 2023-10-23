from netqasm.logging.glob import get_netqasm_logger, set_log_level
from netqasm.logging.output import get_new_app_logger
from netqasm.runtime.settings import Simulator, get_simulator
from netqasm.sdk.classical_communication.message import StructuredMessage
from netqasm.runtime.application import default_app_instance
from netqasm.sdk import EPRSocket, Qubit
from netqasm.sdk.external import NetQASMConnection, Socket, simulate_application, get_qubit_state
from netqasm.sdk.toolbox import set_qubit_state
from netqasm.sdk.toolbox.sim_states import get_fidelity, qubit_from, to_dm
from netsquid import qubits
from netsquid.qubits.qubitapi import *
from netsquid.qubits.qformalism import *
from netsquid.qubits import operators as ops
from netsquid.qubits import ketstates
from netsquid.qubits import Stabilizer

import math
from math import sqrt
from game import Game
from utils import greatest_power_of_two, is_power_of_two
winner_a=0
winner_b=0

logger = get_netqasm_logger()

def run_sender(sender, receiver, coeff = 1/2):
    # Create a socket to send classical information
    socket = Socket(sender, receiver)

    # Create a EPR socket for entanglement generation
    epr_socket = EPRSocket(receiver)

    #print(f"{sender} will start to teleport a qubit to {receiver}")

    # Initialize the connection to the backend
    epr_socket = EPRSocket(receiver)
    with NetQASMConnection(sender, epr_sockets=[epr_socket]) as sender:
        # Create a qubit to teleport
        q = Qubit(sender)

        theta = 2 * math.acos(coeff)
        phi = 0
        set_qubit_state(q, phi, theta)

        #check with netsquid
        '''q2 = qubit_from(phi, theta)
        print(f"WCF qubit: {q2.qstate.qrepr}")'''

        # Create EPR pairs
        epr = epr_socket.create_keep()[0]

        # Teleport
        q.cnot(epr)
        q.H()
        m1 = q.measure()
        m2 = epr.measure()

    # Send the correction information
    m1, m2 = int(m1), int(m2)

    #print(f"{sender} measured the following teleportation corrections: m1 = {m1}, m2 = {m2}")
    #print(f"{sender} will send the corrections to {receiver}")

    socket.send_structured(StructuredMessage("Corrections", (m1, m2)))

    socket.send_silent(str((phi, theta)))

    #return {"m1": m1, "m2": m2}

def run_receiver(receiver, sender):
    global winner_a, winner_b

    # Create a socket to recv classical information
    socket = Socket(receiver, sender)
    # Setup a connection to QNodeOS (quantum node controller)
    epr_socket = EPRSocket(sender)
    with NetQASMConnection(receiver, epr_sockets=[epr_socket]) as receiver:
        epr = epr_socket.recv_keep()[0]
        receiver.flush()

        # Get the corrections
        m1, m2 = socket.recv_structured().payload
        #print(f"{receiver} got corrections: {m1}, {m2}")
        if m2 == 1:
            #print(f"{receiver} will perform X correction")
            epr.X()
        if m1 == 1:
            #print(f"{receiver} will perform Z correction")
            epr.Z()

        receiver.flush()

        # Get the qubit state
        # NOTE only possible in simulation, not part of actual application
        dm = get_qubit_state(epr)
        #print(f"{receiver} received the teleported state {dm}")

        # Reconstruct the original qubit to compare with the received one.
        # NOTE only to check simulation results, normally the Sender does not
        # need to send the phi and theta values!
        msg = socket.recv_silent()  # don't log this
        #print(f"received silent message: {msg}")
        phi, theta = eval(msg)

        original = qubit_from(phi, theta)
        original_dm = to_dm(original)
        fidelity = get_fidelity(original, dm)

        '''print(f"original_state: {original_dm.tolist()}")
        correction1="Z" if m1 == 1 else "None"
        print(f"correction1: {correction1}")
        correction2="X" if m2 == 1 else "None"
        print(f"correction2: {correction2}")
        print(f"received state: {dm.tolist()}")
        print(f"fidelity: {fidelity}")'''

        m=epr.measure()
    if m == 0:
        winner_a+=1
    else:
        winner_b+=1

    


def post_function(backend):
    print("--------")

def weak_coin_flip(p1, p2, coeff):
    print(f"WCF: {p1} vs {p2} with probability {coeff*coeff}")
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


if __name__ == "__main__":
    name1 = 'Alice'
    name2 = 'Bob'
    prob1 = 1/6
    coeff = sqrt(prob1)
    for i in range(0, 100):
        print(f"run {i+1}")
        weak_coin_flip(name1, name2, coeff)
    realprob = float(winner_a/(winner_a+winner_b))
    print(f"{name1} has {realprob} probability to win")
