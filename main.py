from manim import *

from nrpa import NRPA

TREE_CONFIGS = {
    "layout": "tree",
    "root_vertex": 0,
    "layout_scale": 1,
}
COLOR_MAP = {
    0: RED,
    1: BLUE,
    2: GREEN,
    3: YELLOW,
    4: PURPLE,
    5: ORANGE,
    6: PINK,
    7: TEAL,
    8: MAROON,
}
MAX_COLORS = len(COLOR_MAP)


class GraphScene(Scene):
    def construct(self):
        graph = self.coloring_graph()
        # self.play(graph.animate.shift(LEFT * 3))
        # tree = self.tree_graph()
        # self.play(tree.animate.shift(RIGHT * 3))
        # self.create_nodes(tree, 0, [1, 2, 3])
        # self.create_nodes(tree, 1, [4, 5])
        # self.create_nodes(tree, 4, [6])
        # self.create_nodes(tree, 6, [7])
        # self.create_nodes(tree, 0, [8])
        # self.testes()
        nrpa = NRPA(3, MAX_COLORS, graph, self)

        self.wait(3)

    def tree_graph(self):
        tree = Graph([0], [], **TREE_CONFIGS)
        self.play(Create(tree))
        # self.create_edges(tree, 0, ["Vermelho", "Azul"])

        return tree

    def create_nodes(self, tree: Graph, father, vertices):
        tree.add_vertices(*vertices,
                          positions={vertex: tree.vertices[father].get_center() + RIGHT * 0.001 for vertex in vertices})
        tree.add_edges(*[(father, vertex) for vertex in vertices])

        self.play(tree.animate.change_layout(**TREE_CONFIGS))

        def criar_updater(vertex_to_follow):
            return lambda x: x.next_to(vertex_to_follow, RIGHT * 0.5)

        for vertex in vertices:
            text = Text(f'{vertex}', font_size=20).next_to(tree.vertices[vertex], RIGHT * 0.5)
            text.add_updater(criar_updater(tree.vertices[vertex]))
            self.play(Write(text))

    def color_vertex(self, graph, vertex, fill_color: int | ManimColor):
        if isinstance(fill_color, ManimColor):
            self.play(graph[vertex].animate.set_color(fill_color))
        else:
            self.play(graph[vertex].animate.set_color(COLOR_MAP[fill_color: int]))

    def coloring_graph(self):
        graph = Graph([0, 1, 2, 3, 4, 5, 6],
                      [(0, 1), (0, 2), (1, 2), (1, 3), (2, 4), (3, 5), (3, 4), (4, 6), (4, 5), (5, 6)],
                      layout="kamada_kawai",
                      labels=True, layout_scale=3, vertex_config={"color": GREY})
        self.play(Create(graph))
        # self.color_vertex(graph, 0, RED)
        # self.color_vertex(graph, 1, BLUE)
        # self.color_vertex(graph, 2, RED)
        # self.color_vertex(graph, 3, GREEN)

        return graph
