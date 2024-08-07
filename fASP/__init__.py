# noqa: D104
# pylint: disable=missing-docstring
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
# Don't forget to git tag v<version> && git push --tags
version = "0.3.0"  # pylint: disable=invalid-name


def pnml_to_asp(name: str) -> str:
    """Convert a PNML id to an ASP variable."""
    # TODO handle non-accetable chars
    name = name.replace("~", "-")
    if name.startswith("-"):
        return "n" + name[1:]
    return "p" + name


from .fASP import compute_fix_points  # noqa
