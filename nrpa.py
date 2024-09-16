import math
import random
from typing import TYPE_CHECKING

from manim import *

if TYPE_CHECKING:
    from main import GraphScene

ALFA = 0.3
REVERSE_COLOR_MAP = {
    RED: 0,
    BLUE: 1,
    GREEN: 2,
    YELLOW: 3,
    PURPLE: 4,
    ORANGE: 5,
    PINK: 6,
    TEAL: 7,
    MAROON: 8,
}


class NRPA:
    def __init__(self, level: int, num_colors: int, graph: Graph, scene: 'GraphScene'):
        self.level = level
        self.num_colors = num_colors
        self.graph = graph
        self.policy = np.zeros((len(graph.vertices), num_colors))
        self.scene = scene
        self.order = np.random.permutation(len(graph.vertices))
        self.current_vertex = self.order[0]

    @staticmethod
    def adapt_policy(policy, trajectory):
        updated_policy = policy.copy()

        for move in sequence:
            updated_policy[move] += ALFA

            z = 0.0
            for m in possible_moves(state):
                z += math.exp(policy[m])

            for m in possible_moves(state):
                updated_policy[m] -= alpha * (math.exp(policy[m]) / z)

        return updated_policy

    def is_terminal(self, state: Graph):
        return self.current_vertex == len(state.vertices)

    def possible_moves(self, state: Graph) -> list:
        # checar cores dos vizinhos
        all_moves = [color for color in range(self.num_colors)]
        neighbors = state.edges[self.current_vertex]
        for neighbor in neighbors:
            all_moves -= REVERSE_COLOR_MAP[neighbor.fill_color]

        return all_moves

    def playout(self, state, policy):
        sequence = []
        while not self.is_terminal(state):
            z = 0.0
            # Calcula a soma exponencial dos pesos da política para normalização
            for move in self.possible_moves(state):
                z += math.exp(policy[move])

            # Seleciona um movimento com base na distribuição de Gibbs
            r = random.uniform(0, 1)
            cumulative_probability = 0.0
            chosen_move = None
            for move in self.possible_moves(state):
                probability = math.exp(policy[move]) / z
                cumulative_probability += probability
                if r <= cumulative_probability:
                    chosen_move = move
                    break

            # Executa o movimento escolhido e adiciona à sequência
            state = self.play(state, chosen_move)
            sequence.append(chosen_move)

        return self.score(state), sequence

    def color_graph(self, graph, policy):
        colors = [-1] * len(graph.vertices)
        for vertex in range(len(graph.vertices)):
            probabilities = np.exp(policy[vertex])
            probabilities /= np.sum(probabilities)
            chosen_color = np.random.choice(range(self.num_colors), p=probabilities)

            if all(colors[neighbor] != chosen_color for neighbor in graph.edges[vertex]):
                colors[vertex] = chosen_color
            else:
                return None

        return colors

    def nrpa(self, level, policy):
        if level == 0:
            best_trajectory = []
            best_colors = None
            for _ in range(10):
                trajectory = []
                colors = self.color_graph(self.graph, policy)
                if colors:
                    for vertex, move in enumerate(colors):
                        trajectory.append((vertex, move))
                    if not best_colors or len(set(best_colors)) > len(set(colors)):
                        best_trajectory = trajectory
                        best_colors = colors

            return best_colors, best_trajectory

        else:
            best_trajectory = []
            best_colors = None
            for _ in range(10):
                result, trajectory = self.nrpa(level - 1, policy)
                if result and (not best_colors or len(set(best_colors)) > len(set(result))):
                    best_trajectory = trajectory
                    best_colors = result
                    policy = self.adapt_policy(policy, trajectory)

            return best_colors, best_trajectory

    def play(self, state, chosen_move) -> Graph:
        return state

    def score(self, state) -> float:
        return 0.0
