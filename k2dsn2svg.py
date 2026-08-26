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
    for pad_name, shapes in pad_groups.items():
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
            
            if len(at) > 3:
                rot = float(at[3])
                if rot in (90, 270, -90, -270):
                    pw, ph = ph, pw

            min_x = min(min_x, px - pw / 2.0)
            max_x = max(max_x, px + pw / 2.0)
            min_y = min(min_y, py - ph / 2.0)
            max_y = max(max_y, py + ph / 2.0)

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


def make_dsn(
    name: str,
    pads: list[dict],
    obstacles: list[list[tuple[float, float]]],
    connections: list[tuple[int, int]],
    output: Path,
    routing_layers: list[str] = ["F.Cu"],
    trace_width: float = 0.254,
    clearance: float = 0.200,
    margin: float = 20.0,
) -> tuple[float, float, float, float]:
    """生成 DSN 文件，支持指定层、线宽、间距及板框外扩边距，并返回实际板框边界。"""
    
    width_um = int(trace_width * 1000)
    clearance_um = int(clearance * 1000)
    layers_str = " ".join(routing_layers)

    comp_min_x = min(p["x"] + p["rel_bounds"][0] for p in pads)
    comp_max_x = max(p["x"] + p["rel_bounds"][2] for p in pads)
    comp_min_y = min(p["y"] + p["rel_bounds"][1] for p in pads)
    comp_max_y = max(p["y"] + p["rel_bounds"][3] for p in pads)
    
    board_min_x, board_max_x = comp_min_x - margin, comp_max_x + margin
    board_min_y, board_max_y = comp_min_y - margin, comp_max_y + margin

    scale = 1000
    
    unique_padstacks = {}
    for pad in pads:
        rb = pad["rel_bounds"]
        rb_um = (rb[0]*scale, rb[1]*scale, rb[2]*scale, rb[3]*scale)
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
        f'    (boundary (path pcb 0 {board_min_x * scale:.0f} {board_min_y * scale:.0f} {board_max_x * scale:.0f} {board_min_y * scale:.0f} {board_max_x * scale:.0f} {board_max_y * scale:.0f} {board_min_x * scale:.0f} {board_max_y * scale:.0f} {board_min_x * scale:.0f} {board_min_y * scale:.0f}))',
        '    (via via0)',
        f'    (rule (width {width_um}) (clearance {clearance_um}))', 
        '  )',
        '  (placement',
        f'    (component {name}',
        '      (place U1 0 0 front 0)',
        '    )',
        '  )',
        '  (library',
        f'    (image {name}',
        f'      (outline (path signal 50 {comp_min_x * scale:.0f} {comp_min_y * scale:.0f} {comp_max_x * scale:.0f} {comp_min_y * scale:.0f} {comp_max_x * scale:.0f} {comp_max_y * scale:.0f} {comp_min_x * scale:.0f} {comp_max_y * scale:.0f} {comp_min_x * scale:.0f} {comp_min_y * scale:.0f}))',
    ]
    
    for pad in pads:
        lines.append(f'      (pin {pad["padstack"]} {pad["number"]} {pad["x"] * scale:.0f} {pad["y"] * scale:.0f})')
        
    lines += [
        '    )'
    ]
    
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
        f'      (circuit (use_layer {layers_str}) (use_via via0))', 
        f'      (rule (width {width_um}) (clearance {clearance_um}))', 
        '    )',
        '  )',
        ')',
        ''
    ]
    output.write_text("\n".join(lines), encoding="utf-8")
    return board_min_x, board_min_y, board_max_x, board_max_y


def parse_ses(ses_path: Path) -> dict[str, list[list[tuple[float, float]]]]:
    content = ses_path.read_text(encoding="utf-8")
    routes = {}
    
    net_blocks = re.split(r'\(\s*net\s+', content)[1:]
    for block in net_blocks:
        match = re.match(r'"?([^"\s()]+)"?', block)
        if not match:
            continue
        net_name = match.group(1)
        
        path_blocks = re.findall(r'\(\s*path\s+[^)]+\)', block)
        if path_blocks:
            if net_name not in routes:
                routes[net_name] = []
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
                    
    return routes


