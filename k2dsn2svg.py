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

    # 1. 收集所有的物理焊盘并按引脚名称聚类
    pad_groups = {}
    obstacles = []
    for item in data[2:]:
        if not isinstance(item, list) or not item:
            continue
        if item[0] == "pad":
            pad_name = item[1]
            if pad_name not in pad_groups:
                pad_groups[pad_name] = []
            pad_groups[pad_name].append(item)
        elif item[0] == "fp_poly":
            points = find_sub(item, "pts")
            if points:
                obstacles.append([(float(p[1]), float(p[2])) for p in points[1:] if p[0] == "xy"])
        elif item[0] == "fp_line":
            start, end = find_sub(item, "start"), find_sub(item, "end")
            if start and end:
                obstacles.append([(float(start[1]), float(start[2])), (float(end[1]), float(end[2]))])

    pads = []
    # 2. 合并同名焊盘（如 thru_hole + smd 偏置），提取能覆盖所有碎片的绝对外框
    for pad_name, shapes in pad_groups.items():
        # 寻找主锚点（优先采用 thru_hole 类型的坐标作为基准连线中心）
        anchor_at = None
        for shape in shapes:
            if shape[2] == "thru_hole":
                anchor_at = find_sub(shape, "at")
                break
        if not anchor_at:
            anchor_at = find_sub(shapes[0], "at")

        anchor_x = float(anchor_at[1])
        anchor_y = float(anchor_at[2])

        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        for shape in shapes:
            at = find_sub(shape, "at") or anchor_at
            size = find_sub(shape, "size")
            if not size:
                continue
            
            px, py = float(at[1]), float(at[2])
            pw, ph = float(size[1]), float(size[2])
            
            # 兼容带有旋转角度的 pad (处理正交旋转)
            if len(at) > 3:
                rot = float(at[3])
                if rot in (90, 270, -90, -270):
                    pw, ph = ph, pw

            min_x = min(min_x, px - pw / 2.0)
            max_x = max(max_x, px + pw / 2.0)
            min_y = min(min_y, py - ph / 2.0)
            max_y = max(max_y, py + ph / 2.0)

        # 生成相对于主锚点的边框（供 FreeRouting 作为 padstack shape）
        rel_bounds = (min_x - anchor_x, min_y - anchor_y, max_x - anchor_x, max_y - anchor_y)
        
        pads.append({
            "number": f"P{len(pads)}",
            "x": anchor_x,
            "y": anchor_y,
            "rel_bounds": rel_bounds
        })

    if not pads:
        raise ValueError("封装中没有可布线焊盘")
    return data[1], pads, obstacles


