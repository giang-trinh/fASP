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

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from sys import setrecursionlimit
from typing import Generator, IO, List, Set

import networkx as nx

from pyeda.boolalg.bdd import bddvar, expr2bdd
from pyeda.boolalg.expr import expr

from . import version
from .bnet import read_bnet
from .naive import write_naive_asp

setrecursionlimit(10**9)


def solve_asp(asp_filename: str, max_output: int, time_limit: int, method: str) -> str:
    """Run an ASP solver on program asp_file and get the solutions."""
    if method == "conj":
        result = subprocess.run(
            [
                "clingo",
                str(max_output),
                "--outf=2",  # json output
                f"--time-limit={time_limit}",
                asp_filename,
            ],
            capture_output=True,
            text=True,
        )
    elif method == "disj":
        result = subprocess.run(
            [
                "clingo",
                str(max_output),
                "--heuristic=Domain",  # maximal w.r.t. inclusion
                "--enum-mod=domRec",
                "--dom-mod=3,16",
                "--no-gamma",  # fix Clasp's bug on disjunctive rules
                "--outf=2",  # json output
                f"--time-limit={time_limit}",
                asp_filename,
            ],
            capture_output=True,
            text=True,
        )
    else:
        result = subprocess.run(
            [
                "clingo",
                str(max_output),
                "--heuristic=Domain",  # maximal w.r.t. inclusion
                "--enum-mod=domRec",
                "--dom-mod=3,16",
                "--outf=2",  # json output
                f"--time-limit={time_limit}",
                asp_filename,
            ],
            capture_output=True,
            text=True,
        )

    # https://www.mat.unical.it/aspcomp2013/files/aspoutput.txt
    # 30: SAT, all enumerated, optima found, 10 stopped by max
    if result.returncode != 30 and result.returncode != 10 and result.returncode != 20:
        print(f"Return code from clingo: {result.returncode}")
        result.check_returncode()  # will raise CalledProcessError

    if result.returncode == 20:
        return "UNSATISFIABLE"

    return result.stdout


def solution_to_bool(places: List[str], sol: Set[str]) -> List[str]:
    """Convert a list of present places in sol, to a tri-valued vector."""
    return [place_in_sol(sol, p) for p in places]


def solution_to_bdd(places: List[str], source_nodes: List[str], sol: Set[str]):
    """Do something."""
    normal_node = ""
    source_expr = []

    for node in places:
        if node not in source_nodes:
            if "p" + node in sol:
                normal_node += "1"
            if "n" + node in sol:
                normal_node += "0"

    for node in source_nodes:
        p_node = "p" + node
        n_node = "n" + node

        if n_node in sol and p_node not in sol:
            source_expr.append("~" + node)
        if n_node not in sol and p_node in sol:
            source_expr.append(node)

    if len(source_expr) == 0:
        return (normal_node, expr2bdd(expr("1")))
    else:
        return (normal_node, expr2bdd(expr("&".join(source_expr))))


def place_in_sol(sol: Set[str], place: str) -> str:
    """Return 0/1 if place is absent, present in sol."""
    if "p" + place in sol:
        return "'" + place + "'" + ": 1"
    if "n" + place in sol:
        return "'" + place + "'" + ": 0"


def get_solutions(
    asp_output: str, places: List[str]
) -> Generator[List[str], None, None]:
    """Display the ASP output back as fixed points."""
    solutions = json.loads(asp_output)
    yield from (
        solution_to_bool(places, set(sol["Value"]))
        for sol in solutions["Call"][0]["Witnesses"]
    )


