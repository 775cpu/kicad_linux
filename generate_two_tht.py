#!/usr/bin/env python3
"""Generate a minimal two-pad through-hole KiCad footprint."""

import argparse
from pathlib import Path

from KicadModTree import Footprint, KicadFileHandler, Pad, RectLine


def build_footprint(name: str) -> Footprint:
    footprint = Footprint(name)
    footprint.setDescription("Minimal two-pad through-hole footprint")
    footprint.setTags("THT two pad test")

    for number, x in (("1", -2.54), ("2", 2.54)):
        footprint.append(
            Pad(
                number=number,
                type=Pad.TYPE_THT,
                shape=Pad.SHAPE_CIRCLE,
                at=[x, 0],
                size=[2.0, 2.0],
                drill=1.0,
                layers=Pad.LAYERS_THT,
            )
        )

    footprint.append(
        RectLine(
            start=[-4.0, -1.5],
            end=[4.0, 1.5],
            layer="F.SilkS",
            width=0.2,
        )
    )
    return footprint


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", default="Test_THT_2Pad")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"{args.name}.kicad_mod"
    KicadFileHandler(build_footprint(args.name)).writeFile(str(output_path))
    print(output_path)


if __name__ == "__main__":
    main()