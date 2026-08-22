import os
import math
import heapq
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
from shapely.prepared import prep

def parse_sexp(string):
    """极简的 S-expression 解析器"""
    sexp = [[]]
    word = ''
    in_str = False
    for char in string:
        if char == '"':
            in_str = not in_str
        elif in_str:
            word += char
        elif char == '(':
            sexp.append([])
        elif char == ')':
            if word:
                sexp[-1].append(word)
                word = ''
            temp = sexp.pop()
            sexp[-1].append(temp)
        elif char in (' ', '\t', '\n', '\r'):
            if word:
                sexp[-1].append(word)
                word = ''
        else:
            word += char
    return sexp[0][0] if sexp and sexp[0] else []

def find_sub(item, key):
    """查找指定的子节点"""
    for sub in item:
        if isinstance(sub, list) and sub and sub[0] == key:
            return sub
    return None

def layer_match(item_layers, target_layers):
    """判断元素的图层是否在需要渲染的图层列表中"""
    if target_layers == 'all':
        return True
    if isinstance(item_layers, str):
        item_layers = [item_layers]
        
    for il in item_layers:
        if il in target_layers:
            return True
        if il == '*.Cu' and any(tl.endswith('.Cu') for tl in target_layers):
            return True
        if il == '*.Mask' and any(tl.endswith('.Mask') for tl in target_layers):
            return True
    return False

