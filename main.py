from netqasm.logging.glob import get_netqasm_logger, set_log_level
from netqasm.runtime.application import default_app_instance
from netqasm.sdk import EPRSocket, Qubit
from netqasm.sdk.external import NetQASMConnection, simulate_application
from game import Game
from utils import greatest_power_of_two, is_power_of_two

logger = get_netqasm_logger()

games = []

'''ISSSUES:
- match are sequential, there is no parallelism
- unbalanced flip are yet to be implemented'''

def qleTournament(players):
    print(players)
    while len(players) > 1:
        tmp_list = []
        for i in range(0, len(players), 2):
            tmp = weak_coin_flip(players[i], players[i+1])
            tmp_list.append(tmp)
        players = tmp_list
    return players[0]

def quantumLeaderElection(players):
    n_players = len(players)
    if n_players == 1:
        return players[0]
    t = greatest_power_of_two(n_players)
    if t==n_players:
        return qleTournament(players)
    else:
        w1 = qleTournament(players[:t])
        w2 = quantumLeaderElection(players[t:])
        return qleTournament([w1,w2])

def run_sender(name, name_r):
    # Setup a connection to QNodeOS (quantum node controller)
    epr_socket = EPRSocket(name_r)
    with NetQASMConnection(name, epr_sockets=[epr_socket]):
        # Create an entangled pair using the EPR socket to bob
        q_ent = epr_socket.create_keep()[0]
        # Measure the qubit
        m = q_ent.measure()
    # Print the outcome
    print(f"SENDER: Outcome is: {m}\n")

def run_receiver(name, name_s):
    global games
    winner = -1
    # Setup a connection to QNodeOS (quantum node controller)
    epr_socket = EPRSocket(name_s)
    with NetQASMConnection(name, epr_sockets=[epr_socket]):
        # Create an entangled pair using the EPR socket to bob
        q_ent = epr_socket.recv_keep()[0]
        # Measure the qubit
        m = q_ent.measure()
    # Print the outcome
    if m == 0:
        winner = name_s
    else:
        winner = name
    game = Game([name_s, name], winner)
    games.append(game)


def post_function(backend):
    print("--------")

def weak_coin_flip(p1, p2):
    print(f"WCF: {p1} vs {p2}")
    def wcf_sender():
        run_sender(p1, p2)
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
    print("WCF: ")
    return 

if __name__ == "__main__":
    #set_log_level("DEBUG")
    nParties = input("Number of parties:")
    players = []
    for num in range(1, int(nParties)+1):
        label = ""
        while num > 0:
            num, remainder = divmod(num - 1, 26)
            label = chr(65 + remainder) + label
        players.append(label)
    print(players)

    
    w = quantumLeaderElection(players)

    print(f"The winner is {w}!")