def get_solutions_source(
    asp_output: str, places: List[str], source_nodes: List[str]
) -> int:
    """Display the ASP output back as a BDD representing all fixed points."""
    bdd_result = {}

    for node in source_nodes:
        _ = bddvar(node)

    solutions = json.loads(asp_output)
    sols = solutions["Call"][0]["Witnesses"]
    print(f"# answer sets = {len(sols)}")

    for sol in sols:
        (normal_node, source_bdd) = solution_to_bdd(
            places, source_nodes, set(sol["Value"])
        )
        if normal_node in bdd_result:
            bdd_result[normal_node] = bdd_result[normal_node] | source_bdd
        else:
            bdd_result[normal_node] = source_bdd

    n_vars = len(source_nodes)
    num_fixed_points = 0

    for normal_node in bdd_result:
        for sat_x in bdd_result[normal_node].satisfy_all():
            num_fixed_points += int(pow(2, n_vars - len(sat_x)))

    return num_fixed_points


def get_asp_output(
    petri_net: nx.DiGraph,
    max_output: int,
    time_limit: int,
    method: str,
    source_nodes: list[str],
) -> str:
    """Generate and solve ASP file."""
    (fd, tmpname) = tempfile.mkstemp(suffix=".lp", text=True)
    with open(tmpname, "wt") as asp_file:
        write_naive_asp(petri_net, asp_file, method, source_nodes)

    solutions = solve_asp(tmpname, max_output, time_limit, method)

    os.close(fd)
    os.unlink(tmpname)

    return solutions


def compute_fix_points(
    infile: IO,
    display: bool = False,
    max_output: int = 0,
    time_limit: int = 0,
    method: str = "conj",
):
    """Do the fixed point computation on input file infile."""
    start = time.perf_counter()

    toclose = False
    if isinstance(infile, str):
        infile = open(infile, "r", encoding="utf-8")
        toclose = True

    if infile.name.endswith(".bnet"):
        petri_net = read_bnet(infile, method)
        # global bn_name
        # bn_name = infile.name.split("/")[-1].replace(".bnet", "")
    else:
        infile.close()
        raise ValueError("Failed parsing input")

    if toclose:
        infile.close()

    places = []
    source_nodes = []
    for node, data in petri_net.nodes(data=True):
        if not node.startswith("-"):
            places.append(node)
            if str(data["function"]) == node:
                source_nodes.append(node)

    solutions_output = get_asp_output(
        petri_net, max_output, time_limit, method, source_nodes
    )
    print(f"# ASP time = {time.perf_counter() - start:.2f}s")
    n_fixed_points = 0

    if display:
        if solutions_output == "UNSATISFIABLE":
            print("There are no fixed points.")
        else:
            if method == "conj" or method == "disj":
                solutions = get_solutions(solutions_output, places)
                print("\n".join(", ".join(sol) for sol in solutions))
            else:
                # deal with source nodes, thus only return the number of fixed points
                n_fixed_points = get_solutions_source(
                    solutions_output, places, source_nodes
                )
        return
    else:
        if solutions_output == "UNSATISFIABLE":
            return 0
        else:
            if method == "conj" or method == "disj":
                solutions = json.loads(solutions_output)
                return len(list(solutions["Call"][0]["Witnesses"]))
            else:
                # deal with source nodes, thus only return the number of fixed points
                n_fixed_points = get_solutions_source(
                    solutions_output, places, source_nodes
                )
                return n_fixed_points


def main():
    """Enumerate the fixed points."""
    parser = argparse.ArgumentParser(
        description=" ".join(__doc__.splitlines()[:3]) + " GPLv3"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s v{version}".format(version=version),
    )
    parser.add_argument(
        "-m",
        "--max",
        type=int,
        default=0,
        help="Maximum number of solutions (0 for all).",
    )
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=0,
        help="Maximum number of seconds for search (0 for no-limit).",
    )
    parser.add_argument(
        "-e",
        "--encoding",
        choices=["conj", "disj", "source"],
        default="conj",
        type=str,
        help="ASP encoding to compute fixed points.",
    )
    parser.add_argument(
        "infile",
        type=argparse.FileType("r", encoding="utf-8"),
        nargs="?",
        default=sys.stdin,
        help="BoolNet (.bnet) file",
    )
    args = parser.parse_args()
    compute_fix_points(
        args.infile,
        display=True,
        max_output=args.max,
        time_limit=args.time,
        method=args.encoding,
    )


if __name__ == "__main__":
    main()