def find_octilinear_path(start_pt, end_pt, obstacle_polys, clearance=0.35, step=0.1,
                         clearance_weight=6.0, clearance_falloff=1.5,
                         turn_penalty=0.8, escape_length=2.0,
                         escape_start_dir=None, escape_end_dir=None):
    """
    利用网格化 A* 计算严格 45 度和 90 度的避障路径。

    优化点：
    1. 梯度代价场：越靠近焊盘/障碍物，通行代价越高，空旷区域代价低。
    2. 拐弯惩罚：每次改变方向都会叠加额外代价，抑制频繁 45 度微调。
    3. 出线方向约束：起终点先向空旷区域引出，再进入主通道寻路。
    """
    p_start = Point(start_pt)
    p_end = Point(end_pt)
    
    safe_obstacle_polys = []
    for poly in obstacle_polys:
        # 核心优化：豁免包含了起点或终点本身的焊盘障碍物，允许走线从中安全穿出
        if poly.distance(p_start) < 0.1 or poly.distance(p_end) < 0.1:
            continue
        safe_obstacle_polys.append(poly)
        
    if safe_obstacle_polys:
        all_obstacles = unary_union(safe_obstacle_polys).buffer(clearance, join_style=2)
        prep_obstacles = prep(all_obstacles)  # 加速碰撞计算
        bx1, by1, bx2, by2 = all_obstacles.bounds
        minx = min(bx1, start_pt[0], end_pt[0]) - 5.0
        miny = min(by1, start_pt[1], end_pt[1]) - 5.0
        maxx = max(bx2, start_pt[0], end_pt[0]) + 5.0
        maxy = max(by2, start_pt[1], end_pt[1]) + 5.0
    else:
        all_obstacles = None
        prep_obstacles = None
        minx, miny = min(start_pt[0], end_pt[0]) - 5, min(start_pt[1], end_pt[1]) - 5
        maxx, maxy = max(start_pt[0], end_pt[0]) + 5, max(start_pt[1], end_pt[1]) + 5

    # 坐标系到网格映射
    def to_grid(pt):
        return (int(round(pt[0] / step)), int(round(pt[1] / step)))
    def to_pt(g):
        return (round(g[0] * step, 3), round(g[1] * step, 3))

    # 8方向移动 (dx, dy, cost)
    dirs = [
        (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (-1, -1, 1.414)
    ]
    dir_index = {(dx, dy): i for i, (dx, dy, _) in enumerate(dirs)}

    def resolve_dir_idx(vec):
        """将任意方向向量解析到最近的 8 方向索引"""
        if vec is None:
            return None
        vx, vy = vec[0], vec[1]
        norm = math.hypot(vx, vy)
        if norm < 1e-9:
            return None
        vx, vy = vx / norm, vy / norm
        best_i = None
        best_dot = -2.0
        for i, (dx, dy, cost) in enumerate(dirs):
            ux, uy = dx / cost, dy / cost
            dot = vx * ux + vy * uy
            if dot > best_dot:
                best_dot = dot
                best_i = i
        return best_i

    def suggest_escape_dir(pt, other_pt):
        """
        自动建议出线方向：
        综合考虑“指向目标的趋势”和“路径的空旷程度”。优先向开阔区域引出。
        """
        if prep_obstacles is None:
            return None

        # 到另一端点的方向向量
        v_to = (other_pt[0] - pt[0], other_pt[1] - pt[1])
        norm = math.hypot(v_to[0], v_to[1])
        if norm < 1e-9:
            v_to = (0.0, 0.0)
        else:
            v_to = (v_to[0] / norm, v_to[1] / norm)

        best_idx = None
        best_score = -float('inf')

        for idx, (dx, dy, cost) in enumerate(dirs):
            ux, uy = dx / cost, dy / cost
            feasible = True
            
            clearance_sum = 0.0
            steps = int(round(escape_length / step))

            # 检查 escape_length 范围内是否全部可通行，并采集沿途的空旷度数据
            for s in range(1, steps + 1):
                sx = pt[0] + ux * s * step
                sy = pt[1] + uy * s * step
                p_check = Point(sx, sy)
                
                if sx < minx or sx > maxx or sy < miny or sy > maxy:
                    feasible = False
                    break
                if prep_obstacles.intersects(p_check):
                    feasible = False
                    break
                    
                if all_obstacles is not None:
                    # 获取该点到障碍物的距离，距离越远代表越空旷
                    dist = all_obstacles.distance(p_check)
                    clearance_sum += dist

            if not feasible:
                continue

            # 1. 目标方向契合度 (范围: -1.0 到 1.0)
            dot = ux * v_to[0] + uy * v_to[1]
            
            # 2. 空间空旷度 (该方向上平均多出的安全距离，单位 mm)
            avg_clearance = clearance_sum / steps if steps > 0 else 0
            
            # 核心优化：综合评分！
            # 权重 1.5 意味着：每多出 1mm 的空旷空间，就足以抵消 90 度的方向偏差。
            # 这会让走线在面临“拥挤的捷径”和“宽敞的弯路”时，果断选择宽敞的弯路。
            score = dot + (avg_clearance * 1.5)

            # 略偏向于 90 度正交轴方向出线，能让起步更方正美观
            if cost == 1.0:
                score += 0.1

            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx
    
    # 自动或手动确定出线方向
    if escape_start_dir is not None:
        escape_start_idx = resolve_dir_idx(escape_start_dir)
    else:
        escape_start_idx = suggest_escape_dir(start_pt, end_pt)

    if escape_end_dir is not None:
        escape_end_idx = resolve_dir_idx(escape_end_dir)
    else:
        escape_end_idx = suggest_escape_dir(end_pt, start_pt)

    # 构建起终点出线段
    pre_points = [start_pt]
    post_points = [end_pt]
    a_start = start_pt
    a_end = end_pt
    initial_dir_idx = None

    if escape_start_idx is not None:
        dx, dy, cost = dirs[escape_start_idx]
        ux, uy = dx / cost, dy / cost
        raw_escape_start = (start_pt[0] + ux * escape_length, start_pt[1] + uy * escape_length)
        # 吸附到网格，保持 A* 起点一致
        escape_start_pt = to_pt(to_grid(raw_escape_start))
        pre_points.append(escape_start_pt)
        a_start = escape_start_pt
        initial_dir_idx = escape_start_idx

    if escape_end_idx is not None:
        dx, dy, cost = dirs[escape_end_idx]
        ux, uy = dx / cost, dy / cost
        raw_escape_end = (end_pt[0] + ux * escape_length, end_pt[1] + uy * escape_length)
        escape_end_pt = to_pt(to_grid(raw_escape_end))
        post_points = [escape_end_pt, end_pt]
        a_end = escape_end_pt

    def merge_points(points):
        """合并相邻重复点"""
        merged = []
        for p in points:
            if not merged or math.hypot(p[0] - merged[-1][0], p[1] - merged[-1][1]) > 1e-6:
                merged.append(p)
        return merged

    def astar(start_pt_arg, end_pt_arg, start_dir_idx=None):
        """带梯度代价场和拐弯惩罚的 8 方向 A*"""
        start_g = to_grid(start_pt_arg)
        end_g = to_grid(end_pt_arg)

        # 缓存到障碍物的距离，避免重复计算
        dist_cache = {}

        def is_valid(gx, gy):
            if (gx, gy) == start_g or (gx, gy) == end_g:
                return True
            x, y = gx * step, gy * step
            if x < minx or x > maxx or y < miny or y > maxy:
                return False
            if prep_obstacles is None:
                return True
            return not prep_obstacles.intersects(Point(x, y))

        def clearance_penalty(gx, gy):
            """越靠近障碍物，代价越高；越空旷，代价越低"""
            if all_obstacles is None or clearance_weight <= 0:
                return 0.0
            if (gx, gy) == start_g or (gx, gy) == end_g:
                return 0.0
            key = (gx, gy)
            if key in dist_cache:
                d = dist_cache[key]
            else:
                x, y = gx * step, gy * step
                d = all_obstacles.distance(Point(x, y))
                dist_cache[key] = d
            if d <= 0:
                return 0.0
            return clearance_weight * math.exp(-d / clearance_falloff)

        def turn_cost(prev_idx, next_idx):
            """拐弯惩罚：45 度惩罚 = turn_penalty，90 度 = 2*turn_penalty，135 度 = 3*turn_penalty"""
            if prev_idx is None or prev_idx == next_idx:
                return 0.0
            dx1, dy1, _ = dirs[prev_idx]
            dx2, dy2, _ = dirs[next_idx]
            dot = (dx1 * dx2 + dy1 * dy2) / (math.hypot(dx1, dy1) * math.hypot(dx2, dy2))
            dot = max(-1.0, min(1.0, dot))
            angle = math.acos(dot)
            return turn_penalty * (angle / (math.pi / 4.0))

        def heuristic(gx, gy):
            hx = abs(gx - end_g[0])
            hy = abs(gy - end_g[1])
            return 1.0 * max(hx, hy) + 0.414 * min(hx, hy)

        start_state = (start_g[0], start_g[1], start_dir_idx)
        queue = [(0.0 + heuristic(start_g[0], start_g[1]), 0.0, start_state, None)]
        visited = set()
        came_from = {}
        goal_state = None

        while queue:
            f, g, curr, parent = heapq.heappop(queue)

            if curr in visited:
                continue
            visited.add(curr)
            came_from[curr] = parent

            if (curr[0], curr[1]) == end_g:
                goal_state = curr
                break

            curr_dir_idx = curr[2]
            for idx, (dx, dy, cost) in enumerate(dirs):
                nxt = (curr[0] + dx, curr[1] + dy)
                if not is_valid(nxt[0], nxt[1]):
                    continue

                next_state = (nxt[0], nxt[1], idx)
                if next_state in visited:
                    continue

                step_cost = cost
                step_cost += clearance_penalty(nxt[0], nxt[1])
                step_cost += turn_cost(curr_dir_idx, idx)

                new_g = g + step_cost
                h = heuristic(nxt[0], nxt[1])
                heapq.heappush(queue, (new_g + h, new_g, next_state, curr))

        if goal_state is None:
            return None

        # 回溯网格路径
        g_path = []
        curr = goal_state
        while curr is not None:
            g_path.append((curr[0], curr[1]))
            curr = came_from.get(curr)
        g_path.reverse()

        # 去重相邻网格
        dedup = []
        for g in g_path:
            if not dedup or g != dedup[-1]:
                dedup.append(g)
        g_path = dedup

        # 路径简化：只保留真正的拐点
        if len(g_path) <= 2:
            astar_path = [to_pt(g) for g in g_path]
        else:
            simplified = [g_path[0]]
            prev_dx = g_path[1][0] - g_path[0][0]
            prev_dy = g_path[1][1] - g_path[0][1]

            for i in range(1, len(g_path) - 1):
                dx = g_path[i + 1][0] - g_path[i][0]
                dy = g_path[i + 1][1] - g_path[i][1]
                if dx != prev_dx or dy != prev_dy:
                    simplified.append(g_path[i])
                    prev_dx = dx
                    prev_dy = dy

            simplified.append(g_path[-1])
            astar_path = [to_pt(g) for g in simplified]

        return astar_path

    # 优先尝试带出线段的分段寻路
    routed = None
    if escape_start_idx is not None or escape_end_idx is not None:
        routed = astar(a_start, a_end, initial_dir_idx)
        if routed is not None:
            final_path = merge_points(pre_points + routed + post_points)
            if final_path:
                print(f"\n✅ 自动寻路完成 (间距 {clearance}mm，启用空旷区优化)。提取到 {len(final_path)} 个关键控制点：")
                for idx, pt in enumerate(final_path):
                    print(f"  [{idx}] : X={pt[0]:.3f}, Y={pt[1]:.3f}")
                print("-" * 30)
                return final_path

    # 回退：不强制出线段，直接 A*
    routed = astar(start_pt, end_pt, None)
    if routed is not None:
        final_path = merge_points(routed)
        print(f"\n✅ 自动寻路完成 (间距 {clearance}mm，未使用出线约束)。提取到 {len(final_path)} 个关键控制点：")
        for idx, pt in enumerate(final_path):
            print(f"  [{idx}] : X={pt[0]:.3f}, Y={pt[1]:.3f}")
        print("-" * 30)
        return final_path

    # 最终回退：直线
    print(f"⚠️ [警告] 无法找到 {clearance}mm 避障距离下的45度/90度连线，退化为直线。")
    return [start_pt, end_pt]

def kicad_to_svg(kicad_input, layers='all', out_dir="generated/svg", file_name=None,
                 start_end=None, clearance=0.35,
                 clearance_weight=6.0, clearance_falloff=1.5,
                 turn_penalty=0.8, escape_length=2.0):
    """将 KiCad Footprint 转换为 SVG，支持纯45/90度自动避障走线。"""
    if isinstance(kicad_input, str) and os.path.exists(kicad_input):
        with open(kicad_input, 'r', encoding='utf-8') as f:
            content = f.read()
    elif hasattr(kicad_input, 'get_str'):
        content = kicad_input.get_str()
    elif hasattr(kicad_input, '__str__'):
        content = str(kicad_input)
    else:
        raise ValueError("不支持的输入格式或文件不存在")

    data = parse_sexp(content)
    if not data or data[0] != 'module':
        raise ValueError("无效的 kicad_mod 内容")

    module_name = data[1] if len(data) > 1 else "output"
    if not file_name:
        if isinstance(kicad_input, str) and os.path.exists(kicad_input):
            file_name = os.path.basename(kicad_input).replace('.kicad_mod', '.svg')
        else:
            file_name = f"{module_name}.svg"

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, file_name)

    colors = {
        'F.Cu': '#D45D5D',      
        'B.Cu': '#4264BA',      
        'F.SilkS': '#E6E6E6',   
        'Edge.Cuts': '#C7C72A', 
        'Thru_Hole': '#D45D5D'  
    }

    svg_elements = []
    svg_drills = []
    svg_marks = []
    obstacle_polys = []  # 障碍物
    
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    def update_bounds(x, y, padding=2.0):
        nonlocal min_x, min_y, max_x, max_y
        min_x = min(min_x, float(x) - padding)
        min_y = min(min_y, float(y) - padding)
        max_x = max(max_x, float(x) + padding)
        max_y = max(max_y, float(y) + padding)

    # 1. 遍历并建立多边形障碍网
    for item in data[2:]:
        if not isinstance(item, list) or not item:
            continue
            
        type_name = item[0]

        if type_name == 'fp_line':
            layer_node = find_sub(item, 'layer')
            l_name = layer_node[1] if layer_node and len(layer_node) > 1 else 'F.SilkS'
            
            start = find_sub(item, 'start')
            end = find_sub(item, 'end')
            width = find_sub(item, 'width')
            
            if start and end:
                x1, y1 = float(start[1]), float(start[2])
                x2, y2 = float(end[1]), float(end[2])
                
                if l_name == 'Edge.Cuts' or l_name.endswith('.Cu'):
                    line_geom = LineString([(x1, y1), (x2, y2)]).buffer(0.1)
                    obstacle_polys.append(line_geom)

                if layer_match(l_name, layers):
                    raw_w = float(width[1]) if width else 0.15
                    w = max(raw_w, 0.05) 
                    color = colors.get(l_name, '#AAAAAA')
                    update_bounds(x1, y1)
                    update_bounds(x2, y2)
                    svg_elements.append(
                        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                        f'stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
                    )

        elif type_name == 'fp_poly':
            layer_node = find_sub(item, 'layer')
            l_name = layer_node[1] if layer_node and len(layer_node) > 1 else 'F.Cu'
            
            pts_node = find_sub(item, 'pts')
            if pts_node:
                points = []
                for pt in pts_node[1:]:
                    if pt[0] == 'xy':
                        points.append((float(pt[1]), float(pt[2])))
                        update_bounds(float(pt[1]), float(pt[2]))
                
                if len(points) >= 3:
                    poly_geom = Polygon(points)
                    obstacle_polys.append(poly_geom)

                if layer_match(l_name, layers):
                    points_str = [f"{p[0]},{p[1]}" for p in points]
                    color = colors.get(l_name, colors['F.Cu'])
                    svg_elements.append(
                        f'<polygon points="{" ".join(points_str)}" '
                        f'fill="{color}" opacity="0.7" stroke="{color}" stroke-width="0.05"/>'
                    )

        elif type_name == 'pad':
            layers_node = find_sub(item, 'layers')
            pad_layers = layers_node[1:] if layers_node else []

            pad_type = item[2]
            pad_shape = item[3]
            at = find_sub(item, 'at')
            size = find_sub(item, 'size')
            drill = find_sub(item, 'drill')
            
            if at and size:
                x, y = float(at[1]), float(at[2])
                w, h = float(size[1]), float(size[2])
                rot = float(at[3]) if len(at) > 3 else 0.0
                
                update_bounds(x, y, max(w, h)/2)
                
                if any(pl.endswith('.Cu') for pl in pad_layers) or pad_type == 'thru_hole':
                    pad_box = Polygon([
                        (x - w/2, y - h/2), (x + w/2, y - h/2),
                        (x + w/2, y + h/2), (x - w/2, y + h/2)
                    ])
                    obstacle_polys.append(pad_box)

                if layer_match(pad_layers, layers):
                    transform = f' transform="rotate({-rot}, {x}, {y})"' if rot != 0 else ''
                    color = colors.get('Thru_Hole') if pad_type == 'thru_hole' else colors.get('F.Cu')
                    
                    if pad_shape in ['rect', 'roundrect']:
                        px, py = x - w/2, y - h/2
                        rx = min(w, h) * 0.2 if pad_shape == 'roundrect' else 0
                        svg_elements.append(
                            f'<rect x="{px}" y="{py}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
                            f'fill="{color}" opacity="0.85"{transform}/>'
                        )
                    elif pad_shape == 'circle':
                        r = max(w, h) / 2
                        svg_elements.append(
                            f'<circle cx="{x}" cy="{y}" r="{r}" '
                            f'fill="{color}" opacity="0.85"/>'
                        )
                    elif pad_shape == 'oval':
                        r = min(w, h) / 2
                        px, py = x - w/2, y - h/2
                        svg_elements.append(
                            f'<rect x="{px}" y="{py}" width="{w}" height="{h}" rx="{r}" ry="{r}" '
                            f'fill="{color}" opacity="0.85"{transform}/>'
                        )
                
                if drill:
                    d = float(drill[1])
                    svg_drills.append(
                        f'<circle cx="{x}" cy="{y}" r="{d/2}" fill="#0A0A0A"/>'
                    )

    # 2. 调用 A* 函数执行布线
    if start_end and len(start_end) == 2:
        pt_start, pt_end = tuple(start_end[0]), tuple(start_end[1])
        
        # 自动避让间距为 clearance，寻路网格精度为 0.1mm
        routed_path = find_octilinear_path(
            pt_start, pt_end, obstacle_polys,
            clearance=clearance,
            step=0.1,
            clearance_weight=clearance_weight,
            clearance_falloff=clearance_falloff,
            turn_penalty=turn_penalty,
            escape_length=escape_length
        )
        
        # 渲染走线
        path_points_str = " ".join([f"{p[0]},{p[1]}" for p in routed_path])
        svg_marks.append(
            f'  <!-- Octilinear Auto Routed Path -->\n'
            f'  <polyline points="{path_points_str}" fill="none" stroke="#00FF00" stroke-width="0.4" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        
        # 渲染首尾的绿色十字准星
        cross_size = 1.0
        for pt in [pt_start, pt_end]:
            px, py = pt[0], pt[1]
            update_bounds(px, py, cross_size + 1.0)
            svg_marks.append(
                f'  <line x1="{px - cross_size}" y1="{py}" x2="{px + cross_size}" y2="{py}" stroke="#00FF00" stroke-width="0.15" stroke-linecap="round"/>\n'
                f'  <line x1="{px}" y1="{py - cross_size}" x2="{px}" y2="{py + cross_size}" stroke="#00FF00" stroke-width="0.15" stroke-linecap="round"/>'
            )

    svg_elements.extend(svg_drills)
    svg_elements.extend(svg_marks)

    # 生成居中的视口区域
    if min_x == float('inf'): 
        bound_x, bound_y = 15, 10
    else:
        bound_x = max(abs(min_x), abs(max_x)) + 2
        bound_y = max(abs(min_y), abs(max_y)) + 2

    width = bound_x * 2
    height = bound_y * 2
    view_min_x = -bound_x
    view_min_y = -bound_y

    svg_header = (
        f'<?xml version="1.0" encoding="utf-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{view_min_x} {view_min_y} {width} {height}" '
        f'width="{width * 20}px" height="{height * 20}px">\n'
        f'  <rect x="{view_min_x}" y="{view_min_y}" width="{width}" height="{height}" fill="#0A0A0A"/>\n'
    )
    svg_footer = '\n</svg>'
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(svg_header)
        f.write("\n  ".join(svg_elements))
        f.write(svg_footer)
        
    print(f"✅ SVG 保存成功: {out_path}")

if __name__ == "__main__":
    kicad_to_svg(
        kicad_input="IBT_2x4-30x20.kicad_mod",
        layers=['F.Cu', 'B.Cu', 'Edge.Cuts', 'F.SilkS'],
        start_end=[[-3.81, -8.0], [-22.25, -3.0]],
        clearance=0.35
    )