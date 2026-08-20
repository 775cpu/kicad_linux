import os
import math
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union

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

def find_shortest_path_with_shapely(start_pt, end_pt, obstacle_polys, clearance=0.2):
    """
    利用 shapely 计算避障路径
    """
    p_start = Point(start_pt)
    p_end = Point(end_pt)
    
    if not obstacle_polys:
        return [start_pt, end_pt]
        
    # 合并所有障碍物并向外扩展避让间距 (Clearance)
    # buffer(clearance) 确保走线距离焊盘和边框保持安全间距
    all_obstacles = unary_union(obstacle_polys).buffer(clearance, join_style=2)
    
    # 尝试直接连线
    direct_line = LineString([p_start, p_end])
    if not direct_line.intersects(all_obstacles):
        return [start_pt, end_pt] # 如果直线不碰撞障碍，直接直达
        
    # 基础 A* / 候选点寻路（通过收集障碍物多边形的顶点作为导航路标点）
    nodes = [start_pt, end_pt]
    for poly in obstacle_polys:
        if poly.is_empty:
            continue
        coords = list(poly.exterior.coords)
        # 将多边形外扩一点作为安全路径点
        buffered_coords = list(poly.buffer(clearance).exterior.coords)
        for c in buffered_coords:
            nodes.append((c[0], c[1]))
            
    # 构建可见性图并用简单的 Dijkstra / A* 寻找最短无碰撞路径
    # 这里实现一个基于路标点的优化寻路：对每两个候选点检查连线是否穿过障碍
    def is_clear(pt1, pt2):
        line = LineString([pt1, pt2])
        return not line.intersects(all_obstacles)

    # 简单的图广度/最短路径搜索 (基于候选路标)
    import heapq
    
    graph = {node: [] for node in nodes}
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1, n2 = nodes[i], nodes[j]
            if is_clear(n1, n2):
                dist = math.hypot(n2[0]-n1[0], n2[1]-n1[1])
                graph[n1].append((dist, n2))
                graph[n2].append((dist, n1))
                
    # Dijkstra 算法
    queue = [(0.0, start_pt, [start_pt])]
    visited = set()
    
    while queue:
        cost, current, path = heapq.heappop(queue)
        if current == end_pt:
            return path
        if current in visited:
            continue
        visited.add(current)
        
        for weight, neighbor in graph.get(current, []):
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))
                
    # 如果复杂寻路未命中，退化返回折线或直接连线
    return [start_pt, end_pt]

def kicad_to_svg(kicad_input, layers='all', out_dir="generated/svg", file_name=None, start_end=None, clearance=0.3):
    """
    将 KiCad Footprint 转换为 SVG，支持基于 shapely 的自动避障走线。
    :param start_end: [ [x1, y1], [x2, y2] ] 只有传入该参数才开启自动避让布线
    :param clearance: 避让间距 (毫米)
    """
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
    obstacle_polys = []  # 用于 shapely 避障的多边形集合
    
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    def update_bounds(x, y, padding=2.0):
        nonlocal min_x, min_y, max_x, max_y
        min_x = min(min_x, float(x) - padding)
        min_y = min(min_y, float(y) - padding)
        max_x = max(max_x, float(x) + padding)
        max_y = max(max_y, float(y) + padding)

    # 1. 遍历并解析所有 KiCad 元素，同时构建 shapely 障碍物对象
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
                
                # 如果是 Edge.Cuts 或 *.Cu，加入障碍物统计
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
                
                # 将焊盘作为避障障碍物
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

    # 2. 如果传入了 start_end，调用 Shapely 自动避障寻路并渲染路径与起止十字标记
    if start_end and len(start_end) == 2:
        pt_start, pt_end = tuple(start_end[0]), tuple(start_end[1])
        
        # 计算避障路径
        routed_path = find_shortest_path_with_shapely(pt_start, pt_end, obstacle_polys, clearance=clearance)
        
        # 渲染寻路折线 (使用高亮亮绿色 #00FF00，线宽 0.4)
        path_points_str = " ".join([f"{p[0]},{p[1]}" for p in routed_path])
        svg_marks.append(
            f'  <!-- Auto Routed Path -->\n'
            f'  <polyline points="{path_points_str}" fill="none" stroke="#00FF00" stroke-width="0.4" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        
        # 渲染起止点的十字准星
        cross_size = 1.0
        for pt in [pt_start, pt_end]:
            px, py = pt[0], pt[1]
            update_bounds(px, py, cross_size + 1.0)
            svg_marks.append(
                f'  <line x1="{px - cross_size}" y1="{py}" x2="{px + cross_size}" y2="{py}" stroke="#00FF00" stroke-width="0.15" stroke-linecap="round"/>\n'
                f'  <line x1="{px}" y1="{py - cross_size}" x2="{px}" y2="{py + cross_size}" stroke="#00FF00" stroke-width="0.15" stroke-linecap="round"/>'
            )

    # 3. 组合图层 (底层铜皮 -> 钻孔挖空 -> 最顶层自动布线与标记)
    svg_elements.extend(svg_drills)
    svg_elements.extend(svg_marks)

    # 4. 生成规范对称的视口
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
        
    print(f"✅ SVG 自动布线及渲染已完成: {out_path} (间距 clearance: {clearance}mm)")

if __name__ == "__main__":
    # 调用示例：传入 start_end 后将自动开启 shapely 避障寻路
    kicad_to_svg(
        kicad_input="IBT_2x4-30x20.kicad_mod",
        layers=['F.Cu', 'B.Cu', 'Edge.Cuts', 'F.SilkS'],
        start_end=[[-3.81, -8.0], [-22.25, -3.0]],  # 开启自动布线
        clearance=0.35  # 可调的避让安全间距（单位：mm）
    )