def render_svg(
    footprint: Path, 
    svg: Path, 
    routes: dict[str, list[list[tuple[float, float]]]], 
    trace_width: float = 0.254, 
    board_bounds: tuple[float, float, float, float] | None = None
) -> None:
    from k2svg import kicad_to_svg

    base_svg = svg.with_name(f".{svg.stem}.base.svg")
    kicad_to_svg(str(footprint), layers=["F.Cu", "B.Cu", "Edge.Cuts", "F.SilkS"], out_dir=str(svg.parent), file_name=base_svg.name)
    content = base_svg.read_text(encoding="utf-8")
    
    # 收集实际走线与封装的所有坐标范围，紧凑裁切 viewBox 消除巨额空白
    all_x, all_y = [], []
    for segments in routes.values():
        for pts in segments:
            for x, y in pts:
                all_x.append(x)
                all_y.append(y)

    if all_x and all_y:
        pad = 5.0  # 适当留白 5mm
        v_x1, v_y1 = min(all_x) - pad, min(all_y) - pad
        v_x2, v_y2 = max(all_x) + pad, max(all_y) + pad
        v_w, v_h = v_x2 - v_x1, v_y2 - v_y1

        # 重写 ViewBox 与背景 Rect，使其完美紧贴走线区域
        content = re.sub(r'viewBox="[^"]+"', f'viewBox="{v_x1:.3f} {v_y1:.3f} {v_w:.3f} {v_h:.3f}"', content)
        content = re.sub(r'width="[^"]+"', 'width="100%"', content, count=1)
        content = re.sub(r'height="[^"]+"', 'height="100%"', content, count=1)
        content = re.sub(r'<rect x="[^"]+" y="[^"]+" width="[^"]+" height="[^"]+" fill="#000000"[^>]*>', 
                         f'<rect x="{v_x1:.3f}" y="{v_y1:.3f}" width="{v_w:.3f}" height="{v_h:.3f}" fill="#000000" />', content)

    marks = []
    
    # 绘制 FreeRouting 实际边界与中心十字
    if board_bounds:
        bx1, by1, bx2, by2 = board_bounds
        w = bx2 - bx1
        h = by2 - by1
        cx = (bx1 + bx2) / 2.0
        cy = (by1 + by2) / 2.0
        
        cross_size = 1  # 十字标尺寸 3mm
        
        marks.append(f'  <!-- FreeRouting Boundary -->')
        marks.append(f'  <rect x="{bx1:.3f}" y="{by1:.3f}" width="{w:.3f}" height="{h:.3f}" fill="none" stroke="red" stroke-width="0.1" stroke-dasharray="2,2"/>')
        marks.append(f'  <!-- Center Cross -->')
        marks.append(f'  <line x1="{cx - cross_size:.3f}" y1="{cy:.3f}" x2="{cx + cross_size:.3f}" y2="{cy:.3f}" stroke="red" stroke-width="0.1"/>')
        marks.append(f'  <line x1="{cx:.3f}" y1="{cy - cross_size:.3f}" x2="{cx:.3f}" y2="{cy + cross_size:.3f}" stroke="red" stroke-width="0.1"/>')

    colors = ["#00FF00", "#00BFFF", "#FFB000", "#FF4FA3", "#A8FF00", "#FFFFFF"]
    for index, (net, segments) in enumerate(routes.items()):
        color = colors[index % len(colors)]
        for points in segments:
            points_text = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
            marks.append(f'  <!-- FreeRouting {net} -->\n  <polyline points="{points_text}" fill="none" stroke="{color}" stroke-width="{trace_width:.3f}" stroke-linecap="round" stroke-linejoin="round"/>')
            
    content = content.replace("\n</svg>", "\n" + "\n".join(marks) + "\n</svg>")
    svg.write_text(content, encoding="utf-8")
    if base_svg.exists():
        base_svg.unlink()


def print_multi_dot_lines(routes: dict[str, list[list[tuple[float, float]]]], trace_width: float = 0.254, layer: str = "F.Cu") -> None:
    """Print SES routes as reusable KiCad multi_dot_line calls."""
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
        print(f"multi_dot_line(kicad_mod, [{dots}], width={trace_width}, layers='{layer}',)")


