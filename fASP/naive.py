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

from typing import IO, List

import networkx as nx  # TODO maybe replace with lists/dicts

from pyeda.boolalg.expr import AndOp, Constant, Literal, OrOp, Variable, expr

from . import pnml_to_asp


def write_naive_asp(
    petri_net: nx.DiGraph, asp_file: IO, method: str, source_places: List[str]
):
    """Write the ASP program for naive encoding of fixed points."""
    counter = 1

    for node, data in petri_net.nodes(data=True):
        name = pnml_to_asp(node)

        if method == "conj" or method == "disj" or node not in source_places:
            print(f"#show {name}/0.", file=asp_file)
            if not node.startswith("-"):
                print(
                    f":- {name}, {pnml_to_asp('-' + node)}.", file=asp_file
                )  # fixed point constraint
                print(
                    f"{name}, {pnml_to_asp('-' + node)}.", file=asp_file
                )  # fixed point constraint

            if method == "conj":
                counter = add_tree_conj(
                    data["function"], data["var"], asp_file, counter
                )
            elif method == "disj":
                counter = add_tree_disj(
                    data["function"], data["var"], asp_file, counter
                )
            else:
                counter = add_tree_conj(
                    data["function"], data["var"], asp_file, counter
                )
        elif method == "source" and node in source_places:
            if not node.startswith("-"):
                n_name = pnml_to_asp("-" + node)

                print("{", name, "}.", sep="", file=asp_file)
                print("{", n_name, "}.", sep="", file=asp_file)

                print(f"{name}, {n_name}.", file=asp_file)

                print(f"#show {name}/0.", file=asp_file)
                print(f"#show {n_name}/0.", file=asp_file)

        else:
            print("Only support conjunctive, disjunctive, and source ASP encoding!")


def add_tree_conj(source: expr, target: expr, asp_file, counter=1):
    """Add the AST of target <- things to the ASP program."""
    if isinstance(target, Variable) and target.name.startswith("aux"):
        starget = target.name
    else:
        starget = pnml_to_asp(str(target))

    if isinstance(source, Literal):
        print(f"{starget} :- {pnml_to_asp(str(source))}.", file=asp_file)
    elif isinstance(source, Constant):
        if source.is_zero():
            print(f":- {starget}.", file=asp_file)
        elif source.is_one():
            print(f"{starget}.", file=asp_file)
        else:
            print(f"Houston we have a problem with {source}…")
    elif isinstance(source, AndOp):
        source_str = ""
        for s in source.xs:
            if isinstance(s, Literal):
                svs = pnml_to_asp(str(s))
            else:
                vs = expr(f"aux_{counter}")
                counter = add_tree_conj(s, vs, asp_file, counter + 1)
                svs = str(vs)
            if source_str:
                source_str += "; " + svs
            else:
                source_str = svs
        print(f"{starget} :- {source_str}.", file=asp_file)
    elif isinstance(source, OrOp):
        for s in source.xs:
            if isinstance(s, Literal):
                print(f"{starget} :- {pnml_to_asp(str(s))}.", file=asp_file)
            else:
                counter = add_tree_conj(s, target, asp_file, counter)
    else:
        print(f"Houston we have a problem with {source}…")
    return counter


def add_tree_disj(source: expr, target: expr, asp_file, counter=1):
    """Add the AST of things -> target to the ASP program."""
    if isinstance(target, Variable) and target.name.startswith("aux"):
        starget = target.name
    else:
        starget = pnml_to_asp(str(target))

    if isinstance(source, Literal):
        print(f"{pnml_to_asp(str(source))} :- {starget}.", file=asp_file)
    elif isinstance(source, Constant):
        if source.is_zero():
            print(f":- {starget}.", file=asp_file)
        elif source.is_one():
            print(f"{starget}.", file=asp_file)
        else:
            print(f"Houston we have a problem with {source}…")
    elif isinstance(source, OrOp):
        source_str = ""
        for s in source.xs:
            if isinstance(s, Literal):
                svs = pnml_to_asp(str(s))
            else:
                vs = expr(f"aux_{counter}")
                counter = add_tree_disj(s, vs, asp_file, counter + 1)
                svs = str(vs)
            if source_str:
                source_str += "; " + svs
            else:
                source_str = svs
        print(f"{source_str} :- {starget}.", file=asp_file)
    elif isinstance(source, AndOp):
        for s in source.xs:
            if isinstance(s, Literal):
                print(f"{pnml_to_asp(str(s))} :- {starget}.", file=asp_file)
            else:
                counter = add_tree_disj(s, target, asp_file, counter)
    else:
        print(f"Houston we have a problem with {source}…")
    return counter
