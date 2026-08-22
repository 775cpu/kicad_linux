#!/usr/bin/env python3
"""Route KiCad footprints with FreeRouting and render the resulting SES as SVG.

The footprint is converted to a small Specctra design containing one placed
component. FreeRouting owns the actual obstacle avoidance; the SVG renderer
is only used to inspect the result.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_JAR = ROOT / ".cache" / "freerouting.jar"
RELEASE_API = "https://api.github.com/repos/freerouting/freerouting/releases/latest"


def ensure_runtime(jar_path: Path) -> None:
    """Install the only Python dependency and download FreeRouting on demand."""
    try:
        import shapely  # noqa: F401
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "shapely"])

    if shutil.which("java") is None:
        raise RuntimeError("未找到 Java；请安装 Java 17 或更高版本后重试")
    if not jar_path.exists():
        jar_path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(RELEASE_API, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(request) as response:
            release = __import__("json").load(response)
        jar_urls = [asset["browser_download_url"] for asset in release.get("assets", []) if asset["name"].endswith(".jar")]
        if not jar_urls:
            raise RuntimeError("FreeRouting 最新发布中没有找到 JAR 文件")
        print(f"下载 FreeRouting: {jar_urls[0]}")
        urllib.request.urlretrieve(jar_urls[0], jar_path)


def read_footprint(path: Path):
    from k2svg import find_sub, parse_sexp

    data = parse_sexp(path.read_text(encoding="utf-8"))
    if not data or data[0] != "module":
        raise ValueError(f"无效的 KiCad 封装: {path}")

    pads = []
    obstacles = []
    for item in data[2:]:
        if not isinstance(item, list) or not item:
            continue
        if item[0] == "pad" and item[2] == "thru_hole":
            at = find_sub(item, "at")
            size = find_sub(item, "size")
            if at and size:
                pads.append({
                    "number": f"P{len(pads)}",
                    "x": float(at[1]), "y": float(at[2]),
                    "w": float(size[1]), "h": float(size[2]),
                })
        elif item[0] == "fp_poly":
            points = find_sub(item, "pts")
            if points:
                obstacles.append([(float(p[1]), float(p[2])) for p in points[1:] if p[0] == "xy"])
        elif item[0] == "fp_line":
            start, end = find_sub(item, "start"), find_sub(item, "end")
            if start and end:
                obstacles.append([(float(start[1]), float(start[2])), (float(end[1]), float(end[2]))])

    if not pads:
        raise ValueError("封装中没有可布线焊盘")
    return data[1], pads, obstacles


def make_dsn(name: str, pads: list[dict], obstacles: list[list[tuple[float, float]]],
             connections: list[tuple[int, int]], output: Path) -> None:
    min_x = min(p["x"] for p in pads)
    max_x = max(p["x"] for p in pads)
    min_y = min(p["y"] for p in pads)
    max_y = max(p["y"] for p in pads)
    min_x, max_x = min_x - 5.0, max_x + 5.0
    min_y, max_y = min_y - 5.0, max_y + 5.0

    scale = 1000
    
    unique_padstacks = {}
    for pad in pads:
        ps_name = f'PTH_{pad["w"]*scale:.0f}_{pad["h"]*scale:.0f}'
        pad["padstack"] = ps_name
        if ps_name not in unique_padstacks:
            unique_padstacks[ps_name] = (pad["w"], pad["h"])

    lines = [
        f'(pcb "{name}"',
        '  (parser (string_quote ") (space_in_quoted_tokens on))',
        '  (resolution um 1)',
        '  (unit um)',
        '  (structure',
        '    (layer F.Cu (type signal) (property (index 0)))',
        '    (layer B.Cu (type signal) (property (index 1)))',
        f'    (boundary (path pcb 0 {min_x * scale:.0f} {min_y * scale:.0f} {max_x * scale:.0f} {min_y * scale:.0f} {max_x * scale:.0f} {max_y * scale:.0f} {min_x * scale:.0f} {max_y * scale:.0f} {min_x * scale:.0f} {min_y * scale:.0f}))',
        '    (via via0)',
        '    (rule (width 400) (clearance 350))',
        '  )',
        '  (placement',
        f'    (component {name}',
        '      (place U1 0 0 front 0)',
        '    )',
        '  )',
        '  (library',
        f'    (image {name}',
        '      (outline (path signal 50 -30000 -20000 30000 -20000 30000 20000 -30000 20000 -30000 -20000))',
    ]
    
    for pad in pads:
        lines.append(f'      (pin {pad["padstack"]} {pad["number"]} {pad["x"] * scale:.0f} {pad["y"] * scale:.0f})')
        
    lines += [
        '    )'
    ]
    
    for ps_name, (w, h) in unique_padstacks.items():
        hw = (w * scale) / 2.0
        hh = (h * scale) / 2.0
        lines += [
            f'    (padstack {ps_name}',
            f'      (shape (rect F.Cu {-hw:.0f} {-hh:.0f} {hw:.0f} {hh:.0f}))',
            f'      (shape (rect B.Cu {-hw:.0f} {-hh:.0f} {hw:.0f} {hh:.0f}))',
            '      (attach off)',
            '    )'
        ]

    lines += [
        '    (padstack via0',
        '      (shape (circle F.Cu 500))',
        '      (shape (circle B.Cu 500))',
        '      (attach off)',
        '    )',
        '  )',
        '  (network',
    ]
    
    net_names = []
    for index, (first, second) in enumerate(connections, 1):
        net_name = f"NET_{index}"
        net_names.append(net_name)
        lines.append(f'    (net {net_name} (pins U1-{pads[first]["number"]} U1-{pads[second]["number"]}))')
        
    lines += [
        f'    (class default {" ".join(net_names)}',
        '      (circuit (use_layer F.Cu) (use_via via0))', # 保留了关键的单层强制限制
        '      (rule (width 400) (clearance 350))',
        '    )',
        '  )',
        ')',
        ''
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_ses(ses_path: Path) -> dict[str, list[list[tuple[float, float]]]]:
    """提取 FreeRouting 的走线。将属于同一个网络名称的多个物理片段进行聚合存放。"""
    content = ses_path.read_text(encoding="utf-8")
    routes = {}
    
    # 按照网络区块进行正则切分
    net_blocks = re.split(r'\(\s*net\s+', content)[1:]
    for block in net_blocks:
        match = re.match(r'"?([^"\s()]+)"?', block)
        if not match:
            continue
        net_name = match.group(1)
        if net_name not in routes:
            routes[net_name] = []
            
        # 查找当前网络下所有的走线片段
        path_blocks = re.findall(r'\(\s*path\s+[^)]+\)', block)
        for pb in path_blocks:
            # 抹除括号与换行以提取其中的纯坐标
            tokens = pb.replace("(", " ").replace(")", " ").split()
            if len(tokens) >= 3:
                coords = tokens[3:]
                points = []
                for i in range(0, len(coords) - 1, 2):
                    try:
                        x = float(coords[i]) / 1000.0
                        y = float(coords[i+1]) / 1000.0
                        points.append((x, y))
                    except ValueError:
                        pass
                if len(points) >= 2:
                    routes[net_name].append(points)
                    
    if not routes:
        raise RuntimeError(f"SES 中没有解析到走线: {ses_path}")
    return routes


def render_svg(footprint: Path, svg: Path, routes: dict[str, list[list[tuple[float, float]]]]) -> None:
    from k2svg import kicad_to_svg

    base_svg = svg.with_name(f".{svg.stem}.base.svg")
    kicad_to_svg(str(footprint), layers=["F.Cu", "B.Cu", "Edge.Cuts", "F.SilkS"], out_dir=str(svg.parent), file_name=base_svg.name)
    content = base_svg.read_text(encoding="utf-8")
    marks = []
    colors = ["#00FF00", "#00BFFF", "#FFB000", "#FF4FA3", "#A8FF00", "#FFFFFF"]
    
    # 遍历聚合字典。遍历的键数量即真实的网络总数量
    for index, (net, segments) in enumerate(routes.items()):
        color = colors[index % len(colors)]
        for points in segments:
            points_text = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
            marks.append(f'  <!-- FreeRouting {net} -->\n  <polyline points="{points_text}" fill="none" stroke="{color}" stroke-width="0.40" stroke-linecap="round" stroke-linejoin="round"/>')
            
    content = content.replace("\n</svg>", "\n" + "\n".join(marks) + "\n</svg>")
    svg.write_text(content, encoding="utf-8")
    base_svg.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "IBT_2x4-30x20.kicad_mod")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "generated" / "svg")
    parser.add_argument("--jar", type=Path, default=DEFAULT_JAR)
    args = parser.parse_args()

    ensure_runtime(args.jar)
    name, pads, obstacles = read_footprint(args.input)
    # 建立8组网络连通关系
    connections = [(i, 8 + i) for i in range(4)] + [(4 + i, 12 + i) for i in range(4)]
    dsn = args.output_dir / f"{name}.dsn"
    ses = args.output_dir / f"{name}.ses"
    svg = args.output_dir / f"{name}-freerouting.svg"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    make_dsn(name, pads, obstacles, connections, dsn)

    subprocess.run(["java", "-jar", str(args.jar), "-de", str(dsn), "-do", str(ses)], check=True)
    routes = parse_ses(ses)
    render_svg(args.input, svg, routes)
    
    # 通过字典的长度，这回就可以准确检验生成出来的独立网络条数是否严格等于 8
    if len(routes) != len(connections):
        raise RuntimeError(f"期望 {len(connections)} 条网络，实际得到 {len(routes)} 条")
        
    total_segments = sum(len(segs) for segs in routes.values())
    print(f"[OK] DSN: {dsn}")
    print(f"[OK] SES: {ses}")
    print(f"[OK] SVG: {svg} (网络数: {len(routes)}, 物理片段总数: {total_segments})")


if __name__ == "__main__":
    main()