"""Compute fixed points of complex Boolean networks.

Copyright (C) 2023 Sylvain.Soliman@inria.fr and giang.trinh91@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from sys import setrecursionlimit
from typing import IO

import networkx as nx  # TODO maybe replace with lists/dicts

from pyeda.boolalg.expr import expr


def read_bnet(fileobj: IO, method: str) -> nx.DiGraph:
    """Parse a BoolNet .bnet file."""
    net = nx.DiGraph()
    nodes = []

    # big bnets…
    setrecursionlimit(10**9)

    for line in fileobj.readlines():
        # TODO: a more robust parser
        if line.startswith("#") or line.startswith("targets, factors"):
            continue
        line = line.split("#")[0]
        try:
            x, fx = (
                line.replace(" ", "")
                .replace("-", "_")
                .replace("Ci", "Ci_")
                .replace("cot", "cot_")
                .replace("!", "~")
                .replace("GF", "GF_")
                .replace("E", "E_")
                .replace("S", "S_")
                .replace("N", "N_")
                .replace("Ge", "Ge_")
                .replace("Le", "Le_")
                .split(",", maxsplit=1)
            )
        except ValueError:  # not enough values to unpack
            continue

        vx = expr(x)
        fx = expr(fx)

        fx = fx.to_nnf()

        nfx = (~fx).to_nnf()

        net.add_node(x, kind="place")
        net.add_node("-" + x, kind="place")

        nodes.append(x)
        net.nodes[x]["function"] = fx
        net.nodes[x]["var"] = vx
        net.nodes["-" + x]["function"] = nfx
        net.nodes["-" + x]["var"] = ~vx

    return net