def make_dsn(name: str, pads: list[dict], obstacles: list[list[tuple[float, float]]],
             connections: list[tuple[int, int]], output: Path) -> None:
    # 此时计算全局包围盒也需把焊盘偏置算入
    min_x = min(p["x"] + p["rel_bounds"][0] for p in pads)
    max_x = max(p["x"] + p["rel_bounds"][2] for p in pads)
    min_y = min(p["y"] + p["rel_bounds"][1] for p in pads)
    max_y = max(p["y"] + p["rel_bounds"][3] for p in pads)
    min_x, max_x = min_x - 5.0, max_x + 5.0
    min_y, max_y = min_y - 5.0, max_y + 5.0

    scale = 1000
    
    unique_padstacks = {}
    for pad in pads:
        rb = pad["rel_bounds"]
        rb_um = (rb[0]*scale, rb[1]*scale, rb[2]*scale, rb[3]*scale)
        # 带有边界信息的哈希命名（将负号转为 M，满足命名规则）
        ps_name = f'PAD_{rb_um[0]:.0f}_{rb_um[1]:.0f}_{rb_um[2]:.0f}_{rb_um[3]:.0f}'.replace("-", "M")
        pad["padstack"] = ps_name
        if ps_name not in unique_padstacks:
            unique_padstacks[ps_name] = rb_um

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
    
    # 写入完美包裹整个复合焊盘的形变边框
    for ps_name, rb in unique_padstacks.items():
        lines += [
            f'    (padstack {ps_name}',
            f'      (shape (rect F.Cu {rb[0]:.0f} {rb[1]:.0f} {rb[2]:.0f} {rb[3]:.0f}))',
            f'      (shape (rect B.Cu {rb[0]:.0f} {rb[1]:.0f} {rb[2]:.0f} {rb[3]:.0f}))',
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
        '      (circuit (use_layer F.Cu) (use_via via0))', 
        '      (rule (width 400) (clearance 350))',
        '    )',
        '  )',
        ')',
        ''
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_ses(ses_path: Path) -> dict[str, list[list[tuple[float, float]]]]:
    content = ses_path.read_text(encoding="utf-8")
    routes = {}
    
    net_blocks = re.split(r'\(\s*net\s+', content)[1:]
    for block in net_blocks:
        match = re.match(r'"?([^"\s()]+)"?', block)
        if not match:
            continue
        net_name = match.group(1)
        if net_name not in routes:
            routes[net_name] = []
            
        path_blocks = re.findall(r'\(\s*path\s+[^)]+\)', block)
        for pb in path_blocks:
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
    
    for index, (net, segments) in enumerate(routes.items()):
        color = colors[index % len(colors)]
        for points in segments:
            points_text = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
            marks.append(f'  <!-- FreeRouting {net} -->\n  <polyline points="{points_text}" fill="none" stroke="{color}" stroke-width="0.40" stroke-linecap="round" stroke-linejoin="round"/>')
            
    content = content.replace("\n</svg>", "\n" + "\n".join(marks) + "\n</svg>")
    svg.write_text(content, encoding="utf-8")
    base_svg.unlink()


def print_multi_dot_lines(routes: dict[str, list[list[tuple[float, float]]]]) -> None:
    """Print SES routes as eight reusable KiCad multi_dot_line calls."""
    print("\n# FreeRouting routes as multi_dot_line calls")
    for net_name in sorted(routes, key=lambda name: int(name.removeprefix("NET_"))):
        remaining = [list(segment) for segment in routes[net_name]]
        points = remaining.pop(0)
        while remaining:
            for index, segment in enumerate(remaining):
                if segment[0] == points[-1]:
                    points.extend(segment[1:])
                    remaining.pop(index)
                    break
                if segment[-1] == points[-1]:
                    points.extend(reversed(segment[:-1]))
                    remaining.pop(index)
                    break
                if segment[-1] == points[0]:
                    points = segment[:-1] + points
                    remaining.pop(index)
                    break
                if segment[0] == points[0]:
                    points = list(reversed(segment[1:])) + points
                    remaining.pop(index)
                    break
            else:
                raise RuntimeError(f"{net_name} 的 SES 片段无法连续拼接")
        dots = ", ".join(f"({x:.3f}, {y:.3f})" for x, y in points)
        print(f"multi_dot_line(kicad_mod, [{dots}], width=0.254, layers='F.Cu',)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "IBT_2x4-30x20.kicad_mod")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "generated" / "svg")
    parser.add_argument("--jar", type=Path, default=DEFAULT_JAR)
    args = parser.parse_args()

    ensure_runtime(args.jar)
    name, pads, obstacles = read_footprint(args.input)
    # 建立 8 组独立网络
    connections = [(i, 8 + i) for i in range(4)] + [(4 + i, 12 + i) for i in range(4)]
    dsn = args.output_dir / f"{name}.dsn"
    ses = args.output_dir / f"{name}.ses"
    svg = args.output_dir / f"{name}-freerouting.svg"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    make_dsn(name, pads, obstacles, connections, dsn)

    subprocess.run(["java", "-jar", str(args.jar), "-de", str(dsn), "-do", str(ses)], check=True)
    routes = parse_ses(ses)
    render_svg(args.input, svg, routes)
    
    if len(routes) != len(connections):
        raise RuntimeError(f"期望 {len(connections)} 条网络，实际得到 {len(routes)} 条")

    print_multi_dot_lines(routes)
        
    total_segments = sum(len(segs) for segs in routes.values())
    print(f"[OK] DSN: {dsn}")
    print(f"[OK] SES: {ses}")
    print(f"[OK] SVG: {svg} (网络数: {len(routes)}, 物理片段总数: {total_segments})")


if __name__ == "__main__":
    main()