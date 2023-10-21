import math
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import Qubit

class CoinflipConsensus:
    def __init__(self, queue, app_config):
        """
        Inits the algo with the list of candidates ids.
        :param queue: the list of candidates ids.
        """
        self.queue = queue
        self.app_config = app_config

    def _atomic_flip(self, candidate1, candidate2, coeff):
        """
        Performs the basic biased coinflip between two parties.
        :param candidate1: the first party id.
        :param candidate2: the second party id.
        :param coeff: bias.
        :return: the winner id.
        """
        with NetQASMConnection(candidate1, log_config = self.app_config) as alice:
            qA = Qubit(alice)
            qB = Qubit(alice)

            # Bias
            angle = 2 * math.acos(coeff)
            step = int(angle * 256 / (2 * math.pi))
            qA.rot_Y(step)
            qA.cnot(qB)
            qB.X()

            # Send qubit qB to Bob.
            alice.sendQubit(qB, candidate2)

            # Measure the qubits.
            measured_value = qA.measure()
            alice.flush()

            with NetQASMConnection(candidate2, log_config = self.app_config) as bob:
                qB = bob.recvQubit()
                bob_value = qB.measure()
                assert measured_value + bob_value == 1

            if measured_value == 1:  # `candidate1` is a winner.
                return candidate1
            else:
                return candidate2

    def leader(self):
        """
        Executes the coinflip leader election algo.
        :return: the selected leader id.
        """
        assert len(self.queue) >= 2

        winner = self.queue[0]

        for i in range(2, len(self.queue) + 1):
            # This is calculated to bias the every next coinflip to
            # equalize candidates' chances to win.
            coeff = math.sqrt(1 / i)
            winner = self._atomic_flip(winner, self.queue[i - 1], coeff)

        return winner