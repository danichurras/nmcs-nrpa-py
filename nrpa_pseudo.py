import logging
import math
import random

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.animation import FuncAnimation

ALPHA = 0.3
N = 5
MAX_COLORS = 3

# Definir códigos ANSI para as cores
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"

# Definir um dicionário para mapear níveis de log às cores
LOG_COLORS = {
    "DEBUG": CYAN,
    "INFO": GREEN,
    "WARNING": YELLOW,
    "ERROR": RED,
    "CRITICAL": MAGENTA
}


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        # Pegar a cor correspondente ao nível de log
        log_color = LOG_COLORS.get(record.levelname, RESET)

        # Formatar a mensagem de log com a cor correspondente
        record.msg = f"{log_color}{record.msg}{RESET}"
        return super().format(record)


# Configurar o logger com o Formatter colorido
formatter = ColoredFormatter("%(asctime)s - %(levelname)s - %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

counter = 0
graph = nx.Graph()
estados = []  # Lista de estados ao longo das iterações


def code(move: tuple[int, int]) -> int:
    return move[0] * MAX_COLORS + move[1]


def playout(state: list[int], policy: list[float]) -> tuple[int, list[tuple[int, int]]]:
    global estados
    sequence = []
    while not is_terminal(state):
        z = 0.0
        # Calcula a soma exponencial dos pesos da política para normalização
        for move in possible_moves(state):
            z += math.exp(policy[code(move)])

        # Seleciona um movimento com base na distribuição de Gibbs
        r = random.uniform(0, 1)
        cumulative_probability = 0.0
        chosen_move = None
        for move in possible_moves(state):
            probability = math.exp(policy[code(move)]) / z
            cumulative_probability += probability
            if r <= cumulative_probability:
                chosen_move = move
                break

        # Executa o movimento escolhido e adiciona à sequência
        state = play(state, chosen_move)
        estados.append(state)
        sequence.append(chosen_move)

    return score(state), sequence


def nrpa(state: list[int], level: int, policy: list[float]) -> tuple[int, list[tuple[int, int]]]:
    global counter, estados
    counter += 1
    if level == 0:
        return playout(initial_state(), policy)

    # z = sum(math.exp(p) for p in policy)
    # probs = [math.exp(p) / z for p in policy]
    # logging.debug(
    #     f"Level: {level}\nPolicy: {[f'{p:.2f}' for p in policy]}\nProbs: {[f'{100 * p:04.1f}%' for p in probs]}")

    best_score = float('-inf')
    best_sequence = []

    for _ in range(N):
        result, new_sequence = nrpa(state, level - 1, policy.copy())
        if result > best_score:
            cores_usadas = len(set([move[1] for move in new_sequence]))
            logging.debug(
                f"Nova pontuação recorde de nível {level}: {result}\tCores usadas: {cores_usadas}")

            best_score = result
            best_sequence = new_sequence

        # Adapta a política com base na melhor sequência encontrada
        policy = adapt(state, policy, best_sequence)

    return best_score, best_sequence


def adapt(state: list[int], policy: list[float], sequence: list[tuple[int, int]]) -> list[float]:
    updated_policy = policy.copy()

    for move in sequence:
        updated_policy[code(move)] += ALPHA

        z = 0.0
        for m in possible_moves(state):
            z += math.exp(policy[code(m)])

        for m in possible_moves(state):
            updated_policy[code(m)] -= ALPHA * (math.exp(policy[code(m)]) / z)

    return updated_policy


def is_terminal(state: list[int]) -> bool:
    return all(color != -1 for color in state)


def possible_moves(state: list[int]) -> list[tuple[int, int]]:
    moves = []

    for vertex in range(len(state)):
        if state[vertex] == -1:
            for color in range(MAX_COLORS):
                if is_color_valid(state, vertex, color):
                    moves.append((vertex, color))
            break
    return moves


def is_color_valid(state: list[int], vertex: int, color: int) -> bool:
    for neighbor in graph[vertex]:
        if state[neighbor] == color:
            return False
    return True


def play(state: list[int], move: tuple[int, int]) -> list[int]:
    vertex, color = move
    new_state = state.copy()
    new_state[vertex] = color
    return new_state


def score(state: list[int]) -> int:
    conflicts = 0
    for vertex in range(len(state)):
        for neighbor in graph[vertex]:
            if state[neighbor] == state[vertex]:
                conflicts += 1
    colors_used = len(set(state))
    return -conflicts - colors_used


def initial_state() -> list[int]:
    return [-1] * len(graph.nodes)


graph.add_edges_from([(0, 1), (0, 2), (1, 2), (1, 3), (2, 4), (3, 5), (3, 4), (4, 6), (4, 5), (5, 6)])
estado_inicial = initial_state()
politica = [0] * len(graph.nodes) * MAX_COLORS

melhor_score, melhor_sequencia = nrpa(estado_inicial, 4, politica)
cores = [move[1] for move in melhor_sequencia]

logging.info(f"Cores usadas: {len(set(cores))}")
logging.info(f"Numero de vezes que nrpa foi executada: {counter}")
logging.info(f"Melhor pontuação: {melhor_score}")
logging.info(f"Melhor sequência: {melhor_sequencia}")


def animate_coloring(states):
    fig, ax = plt.subplots()
    pos = nx.kamada_kawai_layout(graph)

    def update(frame):
        ax.clear()
        colors = ['white' if color == -1 else ['red', 'green', 'blue'][color] for color in states[frame]]
        nx.draw(graph, with_labels=True, pos=pos, ax=ax, node_color=colors, node_size=800)

    ani = FuncAnimation(fig, update, frames=len(states), interval=1000 / 400, repeat=False)
    plt.show()


# Exemplo de uso
print(len(estados))

# pegar um a cada 100 estados
estados = estados[::100] + estados[-1:]
print(len(estados))
animate_coloring(estados)