def main() -> None:
    try:
        from kicad import Q; print(Q.IBT_2x4())
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "IBT_2x4-30x20.kicad_mod")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "generated" / "svg")
    parser.add_argument("--jar", type=Path, default=DEFAULT_JAR)
    
    parser.add_argument("--layers", nargs="+", default=["F.Cu"], help="允许布线的层，如 F.Cu B.Cu")
    parser.add_argument("--trace-width", type=float, default=0.254, help="线宽 (mm)，默认 0.254")
    parser.add_argument("--clearance", type=float, default=0.5, help="安全间距 (mm)，默认 0.200")
    parser.add_argument("--margin", type=float, default=20.0, help="板框外扩边距 (mm)，默认 20.0")
    parser.add_argument("--passes", type=int, default=100, help="FreeRouting 路由最大迭代次数 (-mp)，默认 100")
    # 新增：动态接线表
    parser.add_argument("--connect",'-c', nargs="+", help="自定义连接关系，格式为 引脚A:引脚B，例如 --connect 1:9 2:10")
    
    args = parser.parse_args()

    ensure_runtime(args.jar)
    name, pads, obstacles = read_footprint(args.input)
    
    # ==== 连接关系生成（替换原硬编码） ====
    if args.connect:
        connections = []
        pad_num_to_idx = {p["number"]: i for i, p in enumerate(pads)}
        for pair in args.connect:
            if ":" not in pair:
                raise ValueError(f"连接对格式错误: {pair}，应为 引脚A:引脚B")
            a, b = pair.split(":")
            a, b = a.strip(), b.strip()
            # 尝试作为索引解析
            try:
                idx_a = int(a)
                idx_b = int(b)
                if idx_a < 0 or idx_a >= len(pads) or idx_b < 0 or idx_b >= len(pads):
                    raise ValueError
                connections.append((idx_a, idx_b))
            except ValueError:
                # 尝试作为 pad number 解析（如 P0:P1）
                if a in pad_num_to_idx and b in pad_num_to_idx:
                    connections.append((pad_num_to_idx[a], pad_num_to_idx[b]))
                else:
                    raise ValueError(f"无法解析连接对: {pair}，请使用有效索引或 pad 编号（如 P0:P1）")
    else:
        # 默认连接逻辑：若引脚数 >= 16，采用原 16 脚排布；否则两两相邻连接
        if len(pads) >= 16:
            connections = [(i, 8 + i) for i in range(4)] + [(4 + i, 12 + i) for i in range(4)]
        else:
            pad_names = [p["number"] for p in pads]
            connections = [(i, i+1) for i in range(0, len(pad_names)-1, 2)]
    
    dsn = args.output_dir / f"{name}.dsn"
    ses = args.output_dir / f"{name}.ses"
    svg = args.output_dir / f"{name}-freerouting.svg"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    board_bounds = make_dsn(
        name=name,
        pads=pads,
        obstacles=obstacles,
        connections=connections,
        output=dsn,
        routing_layers=args.layers,
        trace_width=args.trace_width,
        clearance=args.clearance,
        margin=args.margin,
    )

    cmd = [
        "java", "-jar", str(args.jar),
        "-de", str(dsn),
        "-do", str(ses),
        "-mp", str(args.passes)
    ]
    subprocess.run(cmd, check=True)
    
    routes = parse_ses(ses)
    
    render_svg(args.input, svg, routes, trace_width=args.trace_width, board_bounds=board_bounds)
    
    if len(routes) != len(connections):
        raise RuntimeError(
            f"布线层: {args.layers}, 线宽: {args.trace_width}mm, 安全间距: {args.clearance}mm, "
            f"板框边距: {args.margin}mm, 迭代上限: {args.passes} | 期望 {len(connections)} 条网络，实际得到 {len(routes)} 条"
        )

    print_multi_dot_lines(routes, trace_width=args.trace_width, layer=args.layers[0])
        
    total_segments = sum(len(segs) for segs in routes.values())
    print(f"[OK] DSN: {dsn}")
    print(f"[OK] SES: {ses}")
    print(f"[OK] SVG: {svg} (网络数: {len(routes)}, 物理片段总数: {total_segments})")
    print(f"[配置] 布线层: {args.layers}, 线宽: {args.trace_width}mm, 安全间距: {args.clearance}mm, 板框边距: {args.margin}mm, 迭代上限: {args.passes}")


if __name__ == "__main__":
    main()