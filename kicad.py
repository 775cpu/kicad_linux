#coding=utf-8
# import sys,pathlib				 # .py/qgb   / 
# gsqp=pathlib.Path(__file__).absolute().parent.parent.absolute().__str__()
# if gsqp not in sys.path:sys.path.append(gsqp)#py3 works
# from qgb import py
# U,T,N,F=py.importUTNF()

import sys
py=sys.modules['qgb.py']
U=sys.modules['qgb.U']
T=sys.modules['qgb.T']
N=sys.modules['qgb.N']
F=sys.modules['qgb.F']



try:
    import math
    from KicadModTree import *
    import KicadModTree
    import pcbnew
    
except Exception as e:print('import pcbnew',e)	
################################################
import locale
locale.setlocale(locale.LC_ALL, '')

glayers_edge_fsilk=['Edge.Cuts','F.SilkS',]
glayers_edge=['Edge.Cuts','F.SilkS','Edge.Cuts','B.SilkS',]
glayers_edge_pure=['Edge.Cuts',]
glayers_silk=['F.SilkS','B.SilkS',]# cyan 蓝绿
glayers_F_Cu=['F.Cu',]# 红
glayers_F_Mask=['F.Mask',]# 粉红
glayers_FB_Cu=['F.Cu','B.Cu',]# 
glayers_FB_Mask=['F.Mask','B.Mask',]# 
glayers_cmts=glayers_Cmts=["Cmts.User",] #注释层(文档层) ，蓝   
#'User.1','User.2' "F.Fab" 导入lceda后也是 文档层
################################################
def new_kicad_mod(name='',w=100,h=100,text_at=(11,4),edge_layers=('F.SilkS',),add_time=False,start=[0,0],**ka):
    ''' edge function only F.SilkS '''
    if start in ['mid','-w/2,-h/2']:start=-w/2,-h/2
    if not name:
        if add_time:add_time='-t'+U.stime()[12:17]
        else:add_time=''
        import inspect
        frame=inspect.currentframe()
        frame=frame.f_back
        if ka:ka=T.replace_multi_target(T.repr_without_space(ka),olds=list('{}'+T.quote+T.double_quote),).replace(':','=')
        else :ka=''
        name=frame.f_code.co_name+f'-{w}x{h}{ka}{add_time}'
    
    kicad_mod = KicadModTree.nodes.Footprint(name)
    kicad_mod.setDescription(name)
    
    for n,i in enumerate(text_at.copy()):
        if py.istr(i):
            text_at[n]=eval(i) # start='-w/2,-h/2', text_at  '-h/2+1'  正好贴上沿，在板内
    km_text(kicad_mod,name,at=text_at)  #没有这句 lceda 导入错误
    if w and h:
        edge(kicad_mod,start=start,end=[start[0]+w,start[1]+h],layers=edge_layers)
        assert kicad_mod.attribute==None
        kicad_mod.qgb_dict=dict(w=w,h=h)
    return kicad_mod
def write_kicad_mod(kicad_mod,zip=True):
    file_handler = KicadModTree.KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(kicad_mod.name)}.kicad_mod'
    file_handler.writeFile(fname)
    if zip:F.zip(fname)
    return kicad_mod,fname	
    
def write_gbr(output_dir=py.No(r'default kicad_pcb\qgb_export'),zip=1):
    board=pcbnew.GetBoard()
    pc=pcbnew.PLOT_CONTROLLER(board)
    plot_options = pc.GetPlotOptions()

    name,sp=get_board_name(board,return_dir=1)
    if py.isNo(output_dir):
        output_dir=sp+'qgb_export/'
    if 'qgb_export' in output_dir:
        od=F.delete_dir(output_dir)
        U.set('od',[output_dir,od])
    output_dir=F.mkdir(output_dir)
    # 设置 Gerber 文件的输出选项
    plot_options.SetOutputDirectory(output_dir)
    plot_options.SetPlotFrameRef(False)
    plot_options.SetPlotValue(True)
    plot_options.SetPlotReference(True)
    plot_options.SetPlotInvisibleText(False)
    plot_options.SetExcludeEdgeLayer(True)
    plot_options.SetUseAuxOrigin(True)

    # 设置 Gerber 文件的格式
    plot_options.SetGerberPrecision(6)  # 6 digits after the decimal point
    plot_options.SetCreateGerberJobFile(True)

    # 导出所有层
    layers = [
        (pcbnew.F_Cu, "F.Cu"),
        (pcbnew.B_Cu, "B.Cu"),
        (pcbnew.F_SilkS, "F.SilkS"),
        (pcbnew.B_SilkS, "B.SilkS"),
        (pcbnew.F_Mask, "F.Mask"),
        (pcbnew.B_Mask, "B.Mask"),
        (pcbnew.F_Paste, "F.Paste"),
        (pcbnew.B_Paste, "B.Paste"),
        (pcbnew.Edge_Cuts, "Edge.Cuts"),
    ]

    for layer, layer_name in layers:
        pc.SetLayer(layer)
        pc.OpenPlotfile(layer_name, pcbnew.PLOT_FORMAT_GERBER, layer_name)
        pc.PlotLayer()
    # 导出钻孔文件
    drl_writer = pcbnew.EXCELLON_WRITER(board)
    drl_writer.SetFormat(True, 6, 3)  # 6 digits after the decimal point, 3 digits before
    drl_writer.SetOptions(False, False,board.GetDesignSettings().GetAuxOrigin(), False)
    drl_writer.CreateDrillandMapFilesSet(output_dir, True, False)
    
    # F.ll(output_dir,return_list=1)
    fs=F.ls(output_dir,)
    fz=py.No('no zip')
    zfn=''
    if zip:
        
        zfn=F.get_parent_dir(output_dir)+f'{name}.zip'
        # U.set('zfn',zfn)
        fz=F.zip(*fs,zip_filename=zfn,only_filename=1)
    return board,pc,plot_options,drl_writer,fs,fz,zfn,U.stime()
write_pcb=write_gbr
        
def get_board_name(board=None,return_dir=False):
    if not board:board=pcbnew.GetBoard()
    fn=board.GetFileName()
    assert fn.endswith('.kicad_pcb')
    sp=F.get_splitor(fn)
    name=T.sub_last(fn,sp,'.kicad_pcb')
    if return_dir:
        sd=T.sub_last(fn,'',name+'.kicad_pcb')
        return name,sd
    return name
get_pcb_name=get_board_name

def board_add_track(start,end,width=1):
    import pcbnew
    board = pcbnew.GetBoard()  # 获取当前PCB板对象
    track = pcbnew.PCB_TRACK(board)  # 创建走线对象
    track.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(start), pcbnew.FromMM(start)))  # 设置起点坐标(毫米转纳米)
    track.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(end), pcbnew.FromMM(end)))  # 设置终点坐标
    track.SetWidth(pcbnew.FromMM(width))  # 设置线宽(毫米转纳米)
    board.Add(track)  # 将走线添加到PCB板
    return board, track  # 返回PCB板和走线对象
pcb_add_track=pcb_add_wire=board_add_track	
        
def distance(p1,p2):
    return ((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)**0.5

def text(kicad_mod,t,x=0,y=0,size=[1,1],layers=glayers_silk,at=None, **ka):
    if at:x,y=at
    if py.isint(size) or py.isfloat(size):size=[size,size]
    for layer in get_layers(layers, ka):
        kicad_mod.append(KicadModTree.Text(type='user', text=t, at=[x,y],size=size,layer=layer))
txt=text                           

def non_plated_hole(kicad_mod,x,y,diameter=0,number='',**ka):
    diameter=U.get_duplicated_kargs(ka,'diameter','d','D',default=diameter)
    # if diameter and not d:d=diameter
    if not diameter:return x,y
    if not number:number=f'{diameter}-{x},{y}'
    kicad_mod.append(Pad(number=number,type=Pad.TYPE_NPTH,shape=Pad.SHAPE_CIRCLE,layers=Pad.LAYERS_NPTH,at=[x,y], size=[diameter,diameter], drill=diameter))# size=[0.01,0.01] 没用，还是有黄圈
    
    return x,y
    # kicad_mod.append(KicadModTree.Line(start=[x,y],end=[x,y],layer=,width=width))
    
    # kicad_mod.append(KicadModTree.Circle(center=[x,y],radius=d/2, layer='Edge.Cuts',width=0.001))	
NPH=edge_hole=non_plated_hole

def hexagon_outline(kicad_mod, x, y, flat_to_flat, angle=0, layers=glayers_silk, width=0.15):
    """
    在指定绝对坐标 (x, y) 处绘制一个对边距离为 flat_to_flat 的正六边形丝印/板边轮廓。
    包含 30 度的起始偏置，确保六边形的平边（Flat side）朝向正上方。
    
    :param kicad_mod: KiCad 封装对象
    :param x: 绝对中心坐标 X (mm)
    :param y: 绝对中心坐标 Y (mm)
    :param flat_to_flat: 正六边形平行平边之间的绝对对边距离 (mm)
    :param angle: 整体旋转角度 (度数)
    :param layers: 绘制目标层，默认为全局丝印层 glayers_silk
    :param width: 线宽 (mm)
    """
    if flat_to_flat <= 0:
        return

    # 数学转换：根据对边距离精确计算外接圆半径
    circumradius = flat_to_flat / math.sqrt(3.0)

    dots = []
    for i in range(6):
        # 计算顶点的角度 (30度偏移使平边在顶部，并叠加全局旋转 angle)
        theta = math.radians(30 + angle + i * 60)
        
        # 使用计算出的外接圆半径，求出顶点的绝对坐标
        dots.append((x + circumradius * math.cos(theta), 
                     y + circumradius * math.sin(theta)))
                     
    # 闭合多边形(添加第一个点)
    dots.append(dots[0])
    
    # 调用你的底层线段框架绘制六边形轮廓
    polyline(kicad_mod, dots, layers=layers, width=width)

# 严格保留你的别名映射
hex_outline = hexagon_outline

    
def THT_shape(kicad_mod, path_points, x=0, y=0, angle=0, slot_width=0.5, copper_annular=0.4, number=''):
    """
    使用长孔的一条边作为直线段拟合任意多边形，在内部进行 slot_width/2 的精确向内补偿。
    保证输入 path_points 严格代表最终切出来的多边形【物理内壁边缘】。
    """
    if len(path_points) < 2:
        return

    # 1. 闭合路径处理
    # 创建一份独立副本，避免修改外部传入的原始列表
    local_path = [list(pt) for pt in path_points]
    if local_path[0] != local_path[-1]:
        local_path.append(local_path[0])
        
    n = len(local_path) - 1  # 实际独立顶点的数量

    # ==========================================
    # 核心步骤：计算每个顶点向内补偿（收缩）后的精准坐标
    # ==========================================
    compensated_points = []
    half_w = slot_width / 2.0

    for i in range(n):
        # 当前顶点、上一个顶点、下一个顶点（处理闭合循环）
        curr_pt = local_path[i]
        prev_pt = local_path[(i - 1 + n) % n]
        next_pt = local_path[(i + 1) % n]

        # 计算两条相连边的方向向量
        v1x, v1y = curr_pt[0] - prev_pt[0], curr_pt[1] - prev_pt[1]
        v2x, v2y = next_pt[0] - curr_pt[0], next_pt[1] - curr_pt[1]

        # 归一化两条边的向量
        len1 = math.hypot(v1x, v1y)
        len2 = math.hypot(v2x, v2y)
        if len1 < 1e-5 or len2 < 1e-5:
            compensated_points.append(curr_pt)
            continue

        u1x, u1y = v1x / len1, v1y / len1
        u2x, u2y = v2x / len2, v2y / len2

        # 计算两条边各自的“向内”单位法向量
        # 假设多边形顶点是逆时针排列，向内法向量为：(-y, x)；如果是顺时针则会自动适配
        # 这里通过叉积方向来自动识别并保证法向量始终指向“多边形内部”
        # 我们先计算标准的左侧垂直法线
        n1x, n1y = -u1y, u1x
        n2x, n2y = -u2y, u2x

        # 验证是否指向内部：如果多边形是顺时针，颠倒法线方向
        # 判断多边形整体走向（简单通过当前顶点的局部叉积判断）
        cross_product = u1x * u2y - u1y * u2x
        if cross_product < 0:  # 顺时针情况
            n1x, n1y = u1y, -u1x
            n2x, n2y = u2y, -u2x

        # 合成拐角平分线方向（两个法向量相加）
        bisector_x = n1x + n2x
        bisector_y = n1y + n2y
        len_b = math.hypot(bisector_x, bisector_y)

        if len_b < 1e-5:
            # 180度平角或者极端锐角退化情况，直接沿着法线方向移动
            cx = curr_pt[0] + n1x * half_w
            cy = curr_pt[1] + n1y * half_w
        else:
            bisector_x /= len_b
            bisector_y /= len_b

            # 计算两条内法线夹角一半的余弦值，由此得到平分线上的拉伸系数
            cos_half_theta = n1x * bisector_x + n1y * bisector_y
            if cos_half_theta < 0.1: 
                cos_half_theta = 0.1 # 防止极端锐角除以0导致坐标飞掉
                
            # 精确计算顶点向内推送的距离
            push_dist = half_w / cos_half_theta
            cx = curr_pt[0] + bisector_x * push_dist
            cy = curr_pt[1] + bisector_y * push_dist

        compensated_points.append([cx, cy])

    # 将补偿后的点集重新闭合
    compensated_points.append(compensated_points[0])

    # ==========================================
    # 渲染步骤：基于 compensated_points 生成标准 THT 器件
    # ==========================================
    rad_g = math.radians(angle)
    thickness = slot_width + (copper_annular * 2)

    # 1. 放置所有拐角消除尖刺的【过渡圆孔】
    for i in range(len(compensated_points) - 1):
        vx_l, vy_l = compensated_points[i]
        
        # 整体旋转平移
        vx_g = vx_l * math.cos(rad_g) - vy_l * math.sin(rad_g) + x
        vy_g = vx_l * math.sin(rad_g) + vy_l * math.cos(rad_g) + y
        
        kicad_mod.append(
            Pad(
                number=number,
                type=Pad.TYPE_THT,
                shape=Pad.SHAPE_CIRCLE,
                layers=Pad.LAYERS_THT,
                at=[vx_g, vy_g],
                size=[thickness, thickness],
                drill=[slot_width, slot_width],
                rotation=0
            )
        )

    # 2. 放置所有边对应的【长条槽孔】
    for i in range(len(compensated_points) - 1):
        x1_l, y1_l = compensated_points[i]
        x2_l, y2_l = compensated_points[i+1]

        edge_len = math.hypot(x2_l - x1_l, y2_l - y1_l)
        if edge_len < 0.1:
            continue
            
        cx_l = (x1_l + x2_l) / 2.0
        cy_l = (y1_l + y2_l) / 2.0

        p4x = cx_l * math.cos(rad_g) - cy_l * math.sin(rad_g) + x
        p4y = cx_l * math.sin(rad_g) + cy_l * math.cos(rad_g) + y

        edge_angle_local = math.degrees(math.atan2(y2_l - y1_l, x2_l - x1_l))
        final_angle_deg = (edge_angle_local + angle) % 360.0

        kicad_mod.append(
            Pad(
                number=number, 
                type=Pad.TYPE_THT, 
                shape=Pad.SHAPE_OVAL, 
                layers=Pad.LAYERS_THT,
                at=[p4x, p4y], 
                size=[edge_len, thickness], # 长度精准对应缩水后的边长
                drill=[edge_len, slot_width], 
                rotation=-final_angle_deg
            )
        )
shape_tht=THT_shape

def strong_plated_hole(kicad_mod, x, y, d=3.9, size=10, cu_size=None,min_via_to_via_clearance=1, layers_cu=glayers_FB_Cu, number='1'):
    via_drill = 0.4 # 定义缝合过孔的孔径
    via_pad_size = 0.8 # 定义缝合过孔的焊盘直径
    # min_via_to_via_clearance=1 # 定义过孔钻孔边缘之间的最小安全距离
    kicad_mod.append(Pad(number=number, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, at=[x, y], size=[size, size], drill=d, layers=Pad.LAYERS_THT)) # 1. 创建中心的主通孔焊盘（这个保持默认，需要开窗）
    if not cu_size:cu_size=size
    if cu_size > size: # 2. 如果定义了额外的盖油铜皮
        kicad_mod.append(Pad(number='', type=Pad.TYPE_SMT, shape=Pad.SHAPE_CIRCLE, at=[x, y], size=[cu_size, cu_size], layers=list(layers_cu)))
    # --- 3. 动态计算并放置多圈、错开的“盖油”缝合过孔 ---
    min_center_spacing = via_pad_size + min_via_to_via_clearance # 计算两个过孔的最小中心距离
    current_radius = d / 2 + min_center_spacing # 从主孔d的边缘开始计算第一圈过孔的半径
    ring_index = 0 # 用于追踪是第几圈同心圆
    via_layers = glayers_FB_Cu # **唯一的关键修正**: 定义一个不包含Mask层的layers列表，用于实现过孔盖油
    while current_radius < (cu_size / 2 - via_pad_size / 2): # 只要还有空间容纳下一个环，就继续循环
        available_circumference = 2 * math.pi * current_radius # 计算当前半径下的可用周长
        num_vias_on_ring = int((available_circumference/min_center_spacing)*0.5) # 根据周长和间距，计算该环可容纳的最大过孔数
        if num_vias_on_ring < 3: break # 如果一个环连3个孔都放不下，就终止循环
        angle_step_deg = 360.0 / num_vias_on_ring # 根据过孔数量计算角度步进
        angle_offset_deg = (angle_step_deg / 2) if (ring_index % 2 != 0) else 0 # 如果是奇数圈，则将所有孔旋转半个步长的角度以错开
        for i in range(num_vias_on_ring): # 循环创建当前环上的所有过孔
            angle_rad = math.radians(i * angle_step_deg + angle_offset_deg) # 将偏移量加入最终角度
            via_x = x + current_radius * math.cos(angle_rad) # 计算X坐标
            via_y = y + current_radius * math.sin(angle_rad) # 计算Y坐标
            via_number = f'{number}.{ring_index}.{i}' # 分配唯一的子编号
            kicad_mod.append(Pad(number=via_number, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, at=[via_x, via_y], size=[via_pad_size, via_pad_size], drill=via_drill, layers=via_layers)) # **唯一的关键修正**: 在此处使用via_layers
        current_radius += min_center_spacing # 增加半径，准备放置下一个更外层的环
        ring_index += 1
        

def polygon_full(kicad_mod, x, y, pts, layers=['F.Cu'], angle=0):
    ''' 绘制填充多边形（支持整体旋转）
    
    参数:
        kicad_mod: KiCad 模块对象
        x, y: 旋转与平移的中心参考点
        pts: 相对中心点的顶点列表 [[dx1, dy1], [dx2, dy2], ...]
        layers: 绘图层列表
        angle: 整体旋转角度
    '''
    angle_rad = math.radians(angle)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    absolute_corners = []
    for pt in pts:
        # 1. 旋转（基于 0,0 点旋转）
        rx = pt[0] * cos_a - pt[1] * sin_a
        ry = pt[0] * sin_a + pt[1] * cos_a
        # 2. 平移（到绝对坐标 x, y）
        absolute_corners.append([x + rx, y + ry])
    
    # 绘制
    for layer in layers:
        kicad_mod.append(KicadModTree.Polygon(
            nodes=absolute_corners,
            layer=layer
        ))

        
        

def serpentine_line(kicad_mod, x, y, w, h, angle=0,wire_width=0.4, interval=0.2, layers=['F.Cu'],pop_indexes=None):
    ''' 蛇形走线  angle 0 也就是原来x方向(从左至右) ，angle越大，越往顺时针方向转动。 '''
    s = wire_width + interval
    half_w, half_h = w/2, h/2
    loops = max(1, int((w - wire_width) // (2*s)))
    step = (w - wire_width)/loops

    # 生成连续Z形路径点（相对坐标）
    points = []
    current_x = -half_w + wire_width/2
    for _ in range(loops):
        # Z形路径四关键点
        points.extend([
            (current_x, -half_h),	   # 起点
            (current_x, half_h),		# 垂直向上
            (current_x + step/2, half_h), # 斜向过渡
            (current_x + step/2, -half_h) # 垂直向下
        ])
        current_x += step

    # 添加最后水平连接段
    # points.append((current_x, -half_h))
    if pop_indexes:
        for n in pop_indexes:
            points.pop(n)

    # 生成连续走线（顺序连接所有点）
    for i in range(len(points)-1):
        # 坐标转换：相对坐标->绝对坐标->旋转
        p1 = rotate_point(points[i][0]+x, points[i][1]+y, angle, x, y)
        p2 = rotate_point(points[i+1][0]+x, points[i+1][1]+y, angle, x, y)
        
        # 添加走线段
        for layer in layers:
            kicad_mod.append(KicadModTree.Line(
                start=p1, end=p2, layer=layer, width=wire_width))

    

def draw_octagon(kicad_mod, x, y, opposite_side_distance, angle=0, width=0.01, layers=glayers_silk, **ka):
    ''' octagon 八边形  opposite_side_distance 对边距离
画一个边长48正方形，理论上应该与draw_octagon(kicad_mod,x,y,48,angle=45/2)对边重合
    '''
    import math
    # Calculate the radius of the circumscribed circle
    radius = opposite_side_distance / (2 * math.cos(math.pi / 8))

    # Convert the initial angle to radians
    angle_rad = math.radians(angle)

    # Calculate the coordinates of the vertices of the octagon
    angles = [(i * math.pi / 4 + angle_rad) for i in range(8)]
    vertices = [(x + radius * math.cos(angle), y + radius * math.sin(angle)) for angle in angles]

    # Draw the eight straight segments
    for layer in get_layers(layers, ka):
        for i in range(8):
            multi_dot_line(kicad_mod, [vertices[i], vertices[(i + 1) % 8]], width=width, layer=layer)
octagon=draw_octagon

def draw_trapezoid(kicad_mod, x, y, short_side, long_side, height, width=0.01, layers=glayers_silk, **ka):
    # Calculate the coordinates for the trapezoid
    x0 = x - short_side / 2
    y0 = y - height / 2
    # x1 = x - long_side / 2
    # y1 = y + height / 2

    # Calculate the offset for the short sides
    offset = (long_side - short_side) / 2

    # Draw the four straight segments
    for layer in get_layers(layers, ka):
        multi_dot_line(kicad_mod, [(x0, y0), (x0+short_side, y0)], width=width, layer=layer)  # Top
        multi_dot_line(kicad_mod, [(x0, y0), (x-long_side/2,y+height/2)], width=width, layer=layer)  # Right
        multi_dot_line(kicad_mod, [(x0+short_side, y0), (x+long_side/2, y+height/2)], width=width, layer=layer)  # Bottom
        multi_dot_line(kicad_mod, [(x-long_side/2,y+height/2), (x+long_side/2, y+height/2)], width=width, layer=layer)  # Left
        
trapezoid=draw_trapezoid

def rounded_rectangle(kicad_mod, x, y, w, h, radius=py.No('auto h/2'), width=0.01,layers=glayers_silk,angle=0,**ka):
    if py.isNo(radius):radius=h/2
    x0, y0 = x - w/2, y - h/2
    x1, y1 = x + w/2, y + h/2

    corners = [
        (x0 + radius, y0),
        (x1 - radius, y0),
        (x1, y0 + radius),
        (x1, y1 - radius),
        (x1 - radius, y1),
        (x0 + radius, y1),
        (x0, y1 - radius),
        (x0, y0 + radius)
    ]
    rs = [rotate_point(px,py,angle,x,y) for px, py in corners]

    arcs=[
    [x0 + radius, y0 + radius], [x0, y0 + radius],
    [x1 - radius, y0 + radius], [x1, y0 + radius],
    [x0 + radius, y1 - radius], [x0, y1 - radius],
    [x1 - radius, y1 - radius], [x1, y1 - radius],
    ]
    
    cs=[rotate_point(px,py,angle,x,y) for px, py in arcs]

    # Draw the four straight segments
    for layer in get_layers(layers,ka):
        multi_dot_line(kicad_mod, rs[0:2], width=width, layer=layer)  # Top
        multi_dot_line(kicad_mod, rs[2:4], width=width, layer=layer)  # Right
        multi_dot_line(kicad_mod, rs[4:6], width=width, layer=layer)  # Bottom
        multi_dot_line(kicad_mod, rs[6:8], width=width, layer=layer)  # Left

        # Draw the arcs for the rounded corners
        kicad_mod.append(Arc(center=cs[0], start=cs[1], angle=90 , width=width, layer=layer))  # Top-left
        kicad_mod.append(Arc(center=cs[2], start=cs[3], angle=-90, width=width, layer=layer))  # Top-right
        kicad_mod.append(Arc(center=cs[4], start=cs[5], angle=-90, width=width, layer=layer))  # Bottom-left
        kicad_mod.append(Arc(center=cs[6], start=cs[7], angle=90 , width=width, layer=layer))  # Bottom-right
    
    return


def polar_coordinate(kicad_mod, x, y,angle, distance,func=lambda x,y:non_plated_hole(kicad_mod,x=x,y=y,d=25)):
    import math
    # Convert angle to radians
    angle_rad = math.radians(angle)

    # Calculate new hole's coordinates
    new_x = x + distance * math.cos(angle_rad)
    new_y = y - distance * math.sin(angle_rad)  # subtract because y axis is flipped in KiCad

    # Create new non-plated hole
    return func(new_x,new_y)
add_new_hole=polar_coordinate
        
    
def step_motor_42(kicad_mod,x,y,angle=0,drill_screw=2.9,holes=(0,1,2,3),d=5,hole_func=non_plated_hole,circle_diameter=None,w=42,rectline_layers=glayers_F_Cu+glayers_silk):
    hole_square(kicad_mod,x,y,31,drill_screw,angle=angle,holes=holes,func=hole_func)#,func=0 force reload
    rectline_center(kicad_mod=kicad_mod,x0=x,y0=y,angle=angle,width=0.1,layers=rectline_layers,w=w)
    hole_func(kicad_mod,x,y,d)  #57
    if circle_diameter:
        circle		 (kicad_mod,x,y,crosshair=1,diameter=circle_diameter)	
    
def step_motor_57(kicad_mod,x,y,angle=0,drill_screw=3.9,holes=(0,1,2,3),d=6.35,hole_func=non_plated_hole,circle_diameter=None,w57=56.6,rectline_layers=glayers_F_Cu+glayers_silk):
    # rc_ka=dict()
    hole_square(kicad_mod,x,y,47,drill_screw,angle=angle,holes=holes,func=hole_func)#,func=0 force reload
    rectline_center(kicad_mod=kicad_mod,x0=x,y0=y,angle=angle,width=0.1,layers=rectline_layers,w=w57)
    hole_func(kicad_mod,x,y,d)  #57
    if circle_diameter:
        circle		 (kicad_mod,x,y,crosshair=1,diameter=circle_diameter)	
    
def crosshair(kicad_mod,x,y,w=0,h=0,angle=0,circle_diameter=None,**ka):
    if circle_diameter:
        circle		 (kicad_mod,x,y,crosshair=1,diameter=circle_diameter)	


    if not w:w=200
    if not h and w:h=w
    if not h:h=200
    multi_dot_line(kicad_mod,[rotate_point(x,y-h/2,angle,x,y),rotate_point(x,y+h/2,angle,x,y)],**ka)
    multi_dot_line(kicad_mod,[rotate_point(x-w/2,y,angle,x,y),rotate_point(x+w/2,y,angle,x,y)],**ka)

def edge_distance_turn(w,h,*dxys):
    for dx,dy in dxys:
        yield w-dx,h-dy # 下右
        yield dy,h-dx # 下左
        yield dx,dy  # 上左
        yield w-dy,dx # 上右

def edge_distance(w,h,*dxys):
    for dx,dy in dxys:
        yield w-dx,h-dy # 下右
        yield dx,h-dy # 下左
        yield dx,dy  # 上左
        yield w-dx,dy # 上右

def get_pcb():
    return pcbnew.GetBoard()
pcb=get_pcb	
    
def drawLine(x1, y1, x2, y2, width=1,pcb=None):
    if not pcb:pcb = pcbnew.GetBoard()

    # line = pcbnew.DRAWSEGMENT()
    line = pcbnew.PCB_SHAPE()
    line.SetStart(pcbnew.wxPoint(x1, y1))
    line.SetEnd(pcbnew.wxPoint(x2, y2))
    line.SetLayer(pcbnew.Edge_Cuts)
    line.SetWidth(pcbnew.FromMM(width))
    pcb.Add(line)
    
    return line
    
def get_draw(e,pcb=None):
    if not pcb:pcb = pcbnew.GetBoard()
        
    if py.isint(e):
        if e<999:
            return GetDrawings()[e][1]
        else:
            e=py.hex(e)[2:].upper()
    if py.istr(e):
        # return [i[1] for i in GetDrawings() if e in i[-1]]
        return [py.repr(i) for i in pcb.GetDrawings()]
        e=[i for i in pcb.GetDrawings() if e in py.repr(i)][0]
    return e	
get=get_draw	
    
def get_length_of_two_point(start,end):
    return ((end.x-start.x)**2+(end.y-start.y)**2)**0.5
    
def GetDrawings(enumerate=False,pcb=None):
    if not pcb:pcb = pcbnew.GetBoard()
    r=[]
    for n,e in py.enumerate(pcb.GetDrawings()):
        t=''
        c=e.GetClass()
        try:
            if c=='PTEXT':
                t=e.GetText()
            if c=='PCB_SHAPE':
                t=[e.ShowShape(),e.GetWidth(),get_length_of_two_point(e.GetStart(),e.GetEnd()),e.GetStart(),e.GetEnd(),]
                
        except Exception as err:
            t=py.repr(err)
        r.append([n,e,c,t])	
    return r

def get_all_footprints(pcb=None):
    if not pcb:pcb = pcbnew.GetBoard()
    r=[]
    lfps=py.list(pcb.Footprints())
    ga=[U.StrRepr(i) for i in py.dir(lfps[0]) if i.startswith('Get')]
    r.append(['No.']+ga)
    for n,a in py.enumerate(lfps):
        row=[n]
        for s in ga:
            try:
                row.append(py.getattr(a,s)())
            except Exception as e:
                row.append(e)
            
        r.append(row)
        # path=a.GetPath().AsString()
        # r.append([n,a,a.GetPosition(),a.GetPadCount(),path,a.GetFPIDAsString(),])
    return r
fps=Footprints=get_all_footprints	
    
# def set(e,t,x,y,pcb=None):
    # if not pcb:pcb = pcbnew.GetBoard()
    # e=get_draw(e,pcb=pcb)
    # M=10**6
    # if x<M:x=x*M
    # if y<M:y=y*M

    # e.SetPosition(pcbnew.wxPoint(x,y))
    # e.SetText(t)
    # return e,t,x,y

def set_footprint(f, x=0, y=0, pcb=None):
    import os, pcbnew
    IU_PER_MM = 1000000  # 内部单位转换因子
    pcb = pcb or pcbnew.GetBoard()  # 获取PCB板实例    
    # 自动处理路径逻辑
    if not f.endswith(".kicad_mod"):
        name = os.path.basename(f)  # 从路径提取文件名
        if "." in name: name = name.split(".")[0]  # 去除扩展名
        sp = os.path.dirname(f)  # 获取目录路径
        f = os.path.join(sp, name + ".kicad_mod")  # 构建完整路径
    
    # 处理路径分隔符
    f = f.replace("/", os.sep).replace("\\", os.sep)
    
    # 提取封装名称和库路径
    name = os.path.splitext(os.path.basename(f))[0]  # 不带扩展名的文件名
    sp = os.path.dirname(f)  # 封装库目录路径
    
    # 加载封装
    footprint = pcbnew.FootprintLoad(sp, name)
    if not footprint:
        raise RuntimeError(f"无法加载封装: {f}")
    
    # 设置位置（毫米转内部单位）
    position = pcbnew.VECTOR2I(int(x * IU_PER_MM), int(y * IU_PER_MM))
    footprint.SetPosition(position)
    footprint.SetReference(name)  # 使用固定标识符    
    pcb.Add(footprint)                                    
    return footprint

    
def set_fp(f=r'C:\Program Files\KiCad\6.0\share\kicad\footprints\Connector_HDMI.pretty',pcb=None):
    if not pcb:pcb = pcbnew.GetBoard()
    # p=r'C:\Program Files\KiCad\6.0\share\kicad\footprints'
    f=F.auto_path(f)
    # 
    name=T.sub_last(f,'/','.pretty')
    
    src_type=pcbnew.IO_MGR.GuessPluginTypeFromLibPath(f)# int 1
    plugin = pcbnew.IO_MGR.PluginFind(src_type)
    
    M=13*10**6
    sp='C:/Program Files/KiCad/6.0/share/kicad/footprints/Connector_Molex.pretty/'
    fs=[i for i in F.ls(sp) if i.endswith('.kicad_mod')]
    dxi={0: 0, 2: 1, 3: 2, 18: 3, 19: 4, 20: 5, 21: 6, 22: 7, 26: 8}
    for x,y in U.range2d(27,27):
        if not (17<x<21 or x in [0,2,3,21,22,26]):continue
        n=x*27+y
        f=fs[n]
        _x=x
        x=dxi[x]
        # if y not in [0,1,8,9]:continue
        if y==0:
            text(f'{_x}',x*M*4,-2*M,pcb=pcb)
        name=T.sub_last(f,'/','.kicad_mod')
        m=plugin.FootprintLoad(sp,name)
        if not m:
            return f,name
        m.SetPosition(pcbnew.wxPoint(x*M*4,y*M))#x横向右  y 纵向下
        pcb.Add(m)
        # if n==99:break
    return src_type,plugin
    
    # m = pcbnew.FootprintLoad(f,name)
    
    # return f,m
    # return m
    
def add_pad( x=0,y=0,size=2, name='', pad_type='standard', shape='circle',
            drill=1.0, layers=None,pcb=0):
    """Create a pad on the module
    Args:
        position: pad position in mm
        size: pad size in mm, value if shape == 'circle', tuple otherwise
        name: pad name/number
        pad_type: One of 'standard', 'smd', 'conn', 'hole_not_plated'
        shape: One of 'circle', 'rect', 'oval', 'trapezoid'
        drill: drill size in mm, single value for round hole, or tuple for oblong hole.
        layers: None for default, or a list of layer definitions (for example: ['F.Cu', 'F.Mask'])
    """
    if not pcb:pcb = pcbnew.GetBoard()
        
    pad = pcbnew.PAD(pcb)
    return pad
    pad.type = pad_type
    pad.shape = shape
    pad.size = size
    pad.name = name
    pad.position = position
    pad.layers = layers

    self._module.Add(pad._pad)
    return pad

def get_layers(layers,ka):
    # ['F.Cu','F.SilkS']
    layers=U.get_duplicated_kargs(ka,'layers','layer','lay',default=layers)
    # if not layers:
        # layers=ka['layer']
        # return []
    if not layers:raise py.ArgumentsError(layers)
    # else:
    if py.istr(layers):
        return [layers]
    return layers

def arc_start_end(kicad_mod, center, radius=11, start_angle=0, end_angle=90, layers='F.SilkS', width=0.01, **ka):
    """
    在KiCad封装（kicad_mod）中绘制圆弧。
    
    参数：
        kicad_mod: KiCad封装对象（如通过PyKiCad库创建的Module对象）。
        center: 圆弧中心点坐标（tuple或list，如(0, 0)）。
        radius: 圆弧半径（float，单位：毫米）。
        start_angle: 开始角度（float，范围0-360°）。 0 时 正右方  顺正逆负
        end_angle: 结束角度（float，范围0-360°）。
        layers: 圆弧所在层（str或list，如'F.SilkS'或['F.SilkS', 'B.SilkS']）。
        width: 圆弧线宽（float，单位：毫米，默认0.01mm）。
        **ka: 额外参数（如用于处理层的扩展参数）。
    返回：
        绘制的圆弧对象（Arc）。
        
    
    arc_start_end(kicad_mod,[-33,-33],22,-30,30,layers=glayers_edge_pure+glayers_silk,width=0.2)
    
    """
    # 将角度转换为弧度（三角函数需用弧度）
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    
    # 计算圆弧起点坐标（中心点 + 半径×方向向量）
    start_x = center[0] + radius * math.cos(start_rad)
    start_y = center[1] + radius * math.sin(start_rad)
    start = (start_x, start_y)
    
    total_angle = (end_angle - start_angle)
    # 处理层（复用原函数的get_layers逻辑）
    for layer in get_layers(layers, ka):
        # 创建Arc对象（KiCad要求：center=中心点，start=起点，angle=总角度）
        arc_obj = Arc(
            center=center,
            start=start,
            angle=total_angle,
            layer=layer,
            width=width
        )
        # 将圆弧添加到封装中
        kicad_mod.append(arc_obj)
    
    # 返回最后一个绘制的圆弧对象（若需批量处理，可返回列表）
    return arc_obj    
    
def arc(kicad_mod,center, start, angle, layers='F.SilkS',width=0.01,**ka):
    for layer in get_layers(layers,ka):
        arc=Arc(center=center, start=start, angle=angle, layer=layer,width=width)
        kicad_mod.append(arc)
    return arc
    
def circle_filled(kicad_mod,x,y,diameter=None,radius=None,layers=glayers_silk,lceda=True,**ka):
    ''' lceda 解析时 width=r  ,  kicad 显示 width=r*2-2 '''
    diameter=U.get_duplicated_kargs(ka,'diameter','d','D',default=diameter)
    radius=U.get_duplicated_kargs(ka,'radius','r','R',default=radius)
    lceda=U.get_duplicated_kargs(ka,'lceda','zip','z',default=radius)
    # assert not ka
    if not radius and diameter:
        if py.isnumeric(diameter):
            radius=diameter/2
        else:
            radius=[d/2 for d in diameter]

    if py.isnumeric(radius):
        radius=[radius]
    
    # if lceda:y+=4
    for r in radius:
        polygon_pts = []
        sides=36
        step_angle = 2 * math.pi / sides  # 每个顶点的角度步长（弧度）
        for i in range(sides):
            # 计算每个顶点的相对坐标
            current_angle = i * step_angle
            dx = r * math.cos(current_angle)
            dy = r * math.sin(current_angle)
            polygon_pts.append([dx, dy])
        
        # 调用polygon_full绘制填充多边形（模拟圆形）
        polygon_full(kicad_mod, x, y, polygon_pts, layers,)
        continue        
    return x,y
    
    for layer in get_layers(layers,ka):
        for r in radius:
            
            if lceda:w=r
            else:w=r*2-2
                
            kicad_mod.append(KicadModTree.Circle(center=[x,y],radius=1, layer=layer,width=r)) #2.2	
            # if crosshair:
                # kd=1
                # if py.isnum(crosshair):kd=crosshair
                # multi_dot_line(kicad_mod,[(x-kd,y-r),(x+kd,y-r)],layers=layer,width=width)
                # multi_dot_line(kicad_mod,[(x-kd,y+r),(x+kd,y+r)],layers=layer,width=width)
                # multi_dot_line(kicad_mod,[(x-r,y-kd),(x-r,y+kd)],layers=layer,width=width)
                # multi_dot_line(kicad_mod,[(x+r,y-kd),(x+r,y+kd)],layers=layer,width=width)
    return x,y            
filled_circle=circle_filled

def circle(kicad_mod,x,y,diameter=None,radius=None,width=0.01,layers=glayers_silk,crosshair=False,**ka):
    diameter=U.get_duplicated_kargs(ka,'diameter','d','D',default=diameter)
    radius=U.get_duplicated_kargs(ka,'radius','r','R',default=radius)
    
    if not radius and diameter:
        if py.isnumeric(diameter):
            radius=diameter/2
        else:
            radius=[d/2 for d in diameter]

    if py.isnumeric(radius):
        radius=[radius]
    for layer in get_layers(layers,ka):
        for r in radius:
            kicad_mod.append(KicadModTree.Circle(center=[x,y],radius=r, layer=layer,width=width))	
            if crosshair:
                kd=1
                if py.isnum(crosshair):kd=crosshair
                multi_dot_line(kicad_mod,[(x-kd,y-r),(x+kd,y-r)],layers=layer,width=width)
                multi_dot_line(kicad_mod,[(x-kd,y+r),(x+kd,y+r)],layers=layer,width=width)
                multi_dot_line(kicad_mod,[(x-r,y-kd),(x-r,y+kd)],layers=layer,width=width)
                multi_dot_line(kicad_mod,[(x+r,y-kd),(x+r,y+kd)],layers=layer,width=width)
    mr=py.max(radius)
    if crosshair:#十字准线，准星
        multi_dot_line(kicad_mod,[(x,y-mr),(x,y+mr)],layers=layers,width=width)
        multi_dot_line(kicad_mod,[(x-mr,y),(x+mr,y)],layers=layers,width=width)
    return x,y	
        
def rectline(kicad_mod,start,end,layers=None,width=0.01,**ka):
    for layer in get_layers(layers,ka):
        kicad_mod.append(RectLine(start=start,end=end, layer=layer,width=width))

def rotate_point(x, y, angle, center_x, center_y):
    ''' angle 0 也就是原来x方向(从左至右) ，angle越大，越往顺时针方向转动。 '''
    import math
    # 将角度转换为弧度
    angle_rad = math.radians(angle)

    # 将点平移到原点
    x_shifted = x - center_x
    y_shifted = y - center_y

    # 使用旋转矩阵
    x_rotated = x_shifted * math.cos(angle_rad) - y_shifted * math.sin(angle_rad)
    y_rotated = x_shifted * math.sin(angle_rad) + y_shifted * math.cos(angle_rad)

    # 将点平移回原来的位置
    x_final = x_rotated + center_x
    y_final = y_rotated + center_y

    return x_final, y_final
def centered_range(n,center=50,pitch=2.54):
    start = center - (n - 1) * pitch / 2
    return [start + i * pitch for i in range(n)]    
center_range=centered_range

def rectangle_center_all_point(x0,y0,w,h,):
    return [(x0-w/2, y0-h/2), (x0+w/2, y0-h/2), (x0+w/2, y0+h/2), (x0-w/2, y0+h/2)]
    
    
def rectline_center(kicad_mod, x0, y0, w, h=0, angle=0,crosshair=False,w_holes=None,w_holes_d=4.9,layers=glayers_silk,width=0.01,segments=0,segments_d=0.1,**ka):
    if w and not h:h=w #正方形
    points = [(x0-w/2, y0-h/2), (x0+w/2, y0-h/2), (x0+w/2, y0+h/2), (x0-w/2, y0+h/2)]
    points.append(points[0]) # 首尾衔接
    rotated_points = [rotate_point(x, y, angle, x0, y0) for x, y in points]
    
    if crosshair:
        xs=[(x0,y0-h/2),(x0,y0+h/2)]
        multi_dot_line(kicad_mod,[rotate_point(x, y, angle, x0, y0) for x, y in xs],width=width,layers=get_layers(layers,ka) )
    
        ys=[(x0-w/2,y0),(x0+w/2,y0)]
        multi_dot_line(kicad_mod,[rotate_point(x, y, angle, x0, y0) for x, y in ys],width=width,layers=get_layers(layers,ka) )
    
    if w_holes:
        x=y=0
        if py.isdict(w_holes):
            for i,d in w_holes.items():
                x=i
                y=y0
                non_plated_hole(kicad_mod,*rotate_point(x, y,angle,x0,y0),d=d)
        else:
            for i in w_holes:
                d=w_holes_d
                if py.isnumeric(i):
                    x=x0-w/2+i
                    y=y0
                elif py.isdict(i):
                    assert py.len(i)==1
                    x,d=U.get_dict_item(i)
                    # x=x0-w/2+i
                    y=y0
                elif py.len(i)==2:
                    x,y=i	
                else:
                    raise py.ArgumentUnsupported('纯数字列表代表中线，或者 (x,y) 列表',i)
                non_plated_hole(kicad_mod,*rotate_point(x, y,angle,x0,y0),d=d)
    
    # for layer in get_layers(layers, ka):
    multi_dot_line(kicad_mod,rotated_points,layers=get_layers(layers,ka),width=width)	
        
            
        # 不能用 RectLine，不支持旋转，45° 变成一段直线
        # start=[x0-w/2,y0-h/2]
        # start=rotate_point(*start,angle,x0,y0)
        # end=[x0+w/2,y0+h/2]
        # end=rotate_point(*end,angle,x0,y0)
        
        # kicad_mod.append(RectLine(start=start,end=end,layer=layer,width=width))
        # kicad_mod.append(RectLine(start=[x0-w/2,y0-h/2],end=[x0+w/2,y0+h/2],layer=layer,width=width))
        
def rectangle_vertice_start(kicad_mod,x0,y0,dx,dy,layers=(),**ka):
    for layer in get_layers(layers,ka):
        kicad_mod.append(KicadModTree.Polygon(nodes=[[x0,y0], [x0+dx,y0], [x0+dx, y0+dy], [x0,y0+dy]], layer=layer))
        
def rectangle_outline(kicad_mod,x0,y0,w,h,layers=(),width=0.01,**ka):
    # U.msgbox(repr(layers),'r')
    multi_dot_line(kicad_mod,
    [(x0,y0),(x0+w,y0),(x0+w,y0+h),(x0,y0+h),(x0,y0),],
    layers=layers,width=width)
    # for layer in get_layers(layers,ka):
        # kicad_mod.append(KicadModTree.Polygon(nodes=[[x0,y0], [x0+dx,y0], [x0+dx, y0+dy], [x0,y0+dy]], layer=layer))

def scale_points(path_points, scale_factor, center_x=0.0, center_y=0.0):
    """
    以 (center_x, center_y) 为中心，对点集合整体等比例放大或缩小。
    :param path_points: 原始点集合
    :param scale_factor: 缩放因子。> 1.0 放大，< 1.0 缩小（例如 1.1 代表放大10%，0.9 代表缩小10%）
    :param center_x, center_y: 缩放的基准中心点（如果不传，默认以局部原点 0,0 为中心）
    """
    scaled_points = []
    for px, py in path_points:
        # 先减去中心点，缩放后，再加上中心点，防止多边形发生位置漂移
        new_x = center_x + (px - center_x) * scale_factor
        new_y = center_y + (py - center_y) * scale_factor
        scaled_points.append((round(new_x, 4), round(new_y, 4)))
    return scaled_points        
        
import math
import KicadModTree

def shape_fill(kicad_mod, path_points, x=0, y=0, angle=0, scale=1.0, layers=['F.Cu']):
    """
    基于 KicadModTree.Polygon 的任意形状闭合多边形全填充函数。
    支持在局部坐标系下以 (0,0) 为中心进行等比例缩放（scale），随后进行旋转和平移刚体变换。
    
    :param kicad_mod: KiCad 封装对象
    :param path_points: 局部坐标系下的任意形状顶点列表 [[x1, y1], [x2, y2]...] (mm)
    :param x: 整体平移的目标中心 X 绝对坐标 (mm)
    :param y: 整体平移的目标中心 Y 绝对坐标 (mm)
    :param angle: 整体逆时针旋转角度 (度数)
    :param scale: 缩放因子。> 1.0 放大，< 1.0 缩小，1.0 代表不缩放
    :param layers: 需要生成填充的多层列表，默认只填充顶层铜皮 ['F.Cu']
    """
    if len(path_points) < 3:
        return

    # 将旋转角度转换为弧度
    rad_g = math.radians(angle)
    transformed_nodes = []

    # 1. 遍历所有传入的顶点，先应用等比例缩放，再应用刚体变换公式
    for pt in path_points:
        # 核心步骤一：在局部坐标系下进行等比例缩放（默认以局部原点 0,0 为中心）
        xl = pt[0] * scale
        yl = pt[1] * scale
        
        # 核心步骤二：仿射变换计算全局绝对坐标
        xg = xl * math.cos(rad_g) - yl * math.sin(rad_g) + x
        yg = xl * math.sin(rad_g) + yl * math.cos(rad_g) + y
        
        transformed_nodes.append([round(xg, 4), round(yg, 4)])

    # 2. 自动检查并闭合多边形（如果起点和终点不重合，则复制起点作为终点）
    if transformed_nodes[0] != transformed_nodes[-1]:
        transformed_nodes.append(transformed_nodes[0])

    # 3. 遍历目标层叠，严格按照你的 nodes=[...] 和 layer= 语法规则进行注入
    for layer in layers:
        kicad_mod.append(
            KicadModTree.Polygon(
                nodes=transformed_nodes, 
                layer=layer
            )
        )
arbitrary_shape_fill = fill_shape = shape_fill

        
def square(kicad_mod,x,y,side_len=100,layers=['F.Cu','F.SilkS']):
    ''' full  填充''' 
    t=side_len/2
    for layer in layers:
        kicad_mod.append(KicadModTree.Polygon(nodes=[[x+t,y+t], [x+t,y-t], [x-t,y-t], [x-t,y+t]], layer=layer))

def rectangle_full(kicad_mod, x, y, w, h=0, layers=['F.Cu'], angle=0):
    ''' 绘制填充矩形（支持旋转）
    
    参数:
        kicad_mod: KiCad模块对象
        x, y: 矩形中心坐标
        w: 矩形宽度
        h: 矩形高度
        layers: 绘图层列表（默认F.Cu）
        angle: 旋转角度（度，默认0）
    '''
    if not h:h=w
    # 计算未旋转时的四个角点（相对于中心）
    half_w = w / 2
    half_h = h / 2
    corners = [
        [half_w, half_h],    # 右下
        [half_w, -half_h],   # 右上
        [-half_w, -half_h],  # 左上
        [-half_w, half_h]    # 左下
    ]
    
    # 如果需要旋转
    if angle != 0:
        angle_rad = math.radians(angle)
        rotated_corners = []
        for corner in corners:
            # 应用旋转矩阵
            rotated_x = corner[0] * math.cos(angle_rad) - corner[1] * math.sin(angle_rad)
            rotated_y = corner[0] * math.sin(angle_rad) + corner[1] * math.cos(angle_rad)
            rotated_corners.append([rotated_x, rotated_y])
        corners = rotated_corners
    
    # 转换为绝对坐标
    absolute_corners = []
    for corner in corners:
        abs_x = x + corner[0]
        abs_y = y + corner[1]
        absolute_corners.append([abs_x, abs_y])
    
    # 绘制填充矩形
    for layer in layers:
        kicad_mod.append(KicadModTree.Polygon(
            nodes=absolute_corners,
            layer=layer
        ))
        
def polyline(kicad_mod, dots, layers=glayers_silk, width=0.12, segments=0, segments_d=0.01, **ka):#def multi_dot_line
    ''' 绘制多段线 ['*.Cu','*.Mask'] 无效，应使用 ('F.Cu',) '''
    if len(dots) < 2: raise py.ArgumentsError(dots)
    
    for layer in get_layers(layers, ka):
        for n, xy in enumerate(dots):
            if n == 0: continue
            cp = dots[n-1]
            L = distance(cp, xy)
            
            if segments:  # 分段模式
                # 计算方向向量（单位向量）
                dx, dy = (xy[0]-cp[0])/L, (xy[1]-cp[1])/L
                
                # 处理线段长度小于分段的情况（应用收缩）
                if segments >= L:
                    # 计算收缩后的起点和终点
                    start_point = (cp[0] + dx * segments_d, cp[1] + dy * segments_d)
                    end_point = (xy[0] - dx * segments_d, xy[1] - dy * segments_d)
                    
                    # 确保收缩后仍有有效线段
                    if distance(start_point, end_point) > segments_d:
                        kicad_mod.append(KicadModTree.Line(start=start_point, end=end_point, layer=layer, width=width))
                    continue
                
                # 分段绘制
                while segments < L:
                    next_point = (cp[0] + dx * segments, cp[1] + dy * segments)
                    kicad_mod.append(KicadModTree.Line(start=cp, end=next_point, layer=layer, width=width))
                    cp = (next_point[0] + dx * segments_d, next_point[1] + dy * segments_d)
                    L = distance(cp, xy)
                
                # 绘制最后一段（应用收缩）
                if L > segments_d:
                    end_point = (xy[0] - dx * segments_d, xy[1] - dy * segments_d)
                    kicad_mod.append(KicadModTree.Line(start=cp, end=end_point, layer=layer, width=width))
            else:  # 非分段模式
                kicad_mod.append(KicadModTree.Line(start=cp, end=xy, layer=layer, width=width)) #cp = dots[n-1]
                # kicad_mod.append(KicadModTree.Line(start=dots[n-1], end=xy, layer=layer,width=width)) 

multi_dot_line=polyline

def symmetric_x(kicad_mod,xys,xm,x0=0,y0=0,angle=0,xmid=0,layers=['Edge.Cuts','F.SilkS','Edge.Cuts','B.SilkS'],width=0.01):
    '''
    z=(
[0 ,0   ], [0 , 4   ], [6 , 8 ], [6 , 11], [0 , 12.1], [0 , 17.5],	
[20,17.5], [20, 12.1], [14, 11], [14, 8 ], [20, 4   ], [20, 0   ],
)

xm  xmax

以 0，0 为原点，angle +40  逆时针
    '''
    # z=[0 ,0   ], [0 , 4 ], [3.5, 6.5], [3.5, 9.4], [0 , 12.5], [0 , 17.5],
    # if not xm and xmid:
    if not x0 and xmid:
        x0=xmid-(xm/2)
    
    rz=[]
    for a,b in xys:
        rz.insert(0,[xm-a,b])	
        
    z=list(xys)+rz	
    if z[-1]!=z[0]:
        z.append(z[0]) # 封口		
        
    if angle:
        from KicadModTree.nodes import Rotation
        rot=Rotation(angle)
        zr=[]
        for x,y in z:
            d,_angle=rot.getRealPosition([x,y])
            zr.append([d['x'],d['y'],])	
        z=zr	
        
        # zr=[]
        # for x,y in rz:
            # d,_angle=rot.getRealPosition([x,y])
            # zr.append([d['x'],d['y'],])	
        # rz=zr	
        
        
        
    # z=(
# [0 ,0   ], [0 , 4   ], [6 , 8 ], [6 , 11], [0 , 12.1], [0 , 17.5],	
# [20,17.5], [20, 12.1], [14, 11], [14, 8 ], [20, 4   ], [20, 0   ],
# [0 ,0   ]
# )
    
    multi_dot_line(kicad_mod,[[i[0]+x0,i[1]+y0] for i in z],layers=layers,width=width)	
    
    # N.rpc_set(base='http://192.168.1.3:1122/',ext_cmd='print(a)',a=[z,rz])
    
    circle(kicad_mod,x0,y0,radius=1,layers=['F.SilkS','B.SilkS',])
mirror_x=symmetric_x

def edge_line(kicad_mod,dots,width=1.6,we=0.254,layer=['Edge.Cuts','Edge.Cuts','B.SilkS']):
        # wa=1.6  #  1.6 / 0.0254 = 63 mil
    # h=100-(74+wa/2)
    # kicad_mod.append(KicadModTree.Line(start=[1,h], end=[99,h],layer='Edge.Cuts',width=1.6)) 
    # kicad_mod.append(KicadModTree.Line(start=[1,h+1], end=[99,h+1],layer='Edge.Cuts',width=1.6)) 
    # kicad_mod.append(KicadModTree.Line(start=[1,h+2], end=[99,h+2],layer='Edge.Cuts',width=1.6)) 
    da=1.3
    w2=0.2
    day=(wa-we)/2
    
    # r=[]
    # for (x,y) in dots:
        # r.append([x,y+])
    
    multi_dot_line(kicad_mod,([da,h+day],
                            [da,h-day],[100-da,h-day],[100-da,h+day]),layer=layer,width=we)

def plated_hole_array(kicad_mod, x, y, pitch=2.54, n=4, angle=0,smt_pad=True,**ka):
    ''' 在指定中心点 (x,y) 处生成直线排列的过孔/焊盘阵列 '''
    d=U.get_duplicated_kargs(ka,'diameter','d','D',default=1)
    
    radian = math.radians(angle)
    cs = []
    for i in range(n):
        # 计算当前孔相对于中心点 (x, y) 的直线距离
        # (n - 1) / 2.0 可以找到阵列的绝对中心点，无论 n 是奇数还是偶数都能完美居中
        dist = (i - (n - 1) / 2.0) * pitch
        
        # 将直线距离通过三角函数分解到 X 和 Y 轴上
        hx = x + dist * math.cos(radian)
        hy = y + dist * math.sin(radian)
        
        cs.append([hx, hy])
        
        
        ka.setdefault('diameter',d)
        ka.setdefault('multiple_size',1.1)
        ka.setdefault('number',i)
        
        if smt_pad:
            if 'smt_pad_ka' not in ka:
                ka['smt_pad_ka'] = dict(size=[d,d*1.5],rotation=-angle)
                
        if 'smt_pad_ka' in ka:
            if angle and 'rotation' not in ka['smt_pad_ka']:
                ka['smt_pad_ka']['rotation']=-angle
            # kicad_mod.append(Pad(number=ka['number'],type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                # at=[hx,hy], size=[ka['diameter'],ka['diameter']*2], layers=Pad.LAYERS_THT,rotation=-angle,))
        plated_hole(kicad_mod, hx, hy,**ka)
    return cs
plated_hole_line=plated_hole_array

def plated_hole_circle(kicad_mod,x0,y0,r,d=1,n=4,angle=0,):
    ''' #TODO holes=(0,1,2,3) '''
    a=360/n
    cs=[]
    for i in range(n):
        radian = math.radians(angle+i * a)   # 将角度转换为弧度
        x=x0+ r * math.cos(radian)
        y=y0+ r * math.sin(radian)
        cs.append([x,y])
        plated_hole(kicad_mod,x,y,d,number=i)
    return cs

def non_plated_hole_circle(kicad_mod,x0,y0,n=4,D=0,r=0,d=1,angle=0,):
    ''' #TODO holes=(0,1,2,3) '''
    if D and not r:r=D/2
    a=360/n
    cs=[]
    for i in range(n):
        radian = math.radians(angle+i * a)   # 将角度转换为弧度
        x=x0+ r * math.cos(radian)
        y=y0+ r * math.sin(radian)
        cs.append([x,y])
        non_plated_hole(kicad_mod,x,y,d)
    return cs
non_plated_hole_polygon=hole_circle=non_plated_hole_circle

def non_plated_hole_square(kicad_mod,x,y,side_len_x=0,side_len_y=None,diameter=1,angle=0,holes=(0,1,2,3),func=non_plated_hole,**ka):
    ''' x,y 中心点
边长 The length of the side of a square. 	
    
3	0
2	1
'''	
    from KicadModTree.nodes import Rotation
    side_len_x=U.get_duplicated_kargs(ka,'side_len_x','w','W',default=side_len_x)
    assert side_len_x
    diameter=U.get_duplicated_kargs(ka,'diameter','d','D',default=diameter)
    side_len_y=U.get_duplicated_kargs(ka,'side_len_y','h','H',default=side_len_y)
    
    rot=Rotation(angle)
    def getr(a,b):
        d,_angle=rot.getRealPosition([a-x,b-y])
        return d['x']+x,d['y']+y
    if not holes:holes=(0,1,2,3)
    if not func:func=non_plated_hole

    if not side_len_y:side_len_y=side_len_x
    tx=side_len_x/2
    ty=side_len_y/2
    if 0 in holes:func(kicad_mod,*getr(x+tx,y+ty),diameter,**ka)
    if 1 in holes:func(kicad_mod,*getr(x+tx,y-ty),diameter,**ka)
    if 2 in holes:func(kicad_mod,*getr(x-tx,y-ty),diameter,**ka)
    if 3 in holes:func(kicad_mod,*getr(x-tx,y+ty),diameter,**ka)
hole_rect_center=hole_rect=hole_square=non_plated_hole_square
    
def plated_hole_square(*a,**ka):
    ka['func']=plated_hole
    return non_plated_hole_square(*a,**ka)

# def plated_hole(kicad_mod,x,y,diameter,multiple_size=1.01,size=0,number=None,shape=None,**ka):
    # diameter=U.get_duplicated_kargs(ka,'diameter','d','D',default=diameter)
    # if not shape:shape=Pad.SHAPE_CIRCLE                     
    # if not number:number=f'{diameter}-{x},{y}'
    # if not size:size=diameter*multiple_size
    # kicad_mod.append(Pad(number=number,type=Pad.TYPE_THT,shape=shape,layers=Pad.LAYERS_THT,
            # at=[x,y], size=[size,size], drill=diameter))
            
def plated_hole(kicad_mod, x, y, diameter, multiple_size=1.01, size=None, number=None, shape=None,smt_pad_ka=None, **ka):
    diameter = U.get_duplicated_kargs(ka, 'diameter', 'd', 'D', default=diameter)
    if not shape: shape = Pad.SHAPE_CIRCLE
    if not number: number = f'{diameter}-{x},{y}'
    
    # 处理size参数：如果未提供，则根据diameter和multiple_size计算
    if size is None:
        size = diameter * multiple_size
        # 转换为正方形焊盘尺寸
        pad_size = [size, size]
    else:
        # 如果size是单个数值，则转换为正方形
        if isinstance(size, (int, float)):
            pad_size = [size, size]
        # 如果size是元组或列表，则直接使用
        elif isinstance(size, (tuple, list)) and len(size) == 2:
            pad_size = list(size)
        else:
            raise ValueError("size must be a number or a tuple/list of two numbers")
    
    # 创建焊盘
    kicad_mod.append(Pad(
        number=number,
        type=Pad.TYPE_THT,
        shape=shape,
        layers=Pad.LAYERS_THT,
        at=[x, y],
        size=pad_size,
        drill=diameter
    ))
    
    if smt_pad_ka:
        smt_pad_ka=smt_pad_ka.copy()# 可变对象防止污染
        smt_pad_ka.setdefault('number',number)
        smt_pad_ka.setdefault('layers',Pad.LAYERS_THT)
        smt_pad_ka.setdefault('shape',Pad.SHAPE_RECT)
        smt_pad_ka.setdefault('type',Pad.TYPE_SMT)
        smt_pad_ka.setdefault('size',pad_size)
        smt_pad_ka.setdefault('drill',0.1)
        
        if 'angle' in smt_pad_ka and 'rotation' not in smt_pad_ka:
            smt_pad_ka['rotation']=smt_pad_ka.pop('angle')
        
        at_delta=smt_pad_ka.get('at_delta',[0,0])
        
        
        px,py=rotate_point(at_delta[0]+x,at_delta[1]+y,-smt_pad_ka.get('rotation',0), x, y) #正确写法
        
        smt_pad_ka.setdefault('at',(px,py) ,)
        # smt_pad_ka.setdefault('at',(x+at_delta[0],y+at_delta[1] ) ,)
        
        # U.set(2,[U.stime(),smt_pad_ka])
        kicad_mod.append(Pad(**smt_pad_ka))    #  kicad_mod.append(Pad( 的rotation是逆时针 ，和我别的代码angle约定相反
                
metal_hole=plated_hole

def plated_hole_square_vertice_start(kicad_mod,x0,y0,side_len,d,angle=0,func=plated_hole,**ka):
    from KicadModTree.nodes import Translation,Rotation
    rot=Rotation(angle)
    def getr(x,y):
        d,a=rot.getRealPosition([x-x0,y-y0])
        return d['x']+x0,d['y']+y0
    # trans = Translation(x0,y0)
    # trans.rotate(angle) 
    # x0 = trans.translateCoords((0,0))[0] 

    func(kicad_mod,*getr(x0		    ,y0		   ),d,**ka)
    func(kicad_mod,*getr(x0+side_len,y0		   ),d,**ka)
    func(kicad_mod,*getr(x0+side_len,y0+side_len),d,**ka)
    func(kicad_mod,*getr(x0		    ,y0+side_len),d,**ka)
hole_square_vertice_start=plated_hole_square_vertice_start
    
def edge(kicad_mod,start,end,width=0.8,edge=False,layers=['F.SilkS'],**ka):
    for layer in get_layers(layers, ka):
        kicad_mod.append(KicadModTree.RectLine(start=start,end=end, layer=layer))
    return
    # if not edge:
    start=U.tuple_minus(start,width-0.3)
    end=U.tuple_add(end,width-0.3)
    dd=1 # 嘉立创最小1mm ，1.8 实际 3.2，默认不启用拼版
    dx=end[0]-start[0]
    dy=end[1]-start[1]
    
    s='Edge.Cuts'
    
    kicad_mod.append(KicadModTree.Line(start=start,end=[start[0]+dx/2-dd,start[1]], layer=s,width=width)) 
    kicad_mod.append(KicadModTree.Line(			start=[start[0]+dx/2+dd,start[1]],end=[start[0]+dx,start[1]], layer=s,width=width)) 
    
    kicad_mod.append(KicadModTree.Line(start=start,end=[start[0],start[1]+dy/2-dd], layer=s,width=width)) 
    kicad_mod.append(KicadModTree.Line(			start=[start[0],start[1]+dy/2+dd],end=[start[0],start[1]+dy], layer=s,width=width)) 
    
    
    kicad_mod.append(KicadModTree.Line(start=end, end=[end[0]-dx/2+dd,end[1]],layer=s,width=width)) 
    kicad_mod.append(KicadModTree.Line(			start=[end[0]-dx/2-dd,end[1]],end=[end[0]-dx,end[1]], layer=s,width=width)) 
    
    
    kicad_mod.append(KicadModTree.Line(start=end, end=[end[0],end[1]-dy/2+dd],layer=s,width=width)) 
    kicad_mod.append(KicadModTree.Line(			start=[end[0],end[1]-dy/2-dd], end=[end[0],end[1]-dy], layer=s,width=width)) 

def netbox_edge(unit=0.6,cm=10,layers=['F.SilkS','B.SilkS']):
    name=fr'netbox_edge-{unit}'+T.join(range(cm),separator='  ')
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8+cm,5+cm])  #没有这句 lceda 导入错误
    drect=dict(start=[0,0], end=[10*cm+0.05,10*cm+0.05])
    kicad_mod.append(RectLine(**drect, layer='F.SilkS'))
    kicad_mod.append(RectLine(**drect, layer='B.SilkS'))
    
    for i in range(100):
        iu=unit
        if i%cm==0:
            iu=unit*3
            # multi_dot_line(kicad_mod,layer=layers,width=0.1,dots=([0,i],[unit*,i]))
        elif i%(cm//2)==0:
            iu=unit*2
    
        multi_dot_line(kicad_mod,layer=layers,width=0.1,dots=([0,i],[iu,i]))
        multi_dot_line(kicad_mod,layer=layers,width=0.1,dots=([100,i],[100-iu,i]))
        
        multi_dot_line(kicad_mod,layer=layers,width=0.1,dots=([i,0],[i,iu]))
        multi_dot_line(kicad_mod,layer=layers,width=0.1,dots=([i,100],[i,100-iu]))
                
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname
def netbox(kicad_mod=None,unit=1,cm=3,layers=['F.SilkS','B.SilkS']):
    name=fr'net-'+T.join(range(cm),separator='  ')
    if not kicad_mod:
        kicad_mod = new_kicad_mod(name,w=0)
    
    drect=dict(start=[0,0], end=[10*cm+0.05,10*cm+0.05])
    kicad_mod.append(RectLine(**drect, layer='F.Cu'))
    kicad_mod.append(RectLine(**drect, layer='B.Cu'))
    kicad_mod.append(RectLine(**drect, layer='F.SilkS'))
    kicad_mod.append(RectLine(**drect, layer='B.SilkS'))
    # for x,y in range(10):
    for x,y in U.iter2d_start_end(start=[0,0],end=[cm,cm]):
        x=x*10
        y=y*10
        for i in range(10):
            if i==0:
                multi_dot_line(kicad_mod,layer=layers,width=0.1,dots=([x+i,y+0],[x+i,y+10]))	
                multi_dot_line(kicad_mod,layer=layers,width=0.1,dots=([x+0,y+i],[x+10,y+i]))	
                continue
            ij=[x+i,y+0]
            k=3
            # d=(i+k)%16#-(i+k)/10
            d=((i+5)%10)+1
            # multi_dot_line(kicad_mod,layer=['F.SilkS','B.SilkS'],width=0.1,dots=([ij[1],ij[0]],[max(x+i-d/7,x-0.15),y+ij[1]]))	
            ts=[]
            jm=-0.1*100
            j0=jm
            for n,j in enumerate(range(0,1000,d)):
                # if n%2==1:continue
                if n%(20)!=0:
                    if j0!=jm:
                        j0=j
                    continue
                # ts.append([x+i,y+j/100])
                multi_dot_line(kicad_mod,layer=layers,width=0.1,dots=([x+i,y+j0/100],[x+i,y+j/100]))	
                multi_dot_line(kicad_mod,layer=layers,width=0.1,dots=([x+j0/100,y+i],[x+j/100,y+i]))	
                j0=j
                # ij=[x+i,y+j]
        # for y in range(0,100,d+1):
            # if y==0:continue
            # multi_dot_line(kicad_mod,layer=['F.SilkS','B.SilkS'],width=0.1,dots=(xy,[x,y-d/2]))	
            # multi_dot_line(kicad_mod,layer=['F.SilkS','B.SilkS'],width=0.1,dots=([xy[1],xy[0]],[y-d/2,x]))	
            #### if x==9:print(x,y,xy)
            # xy=x,y
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname
    
def lqfp_48(drill_screw=0.90,mn=12,w=7,D=0.8,Dd=0):
    name=fr'LQFP{mn*4}-{drill_screw}-w{w}-D{D}-{Dd}--'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8,-2-9])  #没有这句 lceda 导入错误
    
    x0=-3.5
    y0=3.5
    size=[0.1,2]
    pins=[
'VBAT','PC13','PC14','PC15','OSCIN','OSCOUT','NRST','VSSA'	 ,'VDDA','PA0' ,'PA1'  ,'PA2'  ,
'PA3' ,'PA4' ,'PA5' ,'PA6' ,'PA7'  ,'PB0'   ,'PB1' ,'PB2/BOOT1','PB10','PB11','VSS_1','VDD_1',
'PB12','PB13','PB14','PB15','PA8'  ,'PA9'   ,'PA10','PA11'	 ,'PA12','PA13','PF6'  ,'PF7'  ,
'PA14','PA15','PB3' ,'PB4' ,'PB5'  ,'PB6'   ,'PB7' ,'BOOT0'	,'PB8' ,'PB9' ,'VSS_3','VDD_3',
]	
    pins+=['']*(mn*4-48)
    t=(w-(mn-1)*0.5)/2
    k=size[1]/2
    dm254=((2.54-0.5)*(mn-1) )/2
    k254=((mn+1)*2.54)/2
    
    kicad_mod.append(RectLine(start=[x0,y0],end=[x0+w,y0-w], layer='F.SilkS'))
    edge(kicad_mod,start=[-k254-2,-k254-2],end=[k254+2,k254+2])
    # kicad_mod.append(Line(start=[x0,y0],end=[x0,y0],width=1,layer='F.Cu'))
    # kicad_mod.append(Line(start=[x0,y0-7],end=[x0,y0-7],width=1,layer='F.Cu'))
    dp=D/2-Dd
    plated_hole(kicad_mod,x0-dp  ,y0+dp,D)
    plated_hole(kicad_mod,x0+w+dp,y0+dp,D)
    plated_hole(kicad_mod,x0-dp  ,y0-w-dp,D)
    plated_hole(kicad_mod,x0+w+dp,y0-w-dp,D)
    
    for n in range(mn):
        # a=
        # kicad_mod.append(KicadModTree.Line(start=, end=[x4+2.54*2, y0+4*2.54], layer='B.Cu',width=0.12)) #EN
        
        kicad_mod.append(Pad(number=pins[n],type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x0+t+0.5*n, y0+k], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
        kicad_mod.append(Pad(number=pins[12+n],type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x0+w+k	  , y0-t-0.5*n], size=[size[1],size[0]], drill=drill_screw, layers=Pad.LAYERS_THT))
        kicad_mod.append(Pad(number=pins[24+n],type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x0+w-t-0.5*n, y0-w-k], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
        kicad_mod.append(Pad(number=pins[36+n],type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x0-k		,y0-w+t+0.5*n], size=[size[1],size[0]], drill=drill_screw, layers=Pad.LAYERS_THT))

        # 2.54 插针
        kicad_mod.append(Pad(number=pins[n],type=Pad.TYPE_THT,shape=Pad.SHAPE_RECT,layers=Pad.LAYERS_THT,
                at=[x0+t-dm254+2.54*n,k254], size=[drill_screw,drill_screw*2], drill=drill_screw))
        kicad_mod.append(Pad(number=pins[12+n],type=Pad.TYPE_THT,shape=Pad.SHAPE_RECT,layers=Pad.LAYERS_THT,
                at=[k254  			 ,y0-t+dm254-2.54*n], size=[drill_screw*2,drill_screw], drill=drill_screw))		
        kicad_mod.append(Pad(number=pins[24+n],type=Pad.TYPE_THT,shape=Pad.SHAPE_RECT,layers=Pad.LAYERS_THT,
                at=[x0+w-t+dm254-2.54*n,-k254], size=[drill_screw,drill_screw*2], drill=drill_screw))		
        kicad_mod.append(Pad(number=pins[36+n],type=Pad.TYPE_THT,shape=Pad.SHAPE_RECT,layers=Pad.LAYERS_THT,
                at=[-k254 			  ,y0-w+t-dm254+2.54*n], size=[drill_screw*2,drill_screw], drill=drill_screw))		
        # 连线
        mka=py.dict(kicad_mod=kicad_mod,width=0.2,layer=['F.Cu','B.Cu',])
        multi_dot_line(dots=([x0+t+0.5*n  ,y0+k*2]		,[x0+t-dm254+2.54*n  ,k254],),**mka)
        multi_dot_line(dots=([x0+w+k*2	  ,y0-t-0.5*n]  ,[k254  			 ,y0-t+dm254-2.54*n],),**mka)
        multi_dot_line(dots=([x0+w-t-0.5*n,y0-w-k*2]	,[x0+w-t+dm254-2.54*n,-k254],),**mka)
        multi_dot_line(dots=([x0-k*2	  ,y0-w+t+0.5*n],[-k254 			 ,y0-w+t-dm254+2.54*n],),**mka)
    
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname
qfp=lqfp_48	
    
def sopN(drill_screw=0.90,mn=4,pin_split='-split',D=0.8):
    name=fr'sop{mn*2}{pin_split}-{drill_screw}-D{D}--'
    kicad_mod=new_kicad_mod(name=name)
    
    
    x0=2.54*(3+2)-1
    y0=0
    
    drect=dict(start=[-2.54*2+1,-2.54*2], end=[x0+2.54*3+1,2.54*4])
    edge(kicad_mod,**drect)
    
    db=5
    yb=y0+db
    xw=-3
    yw=-0.8
    
    size=[0.12,2.3]
    s254=[drill_screw,drill_screw*2]
    
    pins=[
[5,6,7,8],
[1,2,3,'4 GND'],
    ]
    for n in range(mn):
        a,b=U.tuple_operator(U.get_2D_list_column(pins,n),operator=py.str)
        ax254=0+2.54*n-((2.54*(mn-1))-(1.27*(mn-1)))/2
        db0=(2.54*3-db)/2
        at254=[ax254,y0-db0-drill_screw]
        bt254=[ax254,yb+db0+drill_screw]
        
        kicad_mod.append(Pad(number=a,type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x0+1.27*n, y0-0.5], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
        kicad_mod.append(Pad(number=a,type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=at254, size=s254, drill=drill_screw, layers=Pad.LAYERS_THT))		
        multi_dot_line(kicad_mod,layer=['F.Cu','B.Cu'],width=0.1,
#		0		1					   2						3
dots=(at254,[ax254,y0+yw+0.2*n],[xw-0.2*n,y0+yw+0.2*n],[xw-0.2*n,y0-4-0.2*n],[xw-0.2*n,y0-4-0.2*n],[xw-0.2*n,y0-4-0.2*n],[x0+1.27*n,y0-4-0.2*n],[x0+1.27*n,y0-1],))


        kicad_mod.append(Pad(number=a,type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
                at=[ax254,y0-db0], size=[drill_screw,drill_screw+0.1], drill=drill_screw, layers=Pad.LAYERS_THT))		
                
        
        
        kicad_mod.append(Pad(number=b,type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x0+1.27*n, yb+0.5], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
        kicad_mod.append(Pad(number=b,type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=bt254, size=s254, drill=drill_screw, layers=Pad.LAYERS_THT))		
        multi_dot_line(kicad_mod,layer=['F.Cu','B.Cu'],width=0.1,
####		0		1					   2						3
dots=(bt254,[ax254,yb-yw-0.2*n],[xw-0.2*n,yb-yw-0.2*n],[xw-0.2*n,yb+4+0.2*n],[xw-0.2*n,yb+4+0.2*n],[xw-0.2*n,yb+4+0.2*n],[x0+1.27*n,yb+4+0.2*n],[x0+1.27*n,yb+1],))
        
        
        kicad_mod.append(Pad(number=b,type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
                at=[ax254,yb+db0], size=[drill_screw,drill_screw+0.1], drill=drill_screw, layers=Pad.LAYERS_THT))		
                
        if (n+1)!=mn:
            xms=x0+1.27*n+1.27/2
            multi_dot_line(kicad_mod,layer=['F.Cu','B.Cu','F.SilkS','B.SilkS'],width=0.12,
dots=([xms,y0-1.3],[xms,y0+0.7]))	
            multi_dot_line(kicad_mod,layer=['F.Cu','B.Cu','F.SilkS','B.SilkS'],width=0.12,
dots=([xms,yb+1.3],[xms,yb-0.7]))	
        
    xp=x0-0.6	
    kicad_mod.append(RectLine(start=[xp,y0],end=[xp+5,y0+5], layer='F.SilkS'))
    
    # D=0.9
    dp=D/2
    plated_hole(kicad_mod,xp-dp  ,y0-dp,D)
    plated_hole(kicad_mod,xp+5+dp,y0-dp,D)
    plated_hole(kicad_mod,xp-dp  ,y0+5+dp,D)
    plated_hole(kicad_mod,xp+5+dp,y0+5+dp,D)
    # kicad_mod.append(Circle(center=[x0, 0], radius=0.4, layer='Edge.Cuts'))
    
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname
sop8=sopN	
    
def pin_28_2mm(drill_screw=0.85,pin_split='-split',zip=0):
    name=fr'{pin_28_2mm.__name__}{pin_split}-{drill_screw}'
    if zip:name+=f'-{U.stime()}'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[11,4])  #没有这句 lceda 导入错误
    edge(kicad_mod,start=[0,0],end=[100,100])
    
    pins=[
[1	 ,2	 ,3	 ,4	 ,5	 ,6	 ,7	 ,8	 ,9	 ,0	 ,1	 ,2	 ,3	 ,4	],
['3LED','3TX+','3TX-','1TX+','1TX-','RST' ,'2LED','1LED','GND' ,'WLED','WRX+','WRX-','GND' ,'3v3'],	
['GND' ,'3RX-','3RX+','1RX-','1RX+','2RX-','2RX+','2TX-','2TX+','GND' ,'WTX-','WTX+','GND' ,'3v3'],
]

    x,y=24,2
    # x0=y0=0
    dx,dy=-0.1,-0.2
    x0,y0=41+dx,33+dy
    
    x0,y0=x+40.9,y+32.8
    
    size=[drill_screw,drill_screw]
    sdyd=U.tuple_multiply(size,1.4)
    s254=[drill_screw,drill_screw*2]
    msd=1.4
    mmdx=0.8
    mmdy=0.7
    incu=[
    # 'F.SilkS',
    'B.Cu',
    # 'In1.Cu', #黄色
    # 'In2.Cu',#封装编辑器里layers无法选择，只显示铜层可以看见紫色
    ]
    fbcu=['F.Cu',
    # 'F.SilkS','B.SilkS'
    ]
    cut_layer='Edge.Cuts','F.SilkS','B.SilkS','Edge.Cuts'
    
    for n in range(14):
        _n,a,b=U.get_2D_list_column(pins,n)
        yb=y0+2*1		
        ax254=x0+2.54*n-3.78
        at254=[ax254,y0-4]
        bt254=[ax254,yb+4]
        
        kicad_mod.append(Pad(number=a,type=Pad.TYPE_THT,shape=Pad.SHAPE_RECT,
                at=[x0+2*n, y0], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
        kicad_mod.append(Pad(number=a,type=Pad.TYPE_SMT,shape=Pad.SHAPE_RECT,
                at=[x0+2*n, y0-drill_screw+0.05], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
        kicad_mod.append(Pad(number=a,type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                at=at254, size=s254, drill=drill_screw+0.05, layers=Pad.LAYERS_THT))
        multi_dot_line(kicad_mod,layers=fbcu,width=0.12,
dots=([x0+2*n,y0],[x0+2*n,y0+mmdy],[x0+2*n+mmdx,y0+mmdy],[x0+2*n+mmdx,y0-msd],at254))	
        if a[-1] in ['-','+']:
            ya_=bt254[1]+2.54
            multi_dot_line(kicad_mod,layers=incu,width=0.12,
dots=([x0+2*n,y0],[x0+2*n-mmdx,y0],[x0+2*n-mmdx,yb+msd],[ax254+1.27,yb+3],[ax254+1.27,ya_],[ax254,ya_],))	# 外连接线
            kicad_mod.append(Pad(number=a,type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                at=[ax254,ya_], size=sdyd, drill=drill_screw, layers=Pad.LAYERS_THT))	
        ############################################
        kicad_mod.append(Pad(number=b,type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                at=[x0+2*n, yb], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
        kicad_mod.append(Pad(number=b,type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x0+2*n, yb+drill_screw-0.05], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
        
        if b[-1] in ['-','+'] and b[0] in ['1','3']:s254_b=sdyd
        else:s254_b=s254
        kicad_mod.append(Pad(number=b,type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                at=bt254, size=s254_b, drill=drill_screw+0.05, layers=Pad.LAYERS_THT))
        multi_dot_line(kicad_mod,layers=fbcu,width=0.12,
dots=([x0+2*n,yb],[x0+2*n,yb-mmdy],[x0+2*n+mmdx,yb-mmdy],[x0+2*n+mmdx,yb+msd],bt254))		 # 内下
        
    
    
    rectangle_outline(kicad_mod, x + 48.2, y+22.2, 11, 5.5, layers=cut_layer)  # 网卡直出 中  横

    plated_hole(kicad_mod, x + 76.4, y + 33.8, 6)  # 固定柱

    plated_hole(kicad_mod, x + 13.75, y + 46.7, 6.8)  # 左电容
    plated_hole(kicad_mod, x + 4.1, y + 71.0, 6)  # 左电容 下小
    plated_hole(kicad_mod, x + 82.0, y + 5.8, 6)  # 右电容 上小
    plated_hole(kicad_mod, x + 86.8, y + 52.6, 7)  # 右电容

    # rectangle_outline(kicad_mod, x + 24.3, y + 0, 32.3, 1.3, layers=cut_layer)  # 顶边 铁网口
    rectline_center(kicad_mod, x + 40.45, y-7, 32.3, 16, layers=cut_layer)  # 顶边 铁网口

    rectangle_outline(kicad_mod, x + 30.7, y + 4.4, 7, 13, layers=cut_layer)  # 网2.0mm-4 左 竖

    rectangle_outline(kicad_mod, x + 57.9, y -0.5, 19, 17, layers=glayers_Cmts)  # 射频
    rectline_center(kicad_mod, x+57.9+9.5, y+3, w=19, h=27, width=0.01,layers=cut_layer)  # 射频
    

    rectangle_outline(kicad_mod, x + 0, y + 37.2, 7, 23.5, layers=cut_layer)  # cpu 散热
    rectline_center(kicad_mod, x - 4.8, y + 48.95, w=23.5, h=23.5, width=0.01, layers=cut_layer)  # cpu 散热
    
    rectline_center(kicad_mod, x - 12.2, y + 48.95+35.7, w=6.5, h=13.5, width=0.01, layers=cut_layer) # 串口
    
    rectline_center(kicad_mod, x +61, y + 83, w=7.5, h=7.5, width=0.01, layers=cut_layer) # 右下电感
    

    rectangle_outline(kicad_mod, x + 91.4, y + 11.3, 9, 15, layers=cut_layer)  # USB 1
    rectangle_outline(kicad_mod, x + 91.4, y + 36.9, 9, 15, layers=cut_layer)  # USB 1
    rectangle_outline(kicad_mod, x + 91.4, y + 62.4, 9, 15, layers=cut_layer)  # USB 1
        
    
    
    return write_kicad_mod(kicad_mod,zip=zip)

def stepper_driver(kicad_mod=None,drill_screw=0.95,x0=0,y0=0):
    '''
'In1.Cu'
'''	
    if kicad_mod:
        new_footprint=False
    else:
        new_footprint=True
        
    if new_footprint:
        name=f'{stepper_driver.__name__}-{drill_screw}--'
        kicad_mod = Footprint(name)
        kicad_mod.setDescription(name)
        kicad_mod.append(KicadModTree.Text(type='reference', text=name,at=[7,3],size=[1,1],layer='F.SilkS')) #没有这句 lceda 导入错误	

    pins=[
['0'   ,'1GND','2'   ,'3'   ,'4'   ,'5'   ,'6'   ,'7GND'],
['0_EN','1'   ,'2'   ,'3'   ,'4'   ,'5'   ,'6STP','7DIR'],
]

    if kicad_mod:
        for n in range(8):
            size=[drill_screw+0.1,drill_screw*2]
            a,b=U.get_2D_list_column(pins,n)
            if len(a)>1:
                kicad_mod.append(Pad(number=a,type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                at=[x0+n*2.54, y0+0*2.54], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
            if len(b)>1:
                kicad_mod.append(Pad(number=b,type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                at=[x0+n*2.54, y0+5*2.54], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
                
        x4=x0+2*2.54
        y4=y0+4*2.54
        for n,i in enumerate(['STP','DIR','EN','GND']):
            if i=='GND':shape=Pad.SHAPE_RECT
            else:shape=Pad.SHAPE_CIRCLE
        
            kicad_mod.append(Pad(number=i,type=Pad.TYPE_THT, shape=shape,
                at=[x4+2.54*n, y4], size=[1.25,1.25], drill=drill_screw, layers=Pad.LAYERS_THT))
        
        
        # kicad_mod.append(KicadModTree.Line(start=, end=[x4+2.54*2, y0+4*2.54], layer='B.Cu',width=0.12)) #EN
        
        ym=y4+1.27
        
        multi_dot_line(kicad_mod,layer='B.Cu',width=0.12,
dots=([x0+0*2.54,y0+5*2.54],[x4+2.54*2, ym],[x4+2.54*2,y4])) #EN
        
        multi_dot_line(kicad_mod,layer='F.Cu',width=0.12,
dots=([x0+6*2.54,y0+5*2.54],[x4+2.54*0,y0+5*2.54],[x4+2.54*0,y4])) #STP
        
        multi_dot_line(kicad_mod,layer='F.Cu',width=0.12, #DIR
dots=([x0+7*2.54,y0+5*2.54],[x0+7*2.54,ym],[x4+2.54*1,ym],[x4+2.54*1, y4]))
        
        multi_dot_line(kicad_mod,layer='F.Cu',width=0.12, #GND
dots=([x0+1*2.54,y0],[x4+2.54*3, y4],[x0+7*2.54,y0],))
        
        # kicad_mod.append(KicadModTree.Line(layer='B.Cu',width=0.12,
        # start=,end=,)) #EN
    
    if new_footprint:				
        file_handler = KicadFileHandler(kicad_mod)
        fname=f'{T.file_legalized(name)}.kicad_mod'
        file_handler.writeFile(fname)
        return kicad_mod,fname
    
def cnc_shield(drill_screw=0.95,bias=1.8):
    name=fr'{cnc_shield.__name__} {bias}-{drill_screw}--'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[3,-1])  #没有这句 lceda 导入错误
    
    dx=2.54+bias
    
    
    drect=dict(start=[0,0], end=[16*2.54+dx,14*2.54])
    kicad_mod.append(RectLine(**drect, layer='F.SilkS'))
    kicad_mod.append(RectLine(**drect, layer='B.SilkS'))
    
    stepper_driver(kicad_mod,drill_screw,0,0)
    stepper_driver(kicad_mod,drill_screw,8*2.54+dx,0)
    stepper_driver(kicad_mod,drill_screw,0,(6+2)*2.54)
    stepper_driver(kicad_mod,drill_screw,8*2.54+dx,(6+2)*2.54)
    
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname
    
def ramps_5(drill_screw=0.95,bias=0.9):
    name=fr'{ramps_5.__name__} S.D.E.G {bias}-{drill_screw}--'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[3,-1])  #没有这句 lceda 导入错误
    # kicad_mod.append(KicadModTree.Text(type='reference', text=name,at=[3,-1],size=[1,1],layer='F.SilkS'))
    s=1.4
    # kicad_mod.append(KicadModTree.Text(type='value', text="===", at=[-3,50],size=[s,s],layer='B.Cu'))
    
    stepper_driver(kicad_mod,drill_screw,0*2.54,0)
    stepper_driver(kicad_mod,drill_screw,8*2.54+bias,0)
    
    y3=(6+3)*2.54
    stepper_driver(kicad_mod,drill_screw,0*2.54 ,y3)
    stepper_driver(kicad_mod,drill_screw,8*2.54 ,y3)
    stepper_driver(kicad_mod,drill_screw,16*2.54,y3)
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname


    name=f'{ramps_5.__name__}-{drill_screw}--'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    kicad_mod.append(KicadModTree.Text(type='reference', text=name,at=[7,3],size=[1,1],layer='F.SilkS')) #只有这句 lceda 导入错误，参见 km_text
    
    
    stepper_driver(kicad_mod,drill_screw,0*2.54,0)
    stepper_driver(kicad_mod,drill_screw,8*2.54+0.9,0)
    
    y3=(6+3)*2.54
    stepper_driver(kicad_mod,drill_screw,0*2.54 ,y3)
    stepper_driver(kicad_mod,drill_screw,8*2.54 ,y3)
    stepper_driver(kicad_mod,drill_screw,16*2.54,y3)

    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname
    
def footprint_wire(w=1,interval=0.127,max=100,silk_line=True,drill_screw=0.95):
    name=fr'Bed {w}-{interval}-{drill_screw}-{max}--'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    # km_text(kicad_mod,name,at=[-3,2]) 
    kicad_mod.append(KicadModTree.Text(type='reference', text=name,at=[3,-1],size=[1,1],layer='F.SilkS'))
    s=1.4
    kicad_mod.append(KicadModTree.Text(type='value', text="==="
    , at=[-3,50],size=[s,s],layer='B.Cu'))
    
    # stepper_driver(kicad_mod,drill_screw,0*2.54,0)#test
    # file_handler = KicadFileHandler(kicad_mod)
    # fname=f'{T.file_legalized(name)}.kicad_mod'
    # file_handler.writeFile(fname)
    # return kicad_mod,fname,[0]	
    #################################################
    
    drect=dict(start=[0,0], end=[max,max])
    kicad_mod.append(RectLine(**drect, layer='F.SilkS'))
    kicad_mod.append(RectLine(**drect, layer='B.SilkS'))
    # kicad_mod.append(KicadModTree.Line(start=z0, end=z, layer='F.Cu',width=w))
    # max=0
    
    r=[]
    # while r< max:
    
    d=w+interval
    M=py.int(max/(2*d))-1
    # d=w
    # x0=d*2
    # x0=w
    x0=y0=(max-((M+1)*2*d-interval))/2+ w/2
    # x0=y0=0
    y_mid=50
    
    zrow=(	[x0,y0],[max-x0,y0],	# 0   1
                    [max-x0,y0+d],	# 3   2
            [x0,y0+d],				# 4
            [x0,y0+d+d],)		# 
    for i in range(M+1,):
        # kicad_mod.append(KicadModTree.Text(type='value', text=f'{i}', at=[-3,M*2*d],size=[1,1],layer='F.SilkS'))
        
        z0=None
        for n,z in py.enumerate(zrow):
            z=U.deepcopy(z)
            # if i in (0,M):
            if (i==0 and n==0) or (i==M and n==3):
                z[0]+=interval*2
                
            # 斜
            ipad=d*3
            if i==0 and n in (3,4):
                z[0]+=ipad
            if i==1 and n in (0,):
                z[0]+=ipad
                
            if i in (0,M) and n in (1,2): # 螺丝
                z[0]-=d*2
            if i in (M//2,) and n in (3,4): # 螺丝 21 M=43 
                z[0]+=d*2
                if n==4:
                    y_mid=z0[1]+(d/2)
                    print('i,n,=',i,n,'z0,z=',z0,z)
            if i in (M//2+1,) and n in (0,): # 螺丝 22  
                z[0]+=d*2
                # print('i,n,=',i,n,'z0,z=',z0,z)
            # 斜	
            if i==M-1 and n in (3,4):
                z[0]+=ipad
            if i==M and n==0:
                z[0]+=ipad  
            
            
            if i==M and n==4:break
            
            z[1]+=i*d*2
            if n!=0:
                kicad_mod.append(KicadModTree.Line(start=z0, end=z, layer='F.Cu',width=w))
                zs0,zs=z0.copy(),z.copy()
                if n in (1,3) and silk_line:
                    # assert zs0[1]==zs[1]
                    sw_interval=interval-0.01
                    zs0[1]=zs[1]=zs[1]-d/2
                    dxs=w/2+0.06
                    
                    if n==1:
                        zs0[0]+=dxs
                        zs[0]=max
                        if i==0:zs0[0]=0
                    if n==3:
                        zs0[0]-=dxs
                        zs[0]=0
                        if i==M:zs0[0]=max
                    
                    kicad_mod.append(KicadModTree.Line(start=zs0, end=zs, layer='F.SilkS',width=sw_interval))
            z0=z
            # r.append(z)
            
            
    dp=x0-(w/2)
    
    # scale=1.4*(w**(0.4))
    # if w<0.6:scale=1.3
    # else	:scale=1.4
    scale = 1.958271 + (1.34199 - 1.958271)/(1 + (w/2.630715)**5.311663)
    
    xp=(x0+3*d-w/2)/2
    yp=(y0+3*d-w/2)/2
    # yp=d*1.5+dp-interval
    sizep=[scale*xp,scale*yp]
    xp+=w/3
    yp+=w/3
    
    
    kicad_mod.append(Pad(number='', type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,at=[xp,yp], size=sizep, drill=0, layers=['F.Cu','*.Mask',]))			
    kicad_mod.append(Pad(number='', type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,at=[xp,max-yp], size=sizep, drill=0, layers=['F.Cu','*.Mask',]))					
    
    zp0,zp1=[x0+d+w,y0+d*2],[x0+d*2,y0]
    zp0,zp1=[x0+d,y0+d+interval*2],[x0+d*2.88,y0]
    kicad_mod.append(KicadModTree.Line(start=zp0, end=zp1, layer='F.Cu',width=w*0.8))
    
    kicad_mod.append(KicadModTree.Line(start=[x0+d,max-(y0+d+interval*2)], end=[x0+d*2.88,max-(y0)], layer='F.Cu',width=w*0.8))
    
    ########
    dd=(x0+w+interval)*0.65
    kicad_mod.append(Pad(number='', type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,at=[max-dd,dd], size=[0.1,0.1], drill=drill_screw, layers=Pad.LAYERS_THT))	# 螺丝		
    kicad_mod.append(Pad(number='', type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,at=[max-dd,max-dd], size=[0.1,0.1], drill=drill_screw, layers=Pad.LAYERS_THT))		
    
    kicad_mod.append(Pad(number='', type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,at=[dd,y_mid], size=[0.1,0.1], drill=drill_screw, layers=Pad.LAYERS_THT))			
    
    
            
            
    print('M=',U.set(w,M),)		
    # r=zrow	
    # pg=KicadModTree.PolygoneLine(polygone=r,width=w, layer='F.Cu')
    # kicad_mod.append(pg)
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    
    F.replace(U.pwd()+fname,'===',r'"0--\n1--\n2--\n3--\n4--\n5--\n6--\n7--\n8--\n9--\n10--\n11--\n12--\n13--\n14--\n15--\n16--\n17--\n18--\n19--\n20--\n21--\n22--\n23--\n24--\n25--\n26--\n27--\n28--\n29--\n30--\n31--\n32--\n33--\n34--\n35--\n36--\n37--\n38--\n39--\n40--\n41--\n42--\n43--"')
    return kicad_mod,fname,[scale,xp,yp,M]
    
    
def km_text(kicad_mod,t,at=[6,6],size=[1,1]):
    kicad_mod.append(KicadModTree.Text(type='reference', text=t, at=at,size=size,layer='F.SilkS'))
    # kicad_mod.append(KicadModTree.Text(type='reference', text=t, at=at,size=size,layer='B.SilkS'))#lceda 不能有两个 reference  导入错误
    # kicad_mod.append(KicadModTree.Text(type='value', text='vf '+t, at=at,size=size,layer='F.SilkS'))
    # kicad_mod.append(KicadModTree.Text(type='value', text='vb '+t, at=at,size=size,layer='B.SilkS'))
    # at[1]+=5
    # kicad_mod.append(KicadModTree.Text(type='value', text=t, at=at,size=size,layer='F.Cu')) 
    kicad_mod.append(KicadModTree.Text(type='value', text=t, at=at,size=size,layer='B.Cu'))
    
def new_footprint_holes(start=0.25,end=5.9,step=0.01,delta=0.3):
    import numpy
    name=fr'{start}-{end},{step} holes  '
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[-1,4]) 
    m=1
    for x in numpy.arange(start,end,step):
        x=py.float(x)
        print(m,type(x),x)
        # s=min(x+0.1,delta)
        s=x+0.1
        kicad_mod.append(Pad(number=x,type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
            at=[m,0], size=[s,s], drill=x, layers=Pad.LAYERS_THT))
        m=m+x+s	
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    
    return kicad_mod,fname
    
gpn=gesp32s3_pin_names=[
['GND','3V3' ,'EN' ,'IO4' ,'IO5' ,'IO6' ,'IO7' ,'IO15','IO16','IO17','IO18','IO8' ,'IO19','IO20',],
['IO3','IO46','IO9','IO10','IO11','IO12','IO13','IO14','IO21','IO47','IO48','IO45'],
['GND','IO1' ,'IO2','TXD0','RXD0','IO42','IO41','IO40','IO39','IO38','IO37','IO36','IO35','IO0' ,],
]	
    
def new_footprint (w=17.5,yd=17.6,drill_1=0.96,drill_08=0.79,xt=0.1,LAYERS_THT=['F.Cu','B.Cu','F.Mask','B.Mask']):
    if not xt:xt=w/2
    x0,y0=0,0
    
    tf=rf'"{w},{yd}\n{drill_1},{drill_08} {U.stime()[-8:]}"'
    tf=rf'"{w:.2f},{yd:.2f}\n{drill_1:.2f},{drill_08:.2f}  "'

    name=f"{tf[1:-1].replace(T.backslash+'n','='*15)}"
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    # kicad_mod.setTags('q')

    # add model
    # kicad_mod.append(Model(filename="example.3dshapes/example_footprint.wrl",
                           # at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

    
    # km_text(kicad_mod,) # .split(' ')[0]
    km_text(kicad_mod,name,at=[-4,-1.5],size=[0.5,0.5]) #没有这句 lceda 导入错误
    # kicad_mod.append(KicadModTree.Text(type='value',text=tf,at=[xt,10],size=[1,1],mirror=True,layer='B.SilkS'))
    # kicad_mod.append(KicadModTree.Text(type='value',text='w,yd',at=[8,2],size=[1,1],layer='B.SilkS'))
    # kicad_mod.append(KicadModTree.Text(type='value',text=tf,at=[8,6],size=[1,1],mirror=Fa,layer='B.SilkS'))
        # create courtyard
    # kicad_mod.append(RectLine(start=[-3, -3], end=[17, 17], layer='F.CrtYd'))

    kicad_mod.append(RectLine(start=[0+x0, 0], end=[w+x0, yd], layer='F.SilkS'))
    kicad_mod.append(RectLine(start=[0+x0, 0], end=[w+x0, yd], layer='B.SilkS'))

    dx0=(w-11*1.27)/2 #  
    for n in range(12):	
        kicad_mod.append(Pad(number=n,type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
            at=[x0+ n*1.27+dx0, 0+yd], size=[drill_08-0.2, 1.6], drill=drill_08, layers=LAYERS_THT))
            
        n1y=[2.2,4.4][(n+1)%2]	
        kicad_mod.append(Pad(number='NO_'+gpn[1][n], type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
            at=[x0+ n*1.27+dx0, 0+yd+n1y], size=[0.25, n1y*1.7	], drill=drill_1, layers=LAYERS_THT))				 
    for n in range(14):					 
        sx=4
        n1x=[2.2,4.4][(n+1)%2]
        if n==13:
            sx=1.6
            kicad_mod.append(Pad(number=n, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,at=[x0-sx,n*1.27], size=[sx,0.55], drill=0, layers=LAYERS_THT))	
            kicad_mod.append(Pad(number=n, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,at=[x0+ w+sx,n*1.27], size=[sx,0.55], drill=0, layers=LAYERS_THT))	
            
        # if n==0:
            # number='GND'
        # else:
            # number=''
            
        kicad_mod.append(Pad(number='NO_'+gpn[0][n], type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,at=[x0-n1x,n*1.27], size=[n1x*1.35, 0.25], drill=drill_1, layers=LAYERS_THT))				 
        kicad_mod.append(Pad(number='NO_'+gpn[2][n], type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,at=[x0+ w+n1x,n*1.27], size=[n1x*1.35, 0.25], drill=drill_1, layers=LAYERS_THT))				 
                         
        kicad_mod.append(Pad(number=n, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                         at=[x0,n*1.27], size=[sx, drill_08-0.2], drill=drill_08, layers=LAYERS_THT)) #左 14
                        
                         
        kicad_mod.append(Pad(number=n, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                         at=[x0+ w,n*1.27], size=[sx, drill_08-0.2], drill=drill_08, layers=LAYERS_THT))

    kicad_mod.append(Pad(number='NO_'+gpn[0][0], type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,at=[x0+ w+4.4,14*1.27], size=[drill_1+0.2,drill_1+0.2], drill=drill_1, layers=Pad.LAYERS_THT))	#IO 0			 
    kicad_mod.append(Pad(number='NO_'+gpn[0][0], type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,at=[x0+ 1*1.27+dx0,0+yd+n1y+4.4], size=[drill_1+0.2,drill_1+0.2], drill=drill_1, layers=Pad.LAYERS_THT))	#IO 46		 
    # output kicad model	
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    
    # pcbnew.refresh()# AttributeError: module 'pcbnew' has no attribute 'refresh'
    return kicad_mod,fname
    
def generate_all():
    l4_9_1116=[
 (17.8, 18.0, 0.94, 0.76),
 (18.0, 18.2, 0.95, 0.77),
 (18.2, 18.4, 0.96, 0.78),
 (18.4, 18.6, 0.96, 0.79),
 (18.5, 18.7, 0.96, 0.79),
 (18.6, 18.8, 0.96, 0.79),
 (18.7, 18.9, 0.96, 0.80),
 (18.8, 19.0, 0.96, 0.81),
 (19.1, 19.3, 0.96, 0.82)]
 
    l4_9_1123=[
 (18.30, 18.10, 0.90, 0.70),
 (18.35, 18.15, 0.90, 0.70),
 (18.40, 18.18, 0.90, 0.70),
 (18.45, 18.20, 0.90, 0.70),
 (18.42, 18.22, 0.90, 0.70),
 (18.44, 18.24, 0.90, 0.70),
 (18.50, 18.26, 0.90, 0.70),
 (18.54, 18.28, 0.95, 0.75),
 (18.58, 18.30, 0.95, 0.75)]
    l4_9_1129=[
 (18.38, 18.17, 0.90, 0.70),
 (18.39, 18.18, 0.90, 0.70),
 (18.40, 18.19, 0.90, 0.70),
 (18.41, 18.20, 0.90, 0.70),
# (18.42, 18.21, 0.95, 0.76),
 # (18.43, 18.22, 0.95, 0.76),
 # (18.44, 18.23, 0.95, 0.76),
 # (18.45, 18.24, 0.95, 0.77),
 # (18.46, 18.25, 0.95, 0.78),
 ]
    l4_9_1204=[
 (18.37, 18.18, 0.95, 0.75),
 (18.38, 18.19, 0.95, 0.75),
 (18.39, 18.20, 0.95, 0.75),
 (18.40, 18.21, 0.95, 0.75),
 (18.41, 18.22, 0.95, 0.75),
 (18.42, 18.22, 0.95, 0.75),
 (18.43, 18.23, 0.95, 0.75),
 (18.44, 18.24, 0.95, 0.75),
 ]
 # 请严格按照我提交的原始文件生产。不要对焊盘过孔内径进行补偿，谢谢审核 辛苦啦
 

    for n,l4 in enumerate(l4_9_1204):
        r=new_footprint(*l4)
        print(n,r)
    # fs=F.ls(U.pwd(),include='.kicad_mod')
    
    # for x,y in U.range2d(4,4):
        # x
gall=generate_all		

def stepper57(d_2gt194=47.6):
    ''' 连皮带总距 79
单72连两边皮带 51.7	
单72 50.5
皮带厚度 0.6mm


单20 12
单20连两边皮带 13.26

79-(51.7+13.2)/2==46.55

194 :  48.155
228 :  65.922

288 ： 96.582
298 :  101.652 # 10x10 板到顶点 101.398  一般 101.398-5/2-1.6 == 97.298

340 ： 122.885
376 :  141.029
380 :  143.042
'''	
    name=fr'stepper57-d_2gt194={d_2gt194}--'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[12,60])  #没有这句 lceda 导入错误

    d47=(56.5-47)/2
    plated_hole_square_vertice_start(kicad_mod,d47,d47,47,3.9)
    plated_hole_square_vertice_start(kicad_mod,d47+47,d47+47,47,3.9,angle=45)
    
    x,y=56.5/2,56.5/2
    plated_hole(kicad_mod,x,y,38)  #57
    plated_hole(kicad_mod,x+d_2gt194,y,4.9)  # x
    plated_hole(kicad_mod,x,y+48,4.91)  #57
    
    
    # square(kicad_mod,-50,-50,side_len=100)
    edge(kicad_mod,start=[0,0],end=[100,100])
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname

def m57(dy0=-0,dxm=12,drill_screw=3.95):
    ''' 连皮带总距 79
单72连两边皮带 51.7	
单72 50.5
皮带厚度 0.6mm


单20 12
单20连两边皮带 13.26

79-(51.7+13.2)/2==46.55
'''	
    name=fr'm57={dy0}-{dxm}--'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[12,60])  #没有这句 lceda 导入错误

    wa=1.6  #  1.6 / 0.0254 = 63 mil
    h=100-(74+wa/2)
    # kicad_mod.append(KicadModTree.Line(start=[1,h], end=[99,h],layer='Edge.Cuts',width=1.6)) 
    # kicad_mod.append(KicadModTree.Line(start=[1,h+1], end=[99,h+1],layer='Edge.Cuts',width=1.6)) 
    # kicad_mod.append(KicadModTree.Line(start=[1,h+2], end=[99,h+2],layer='Edge.Cuts',width=1.6)) 
    da=1.6+0.3
    we=0.254
    w2=0.2
    day=(wa-we)/2
    # multi_dot_line(kicad_mod,([da,h+day],
                            # [da,h-day],[100-da,h-day],[100-da,h+day]),layer=['Edge.Cuts','Edge.Cuts','B.SilkS'],width=we)
    # multi_dot_line(kicad_mod,([da,h-we],[100-da,h-we]),layer=['Edge.Cuts','Edge.Cuts','B.SilkS'],width=we)
    multi_dot_line(kicad_mod,([da,h],[100-da,h]),layer=['Edge.Cuts','Edge.Cuts','B.SilkS'],width=wa)
    # multi_dot_line(kicad_mod,([da,h+day],[100-da,h+day]),layer=['Edge.Cuts','Edge.Cuts','B.SilkS'],width=we)
    
    # kicad_mod.append(KicadModTree.Line(start=[1,h], end=[99,h],layer=['Edge.Cuts','F.SilkS','B.SilkS'],width=0.8)) 
    # kicad_mod.append(KicadModTree.Line(start=[1,h], end=[99,h],layer='B.SilkS',width=0.8)) 
    dwa=0.3
    # multi_dot_line(kicad_mod,([wa-dwa,h],[50-wa/2-dwa/2,h]),layer=['Edge.Cuts','Edge.Cuts','B.SilkS'],width=wa)
    # multi_dot_line(kicad_mod,([50+wa/2+dwa/2,h],[100-(wa-dwa),h]),layer=['Edge.Cuts','Edge.Cuts','B.SilkS'],width=wa)
    

    # d47=100-(14.6+47/2)
    d47=100-((47*1.4142)/2+5.5)
    
    
    plated_hole(kicad_mod,50,d47+dy0,6.35)  #57 main
    
    
    plated_hole_square(kicad_mod,50,d47+dy0,47,drill_screw,angle=0)
    plated_hole_square(kicad_mod,50,d47   ,47,drill_screw,angle=45,holes=[0,2,3,])
    # plated_hole_square_vertice_start(kicad_mod,d47+47,d47+47,47,3.9,angle=45)
    
    # x,y=56.5/2,56.5/2
    y=100-6.93
    
    dx0=2
    
    plated_hole(kicad_mod,dx0+50-dxm*1,y,drill_screw)  
    plated_hole(kicad_mod,dx0+50+dxm*1,y,drill_screw)  
    
    plated_hole(kicad_mod,dx0+50-dxm*2,y,drill_screw)  
    plated_hole(kicad_mod,dx0+50+dxm*2,y,drill_screw)  
    
    plated_hole(kicad_mod,dx0+50-dxm*3,y,drill_screw)  
    plated_hole(kicad_mod,dx0+50+dxm*3,y,drill_screw)  
    
    
    d2=12
    # plated_hole(kicad_mod,d2,50,1.9)  
    plated_hole(kicad_mod,d2,100-70,1.9)  
    # plated_hole(kicad_mod,100-d2,50,1.9)  
    plated_hole(kicad_mod,100-d2,100-70,1.9)  
    plated_hole(kicad_mod,50,100-70,1.9)  
    
    
    plated_hole(kicad_mod,6.5,52,4.9)  
    # plated_hole(kicad_mod,8,100-40,1.9)  
    
    
    # plated_hole(kicad_mod,x,y+48,4.91)  #57
    
    
    # square(kicad_mod,-50,-50,side_len=100)
    edge(kicad_mod,start=[0,0],end=[100,100])
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname
    
    
def stepper42(dyb=61,dxm=12,drill_screw=2.9):
    name=fr'stepper42-{dyb}-{drill_screw}'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8+1,5+1])  #没有这句 lceda 导入错误
    drect=dict(start=[0,0], end=[100+0.05,100+0.05])
    
    kicad_mod.append(RectLine(**drect, layer='F.Cu'))
    kicad_mod.append(RectLine(**drect, layer='B.Cu'))
    kicad_mod.append(RectLine(**drect, layer='F.SilkS'))
    kicad_mod.append(RectLine(**drect, layer='B.SilkS'))
    
    plated_hole(kicad_mod,50,dyb,22.1)  #42 main 22.05非常紧，勉强敲入
    # plated_hole(kicad_mod,50,dyb,5.05)  #
    plated_hole_square(kicad_mod,50,dyb,31,drill_screw,angle=0)
    plated_hole_square(kicad_mod,50,dyb,47,3.9,angle=0)
    plated_hole_square(kicad_mod,50,dyb,47,3.9,angle=45,holes=[0,2,])
    
    for x in range(1,10):
        for y in range(1,10):
            if 2<x<8 and 2<y<9:continue
            if 1<x<9 and y==6:continue
            plated_hole(kicad_mod,x*10,y*10,1.9)  
                
    for x in range(5,100,10):
        for y in [5,95]:
            plated_hole(kicad_mod,x,y,1.9)  
            plated_hole(kicad_mod,y,x,1.9)  
    # edge(kicad_mod,start=[0,0],end=[100,100])
    # KicadModTree fill square F.Cu
    
        
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname	
    
def hgr20n(x=0,y=0):
    name=fr'hgr20n'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8+1,5+1])  #没有这句 lceda 导入错误

    z=[0 ,0   ], [0 , 4   ], [3.5, 8 ], [3.5, 11], [0 , 12.1], [0 , 17.5],
    
    rz=[]
    for x,y in z:
        rz.insert(0,[20-x,y])
    z=list(z)+rz	
    # z=(
# [20,17.5], [20, 12.1], [14 , 11], [14 , 8 ], [20, 4   ], [20, 0   ],
# )
    multi_dot_line(kicad_mod,[[i[0]+0,i[1]+0] for i in z],layer=['Edge.Cuts','F.SilkS','Edge.Cuts','B.SilkS'],width=0.01)	
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname	
    

def hgr20(belt=228,dscrew=5.9,x_egr=40,width=0.01):
    name=fr'hgr20-{belt}-{x_egr}'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8+1,5+1])  #没有这句 lceda 导入错误
    drect=dict(start=[0,0], end=[100+0.05,100+0.05])
    kicad_mod.append(RectLine(**drect, layer='F.Cu'))
    kicad_mod.append(RectLine(**drect, layer='B.Cu'))
    kicad_mod.append(RectLine(**drect, layer='F.SilkS'))
    kicad_mod.append(RectLine(**drect, layer='B.SilkS'))
    kicad_mod.append(RectLine(**drect, layer='Edge.Cuts'))
    
    h=17.45
    w=20
    yeb=4
    dem=(w-13.1)/2
    yem=8
    hem=3
    yet=12.1
    
    ye0=0
    multi_dot_line(kicad_mod,(
[x_egr,0],[x_egr,yeb],[x_egr+dem,yem],[x_egr+dem,yem+hem],[x_egr,yet],[x_egr,h],
# [x_egr+w,h_egr],
[x_egr+w,h],[x_egr+w,yet],[x_egr+w-dem,yem+hem],[x_egr+w-dem,yem],[x_egr+w,yeb],[x_egr+w,0],
# [x_egr,0],
),layer=['F.Cu'],width=0.01)	
        
    plated_hole(kicad_mod,50,33,dscrew)	
    
    z=[0 ,0   ], [0 , 4 ], [3.5, 6.6], [3.5, 9.4], [0 , 12.5], [0 , 17.5],
    z=[0 ,0   ], [0 , 4.4], [3.5, 7.4], [3.5, 10.2], [0 , 13.3], [0 , 17.5],
    # rz=[]
    # for x,y in z:
        # rz.insert(0,[20-x,y])
    # z=list(z)+rz

    # multi_dot_line(kicad_mod,[[i[0]+10,i[1]+0] for i in z],layer=['Edge.Cuts','F.SilkS','Edge.Cuts','B.SilkS'],width=0.01)	

    symmetric_x(kicad_mod,z,xm=20,x0=30,y0=0,angle=0,layers=['Edge.Cuts','F.SilkS','Edge.Cuts','B.SilkS'],width=0.01)
    # symmetric_x(kicad_mod,z,xmid=20,x0=10,y0=20,angle=20,layers=['Edge.Cuts','F.SilkS','Edge.Cuts','B.SilkS'],width=0.01)
    
    
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname	
    
    
def egr15(belt=228,dscrew=5.9,x_egr=(47/2+2	),h_egr=12.5,width=0.01):
    name=fr'egr15-{belt}-{x_egr}'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8+1,5+1])  #没有这句 lceda 导入错误
    drect=dict(start=[0,0], end=[100+0.05,100+0.05])
    kicad_mod.append(RectLine(**drect, layer='F.Cu'))
    kicad_mod.append(RectLine(**drect, layer='B.Cu'))
    kicad_mod.append(RectLine(**drect, layer='F.SilkS'))
    kicad_mod.append(RectLine(**drect, layer='B.SilkS'))

    w=15
    dem=(15-10.8)/2
    yem=5
    yeb=2.5
    hem=2.4
    yet=9
    ye0=0
#	multi_dot_line(kicad_mod,(
#[x_egr,0],[x_egr,yeb],[x_egr+dem,yem],[x_egr+dem,yem+hem],[x_egr,yet],[x_egr,h_egr],
###[x_egr+w,h_egr],
#[x_egr+w,h_egr],[x_egr+w,yet],[x_egr+w-dem,yem+hem],[x_egr+w-dem,yem],[x_egr+w,yeb],[x_egr+w,0],
### [x_egr,0],
#),layer=['Edge.Cuts','Edge.Cuts','F.SilkS','B.SilkS'],width=0.01)	
        
    
    # U.set('zr',([x_egr,0],[x_egr,yeb],[x_egr+dem,yem],[x_egr+dem,yem+hem],[x_egr,yet],[x_egr,h_egr],))
    symmetric_x(kicad_mod,([0,0], [0,2.5], [2.1, 5], [2.1, 7.4], [0, 9], [0, 12.5]),
        xm=15,x0=25.5,y0=0,angle=0,)	
        
    x_egr_m=x_egr+w/2
    multi_dot_line(kicad_mod,([x_egr_m,0],[x_egr_m,100]),layer=['F.SilkS','B.SilkS'],width=0.01)	
    
    xf0=x_egr_m-34/2
    xf1=x_egr_m+34/2
    yf=24
    multi_dot_line(kicad_mod,([xf0,yf],[xf1,yf]),layer=['F.SilkS','B.SilkS'],width=0.01)	
        
    sxy=x_egr_m,33	
    plated_hole(kicad_mod,*sxy,dscrew)
    
    plated_hole_square(kicad_mod,*sxy,47,3.9,angle=0)
    
    plated_hole_square(kicad_mod,*sxy,31,2.9,angle=45,holes=[0,2,3])
    
    circle(kicad_mod,33,33,radius=33,layers=['F.SilkS','B.SilkS',])
    
    circle(kicad_mod,33,33,radius=48.155,layers=['F.SilkS','B.SilkS',])
    circle(kicad_mod,33,33,radius=65.922,layers=['F.SilkS','B.SilkS',])
    multi_dot_line(kicad_mod,([0,0],[100,100]),layers=['F.SilkS','B.SilkS'],width=0.01)	
    # kicad_mod.append(KicadModTree.Circle(center=[33,33], radius=48.155, layer='F.SilkS', width=0.01))	
    x=y=67.07
    
    a,a47=0,0
    # a47=0
    # a=6
    # a,a47=40,77
    # a,a47=45,45
    
    rot=Rotation(a)
    def getr(x,y):
        x0,y0=33,33
        d,a=rot.getRealPosition([x-x0,y-y0])
        return d['x']+x0,d['y']+y0
    
    plated_hole(kicad_mod,*getr(x,y),6.35)
    plated_hole_square(kicad_mod,*getr(x,y),47,3.9,angle=a+a47)
    
    plated_hole_square(kicad_mod,x,y,31,2.9,angle=45,holes=[0,1,2,3])
    
    x=y=79.61
    plated_hole(kicad_mod,x,y,4.95)
    plated_hole_square(kicad_mod,x,y,31,2.9,angle=0,holes=[ 0,1,3])
    
        
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname	
    
def wheel_2gt(n=156,drill_screw=1.95,x0=50,y0=50,pitch=2):	
    '''
Pitch is the distance between groove centers 节距是凹槽中心之间的距离

'''	
    name=fr'2gt-{n}'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8+1,5+1])  #没有这句 lceda 导入错误
    drect=dict(start=[0,0], end=[100+0.05,100+0.05])
    kicad_mod.append(RectLine(**drect, layer='F.Cu'))
    kicad_mod.append(RectLine(**drect, layer='B.Cu'))
    kicad_mod.append(RectLine(**drect, layer='F.SilkS'))
    kicad_mod.append(RectLine(**drect, layer='B.SilkS'))

    import math
    # arc = Arc(0,0, 11 / 2, 0, 50, 0.01,layer='F.SilkS')
    if n==160 or 1:
        a180,rd,a40,dod=-179.5,0.7,38.8,0.23
        # a40=183
        a40=360+a180
    if n== 20:
        a180,rd,a40,dod=-173.7,0.7,37.9,0.6
        a40=360+a180
            
    
    # dod=0.22
    
    a=360/n
    pd=pitch*n/3.14159
    od=pd-0.51 # 外径 (OD) = 节圆直径 (PD) – (2 x U) 注：“U” = 张力线与同步带齿底部之间的距离 
    
    circle(kicad_mod,x0,y0,radius=od/2,layers=['F.SilkS','B.SilkS',])
    od-=dod
    
    FOD=pd+5
    
    U.set('po',[pd,od])
    rds=U.set('rds',[])
    
    
    def draw_ma(i,r,ad,am,angle):
        radian = math.radians(i * a+ ad)   # 将角度转换为弧度
        x=x0+ r * math.cos(radian)
        y=y0+ r * math.sin(radian)
        
            
        radian = math.radians(i * a+ am)   # 将角度转换为弧度
        cx=x0+ r * math.cos(radian)
        cy=y0+ r * math.sin(radian)
    
        rd=((x-cx)**2+(y-cy)**2)**0.5
        rds.append(rd)
        
        return arc(kicad_mod,center=[cx, cy], start=[x, y], angle=angle, layers=['F.SilkS','Edge.Cuts','B.SilkS'],width=0.01)
        # kicad_mod.append(arc)
    
        # U.set('arc',arc)
        # return arc
    arc0=None	
    for i in range(n):	
            
        ab=draw_ma(i,r=od/2,ad=a/4,am=a/2,angle=a180)
        
        # if not arc0:
            # arc0=arc
            # continue
        
        # r=od/2 
        # angle = i * a+ a/6  # 8:0.746  9:0.7738
        
        # radian = math.radians(angle)   # 将角度转换为弧度
        
        # x=50+ r * math.cos(radian)
        # y=50+ r * math.sin(radian)
        
        
        # r=od/2-0.68 # 20 -174
        # r=od/2-0.7  #160  angle=39
        r=od/2-rd #160 -179.5  angle=39
        r=od/2
        
        angle = (i * a) + a
        radian = math.radians(angle)   # 将角度转换为弧度
        cx=x0+ r * math.cos(radian)	
        cy=y0+ r * math.sin(radian)
        
        # at = Arc(center=[cx, cy], start=arc0.getEndPoint(),end=arc.getStartPoint(), layer='F.SilkS',width=0.01)
        arc(kicad_mod,center=[cx, cy], start=ab.getEndPoint(), angle=a40, layers=['F.SilkS','Edge.Cuts','B.SilkS'],width=0.01)
        # kicad_mod.append(at)

        # arc0=arc
        
        # draw_ma(i,r=od/2-0.68,ad=a/2+a/8,am=a,angle=180)
    '''
160 , -180,39.7
20  , -174,39	
    
    '''


    plated_hole(kicad_mod,x0,y0,4.95)
    
    non_plated_hole_circle(kicad_mod,x0,y0,r=(od/2)*0.9,n=n//6,d=1.55)
    # non_plated_hole_circle(kicad_mod,n//9,x0,y0,(od/2)*0.7,d=2.9)
    
    plated_hole_square(kicad_mod,x0,y0,47,3.95,angle=0)
    plated_hole_square(kicad_mod,x0,y0,31,2.95,angle=45)
        
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname	
    
def wheel_s3m(n=90,drill_screw=1.95,x0=50,y0=50,pitch=3):
    # if pitch==3:
    if pitch==2:
        name=fr'hole-2gt-{n}'
    else:	
        name=fr's3m-{n}-{pitch}'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8+1,5+1])  #没有这句 lceda 导入错误
    drect=dict(start=[0,0], end=[100+0.05,100+0.05])
    kicad_mod.append(RectLine(**drect, layer='F.Cu'))
    kicad_mod.append(RectLine(**drect, layer='B.Cu'))
    kicad_mod.append(RectLine(**drect, layer='F.SilkS'))
    kicad_mod.append(RectLine(**drect, layer='B.SilkS'))
    
    a=360/n
    pd=pitch*n/3.14159
    od=pd-3
    # -0.51 # 外径 (OD) = 节圆直径 (PD) – (2 x U) 注：“U” = 张力线与同步带齿底部之间的距离 
    
    circle(kicad_mod,x0,y0,radius=(od/2)+(pitch/4),layers=['F.SilkS','B.SilkS',])
    cwidth=0.5
    circle(kicad_mod,x0,y0,radius=(od/2)+(pitch/4)+cwidth,layers=['F.SilkS','B.SilkS','Edge.Cuts',],width=cwidth)

    if pitch==2.9:
        hole_circle(kicad_mod,n,x0,y0,(od/2),d=1.5)
    else:	
        hole_circle(kicad_mod,n,x0,y0,(od/2),d=pitch/2)
    
    # dar,na=0.8,4.6
    # dar,na=0.55,11.8
    # dar,na=0.7,6.46 # 2.8
    dar,na=0.7,6.4 # 2.9
    hole_circle(kicad_mod,n,x0,y0,(od/2)+dar,d=1,angle=a/na)
    # non_plated_hole_circle(kicad_mod,n,x0,y0,(od/2)+0.7+0.8,d=0.8,angle=a/2)
    hole_circle(kicad_mod,n,x0,y0,(od/2)+dar,d=1,angle=(a/na)*(na-1))
        
    # dar,na=0.92,6.5
    dar,na=1.1,6.3 #2.8
    hole_circle(kicad_mod,n,x0,y0,(od/2)+dar,d=1,angle=(a/na)*2)
    hole_circle(kicad_mod,n,x0,y0,(od/2)+dar,d=1,angle=(a/na)*(na-2))
    
    import math
    r=od/2
    for i in range(n):
        radian = math.radians(i * a+ a/4)   # 将角度转换为弧度
        x=x0+ r * math.cos(radian)
        y=y0+ r * math.sin(radian)
        
            
        radian = math.radians(i * a+ a/2)   # 将角度转换为弧度
        cx=x0+ r * math.cos(radian)
        cy=y0+ r * math.sin(radian)
    
        # rd=((x-cx)**2+(y-cy)**2)**0.5
        # rds.append(rd)
        
        arc(kicad_mod,center=[cx, cy], start=[x, y], angle=180, layers=['F.SilkS','B.SilkS'],width=0.01)
    
    # hole_circle(kicad_mod,n//6,x0,y0,(od/2)*0.88,d=1.55)
    hole_square(kicad_mod,x0,y0,47,3.95,angle=0)
    hole_square(kicad_mod,x0,y0,31,2.95,angle=45)
    # hole_square=(kicad_mod,x0,y0,15,2.95,angle=0)
    hole_circle(kicad_mod,3,x0,y0,8,d=2.95,angle=30)
    circle(kicad_mod,x0,y0,radius=8,layers=['F.SilkS','B.SilkS',])

    
    non_plated_hole(kicad_mod,x0,y0,6.35)
        
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname	
    
    
def hgr20_57(w=56.5):
    name=fr'hgr20_57'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8+1,5+1])  #没有这句 lceda 导入错误
    drect=dict(start=[0,0], end=[100+0.05,100+0.05])
    kicad_mod.append(RectLine(**drect, layer='F.Cu'))
    # kicad_mod.append(RectLine(**drect, layer=''))
    # kicad_mod.append(RectLine(**drect, layer='B.Cu'))
    rectline(kicad_mod,**drect, layers=glayers_edge)

    d47=(w-47)/2
    mx=50
    my=40-w/2# 37- w/2=8.75   # 余下 34.85
    hole_square_vertice_start(kicad_mod,mx-47/2,my+d47,47,3.9,func=non_plated_hole)
    
    
    non_plated_hole(kicad_mod,mx,my+w/2,6.35)
    
    rectangle_outline(kicad_mod,mx-w/2,my,w,w,layers=['F.SilkS','B.SilkS']) 
    
    # symmetric_x(kicad_mod,([0,0], [0,2.5], [2.1, 5], [2.1, 7.4], [0, 9], [0, 12.5]),
        # xm=15,x0=mx-15/2,y0=my,angle=0,)	
    
    t=-0.3
    z=[0 ,0   ], [0 , 4.4], [3.5, 7.4], [3.5, 10.2], [0 , 13.3], [0 , 17.5],
    # symmetric_x(kicad_mod,([t,0],[t,4],[t+3.5,6.6],[t+3.5,9.4],[t,12.5],[t,17.5-t]),#HGR20 外圈
        # xm=20,x0=mx-10,y0=0,angle=0,layers=['F.SilkS','B.SilkS'],width=0.01)
    symmetric_x(kicad_mod,z,#HGR20
        xm=20,x0=mx-10,y0=0,angle=0,layer=glayers_edge,width=0.01)
        # xm=20,x0=m-10,y0=-5,angle=0,layer=['F.SilkS','B.SilkS'],width=0.01)
        # xm=20,x0=w/2+10,y0=w/2+36,angle=-90,layer=['Edge.Cuts','F.SilkS','Edge.Cuts','B.SilkS'],width=0.01)
    multi_dot_line(kicad_mod,[(0,40),(100,40)],layers=glayers_silk)
    multi_dot_line(kicad_mod,[(0,50),(100,50)],layers=glayers_silk)
    multi_dot_line(kicad_mod,[(50,0),(50,100)],layers=glayers_silk)
    yk=my+w/2 
    
    kw=78
    kh=44#44
    
    hole_rect(kicad_mod,mx,yk,side_len_x=78.8,side_len_y=32,d=4.9,angle=0,holes=[0,2,3,1])
    rectline_center(kicad_mod,mx-(kw+36)/2,yk,kw,kh,layers=glayers_silk)
    rectline_center(kicad_mod,mx+(kw+36)/2-36,yk,kw,kh,layers=glayers_silk)
    # =hole_rect=(kicad_mod,mx,yk-21,side_len_x=78.8,side_len_y=53,d=4.9,angle=0,holes=[1,2]) # 40 x 53
    hole_rect(kicad_mod,mx,yk+(53/2-32/2),side_len_x=78.8,side_len_y=53,d=4.9,angle=0,holes=[0,3]) # 40 x 53
    hole_rect(kicad_mod,mx,yk-(44/2-32/2),side_len_x=78.8,side_len_y=44,d=4.9,angle=0,holes=[1,2]) # 并排 20CA
    
    
    circle(kicad_mod,mx+19.75,my+w/2,diameter=[0.3,2.2,5.5],layers=glayers_silk) # 16铝座 17,5.5,2.5 =50
    circle(kicad_mod,mx-19.75,my+w/2,diameter=[0.3,2.2,5.5],layers=glayers_silk)
    
    circle(kicad_mod,mx+24.713,my+w/2,diameter=[0.3,3,6.85],layers=glayers_silk) # 15 锌合金座 46/2=23,6.85<7,  3 =65.7
    circle(kicad_mod,mx-24.713,my+w/2,diameter=[0.3,3,6.85],layers=glayers_silk)
    
    circle(kicad_mod,mx,my+w/2,diameter=[15,16,20,22,28,30],layers=glayers_silk)
    
    
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname	
        
        
    # symmetric_x(kicad_mod,([0,0],[0,4],[3.5,6.6],[3.5,8]),# egr 对面
        # xm=20,x0=m+10,y0=w/2+37,angle=180,layers=['Edge.Cuts','F.SilkS','Edge.Cuts','B.SilkS'],width=0.01)
    # symmetric_x(kicad_mod,([0,0],[0,4],[3.5,6.6],[3.5,9.4],[0,12.5],[0,17.5]),#HGR20
        # xm=20,x0=m+10,y0=w/2+37,angle=180,layers=['F.SilkS','B.SilkS'],width=0.01)
    
    
    h=100-w/2
    # plated_hole_square(kicad_mod,h,h,47,3.9,angle=0,holes=[1,0,3])
#2 1
#3 0	

    kdx=5.5
    kdy=1.5
    # kdx,kdy=11,17.5# 
    # plated_hole_square(kicad_mod,kx/2,100-ky/2,26,3.9,angle=0,holes=[0,1,2,3])
    kx0,ky0=kdx+kx/2,100-ky/2-kdy
    # hole_rect(kicad_mod,kx0,ky0,side_len_x=36,side_len_y=32,d=4.9,angle=0,holes=[0,2,3,1])
    #def circle(kicad_mod,kx0+36/2,ky0-32/2,radius=[0.1,1.9,2.5],layers=glayers_silk)
    # rectangle_outline(kicad_mod,kdx,100-ky-kdy,kx,ky,layers=['F.SilkS','B.SilkS']) 
    
    
    kx=59
    ky=34
    rectangle_outline(kicad_mod,0,100-ky,kx,ky,layers=['F.SilkS','B.SilkS']) 
    plated_hole_square(kicad_mod,kx/2,100-ky/2,26,3.9,angle=0,holes=[0,1,2,3])
    
    # rectangle_outline(kicad_mod,100-kx,100-ky,kx,ky,layers=['F.SilkS','B.SilkS']) 
    # plated_hole_square(kicad_mod,100-kx/2,100-ky/2,26,3.9,angle=0,holes=[0,1,2,3])
    ew=1.6	
    xw=w/2  #50-w/2
    hew=my+w#+ew/2
    multi_dot_line(kicad_mod,[(0,hew),(50-xw-ew/2,hew)],layers=glayers_edge,width=ew)
    hew=my+w+ew/2
    multi_dot_line(kicad_mod,[(kx+ew/2,hew),(100,hew),],layers=glayers_edge,width=ew)
    
    xew=kx+ew/2+0.1
    multi_dot_line(kicad_mod,[(xew,100-ky),(xew,100),],layers=glayers_edge,width=ew)
    # multi_dot_line(kicad_mod,[(50+xw,hew),(100,hew),],layers=glayers_edge,width=ew)
    

def egr15_57(w57=56.6):
    name=fr'egr15_57_'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8+1,5+1])  #没有这句 lceda 导入错误
    drect=dict(start=[0,0], end=[100+0.05,100+0.05])
    kicad_mod.append(RectLine(**drect, layer='F.Cu'))
    # kicad_mod.append(RectLine(**drect, layer='B.Cu'))
    kicad_mod.append(RectLine(**drect, layer='F.SilkS'))
    kicad_mod.append(RectLine(**drect, layer='B.SilkS'))	
    
    
    d47=(w57-47)/2
    mx=w57/2
    my=0# 37- w/2 
    hole_square_vertice_start(kicad_mod,mx-47/2,my+d47,47,3.9,func=non_plated_hole)
    
    non_plated_hole(kicad_mod,mx,my+w57/2,5.9)
    
    rectangle_outline(kicad_mod,mx-w57/2,my,w57,w57,layers=['F.SilkS','B.SilkS']) 
    
    symmetric_x(kicad_mod,([0,0], [0,2.7], [2.1, 5.2], [2.1, 7.6], [0, 9.2], [0, 12.7]),
        xm=15,x0=mx-15/2,y0=my,angle=0,)	
        
    ew=1.6	
    hew=w57+ew/2
    xw=5  #50-w/2
    multi_dot_line(kicad_mod,[(w57,0),(w57,50)],layers='Edge.Cuts',width=ew)
    multi_dot_line(kicad_mod,[(0,hew),(w57,hew)],layers='Edge.Cuts',width=ew)
    # multi_dot_line(kicad_mod,[(50+xw,hew),(100,hew),],layers='Edge.Cuts',width=ew)
    
    multi_dot_line(kicad_mod,[(0,50),(100,50)],layers=glayers_silk)
    multi_dot_line(kicad_mod,[(50,0),(50,100)],layers=glayers_silk)
    
    kx=57
    ky=34
    # rectangle_outline(kicad_mod,0,100-ky,kx,ky,layers=['F.SilkS','B.SilkS']) 
    # plated_hole_square(kicad_mod,kx/2,100-ky/2,26,3.9,angle=0,holes=[0,1,2,3])
    
    
    kw=78
    kh=44#44
    
    x0=w57+kh/2
    # y0=100-kh/2-0.6
    y0=kw/2
    rectline_center(kicad_mod,x0,y0,kh,kw,layers=glayers_silk)
    rectline_center(kicad_mod,x0,y0,0.01,kw,layers=['F.SilkS','B.SilkS']) 
    rectline_center(kicad_mod,x0,y0,kh,0.01,layers=['F.SilkS','B.SilkS']) 
    
    t57=(40+w57/2)
    hole_rect_center(kicad_mod,x0,y0,side_len_x=32,side_len_y=36,d=4.85,angle=0,holes=[]) # 40 x 53
    
    kw=59
    kh=34
    # x0,y0=kx/2,100-ky/2
    rectline_center(kicad_mod,x0,y0,kh,kw,layers=['F.SilkS','B.SilkS']) 
    rectline_center(kicad_mod,x0,y0,4,20,layers=['F.SilkS','B.SilkS']) 
    rectline_center(kicad_mod,x0,y0,10,30,layers=['F.SilkS','B.SilkS']) 
    plated_hole_square(kicad_mod,x0,y0,26,3.9,angle=0,holes=[0,1,2,3])
    
    plated_hole_square(kicad_mod,x0,y0,26,3.9,angle=0,holes=[0,1,2,3])
    
    
    for x in range(1,20):
        for y in  range(1,8):
            non_plated_hole(kicad_mod,x*5,60+y*5,1.6)
    
    # multi_dot_line(kicad_mod,[(100-kh,t57+ew/2),(100-kh,100)],layers='Edge.Cuts',width=ew)
    # multi_dot_line(kicad_mod,[(100-kh+ew,100-kw-ew/2),(100,100-kw-ew/2)],layers='Edge.Cuts',width=ew)
    
    
    # plated_hole_square(kicad_mod,kx+(kx)/2,100-ky/2,26,3.9,angle=0,holes=[0,1,2,3])
    # yk=100-ky-ew/2
    # multi_dot_line(kicad_mod,[(0,yk),(50-xw,yk)],layers=glayers_edge,width=ew)
    # multi_dot_line(kicad_mod,[(50+xw,yk),(100,yk)],layers=glayers_edge,width=ew)
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname		
    
def hgr20_egr15_k(ew=1.6):	
    name=fr'hgr20_egr15_k'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8+1,5+1])  #没有这句 lceda 导入错误
    drect=dict(start=[0,0], end=[100+0.05,100+0.05])	
    rectline(kicad_mod,**drect, layers=['F.Cu','F.SilkS','B.SilkS'])


    w57=56.5
    d47=(w57-47)/2
    mx=w57/2
    z=[0 ,0   ], [0 , 4.4], [3.5, 7.4], [3.5, 10.2], [0 , 13.3], [0 , 17.5],
    symmetric_x(kicad_mod,z,xm=19.8,x0=mx-10/2,y0=0,angle=0,layers=glayers_edge,width=0.01)
    
    mx10=16.1
    my=18.3+5 #23.3 
    
    hole_square_vertice_start(kicad_mod,mx-47/2,my+d47,47,3.9,func=non_plated_hole)
    non_plated_hole(kicad_mod,mx,my+w57/2,6.35)
    rectline_center(kicad_mod,mx,my+w57/2,w57,w57,layers=glayers_silk) 
    
    
    


    x0=y0=50
    
    # non_plated_hole(kicad_mod,x0,y0,3.9)
    # rectline_center(kicad_mod,x0,y0,20,6,layers=glayers_silk)
    
    kw=78
    kh=44#44
    
    x0=100-kh/2
    y0=100-kw/2
    rectline_center(kicad_mod,x0,y0,kh,kw,layers=glayers_silk)
    rectline_center(kicad_mod,x0,y0,0.01,kw,layers=['F.SilkS','B.SilkS']) 
    rectline_center(kicad_mod,x0,y0,kh,0.01,layers=['F.SilkS','B.SilkS']) 
    ew=1.6
    
    t57=(40+w57/2)
    hole_rect_center(kicad_mod,x0,y0,side_len_x=32,side_len_y=36,d=4.85,angle=0,holes=[]) # 40 x 53
    multi_dot_line(kicad_mod,[(100-kh,t57+ew/2),(100-kh,100)],layers='Edge.Cuts',width=ew)
    multi_dot_line(kicad_mod,[(100-kh+ew,100-kw-ew/2),(100,100-kw-ew/2)],layers='Edge.Cuts',width=ew)
    
    # hole_rect(kicad_mod,x0,y0,side_len_x=78.8,side_len_y=32,d=4.9,angle=0,holes=[0,2,3,1])
    # rectline_center(kicad_mod,x0,y0,kw,kh,layers=glayers_silk)
    # rectline_center(kicad_mod,x0,y0,kw,kh,layers=glayers_silk)
    # hole_rect(kicad_mod,mx,yk-21,side_len_x=78.8,side_len_y=53,d=4.9,angle=0,holes=[1,2]) # 40 x 53
    # hole_rect_center(kicad_mod,x0,y0,side_len_x=40,side_len_y=53,d=4.9,angle=0,holes=[]) # 40 x 53
    # hole_rect_center(kicad_mod,x0,y0,side_len_x=36,side_len_y=32,d=4.9,angle=0,holes=[]) # 并排 20CA


    
    kw=59
    kh=34
    # x0,y0=kx/2,100-ky/2
    rectline_center(kicad_mod,x0,y0,kh,kw,layers=['F.SilkS','B.SilkS']) 
    rectline_center(kicad_mod,x0,y0,4,20,layers=['F.SilkS','B.SilkS']) 
    rectline_center(kicad_mod,x0,y0,10,30,layers=['F.SilkS','B.SilkS']) 
    plated_hole_square(kicad_mod,x0,y0,26,3.9,angle=0,holes=[0,1,2,3])
    
    plated_hole_square(kicad_mod,w57/2,100-(100-t57)/2,26,3.9,angle=0,holes=[0,1,2,3])
    
    multi_dot_line(kicad_mod,[(11,t57-ew/2),(w57-11,t57-ew/2)],layers='Edge.Cuts',width=ew) # 左边 横
    non_plated_hole(kicad_mod,1,t57,0.8)
    non_plated_hole(kicad_mod,5,t57,0.8)
    non_plated_hole(kicad_mod,w57-6,t57,0.8)
    non_plated_hole(kicad_mod,w57-2,t57,0.8)
    
    for i in range(9):
        non_plated_hole(kicad_mod,w57-0.35,23+5*i,0.8)
    
    
    # xw=5
    # multi_dot_line(kicad_mod,[(0,yk),(50-xw,yk)],layers=glayers_edge,width=ew)
    # multi_dot_line(kicad_mod,[(50+xw,yk),(100,yk)],layers=glayers_edge,width=ew)
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname		
    
def egr15_jz(ew=1.6):	
    name=fr'egr15_jz'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8+1,5+1])  #没有这句 lceda 导入错误
    drect=dict(start=[0,0], end=[100+0.05,100+0.05])	
    rectline(kicad_mod,**drect, layers=['F.Cu','F.SilkS','B.SilkS'])

    
    w57=56.5
    hole_rect_center(kicad_mod,w57/2,100-(100-w57)/2,26,3.1,angle=0,holes=[0,1,2,3],func=circle)

    d47=(w57-47)/2
    mx=w57/2
    z=[0,0], [0,2.7], [2.1, 5.2], [2.1, 7.6], [0, 9.2], [0, 12.7]
    symmetric_x(kicad_mod,z,xm=15,xmid=mx,y0=0,angle=0,layers=glayers_edge,width=0.01)
    
    z=[0 ,0   ], [0 , 4.3], [3.5, 7.4], [3.5, 10.2], [0 , 13.3], [0 , 17.5],
    symmetric_x(kicad_mod,z,xm=19.8,xmid=mx,y0=0,angle=0,layers=glayers_silk,width=0.01)

    
    hz57=mx
    ktop=24
    multi_dot_line(kicad_mod,[(0,hz57),(100,hz57)],layers=glayers_silk)
    non_plated_hole (kicad_mod,mx,hz57,6.35)
    hole_rect_center(kicad_mod,mx,hz57,47,d=3.9,holes=[0,1,2,]) # 右下角0  ，逆时针
    hole_rect_center(kicad_mod,mx,hz57,47,d=3.9,func=circle)
    
    multi_dot_line(kicad_mod,[(mx-17,ktop),(mx+17,ktop)],layers=glayers_silk)
    # multi_dot_line(kicad_mod,[(mx-22,30),(mx+22,30)],layers=glayers_silk)
    multi_dot_line(kicad_mod,[(mx,0),(mx,100)],layers=glayers_silk)
    
    rectline_center(kicad_mod,mx,hz57,w57,w57,layers=glayers_silk) 
    # ktop+=1.6 # 转接板
    hz57=39.8
    multi_dot_line(kicad_mod,[(0,hz57),(100,hz57)],layers=glayers_silk)
    
    mx10=-16.1
    my10=1.2+18.3+5 #19.5+5 =24.5
    x1,y1=mx+mx10,ktop+my10
    non_plated_hole(kicad_mod,x1,y1,10)
    # hole_square_vertice_start(kicad_mod,x1,y1,47,3.9,angle=45,func=non_plated_hole)
    hole_rect_center(kicad_mod,x1,y1,47,d=3.9,angle=45,func=circle)# 依赖circle默认参数 layers=glayers_silk
    hole_rect_center(kicad_mod,x1,y1,47,d=3.9,angle=0,func=circle)# 依赖circle默认参数 layers=glayers_silk
    
    circle(kicad_mod,x1,y1,radius=48.155,layers=['F.SilkS','B.SilkS',])  #2gt-194
    circle(kicad_mod,x1,y1,radius=65.922,layers=['F.SilkS','B.SilkS',]) #228
    x228=x1+(65.922**2-(y1-hz57)**2)**0.5
    non_plated_hole (kicad_mod,x228,hz57,6.35)
    hole_rect_center(kicad_mod,x228,hz57,47,d=3.9,angle=0,holes=(0,1)) #  右下0，  逆时针
    hole_rect_center(kicad_mod,x228,hz57,47,d=3.9,angle=0,holes=(2,3),func=circle) 
    circle(kicad_mod,x1,y1,radius=96.582,layers=['F.SilkS','B.SilkS',]) #288
    
    
    mx10=-16.1
    my10=1.2+18.3+5 #19.5+5 =24.5
    x,y=mx+mx10,30+my10
    circle(kicad_mod,x,y,[1,4,6,8,10])
    # my=40-w57/2
    
    # hole_square_vertice_start(kicad_mod,mx-47/2,my+d47,47,3.9,func=non_plated_hole)
    # non_plated_hole(kicad_mod,mx,my+w57/2,6.35)
    # rectline_center(kicad_mod,mx,my+w57/2,w57,w57,layers=glayers_silk) 
    m=3
    ym=int(45/m)
    for x in range(1,int(100/m)):
        for y in  range(1,ym):
            non_plated_hole(kicad_mod,x*m,(100-m*ym)+y*m,1)
    
    
    
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname		
    
def hgr20_jz():	
    name=fr'hgr20_jz'
    kicad_mod = Footprint(name)
    kicad_mod.setDescription(name)
    km_text(kicad_mod,name,at=[8+1,5+1])  #没有这句 lceda 导入错误
    drect=dict(start=[0,0], end=[100+0.05,100+0.05])	
    rectline(kicad_mod,**drect, layers=['F.Cu','F.SilkS','B.SilkS'])


    ew=1.6
    
    w57=56.5
    d47=(w57-47)/2
    mx=w57/2
    mx=50
    
    z=[0 ,0   ], [0 , 4.2], [3.45, 7.4], [3.45, 10.2], [0 , 13.3], [0 , 17.5],
    symmetric_x(kicad_mod,z,xm=19.7,xmid=mx,y0=0,angle=0,layers=glayers_edge,width=0.01)
    hz57=39.4
    ktop=30
    multi_dot_line(kicad_mod,[(0,hz57),(100,hz57)],layers=glayers_silk)
    non_plated_hole(kicad_mod,mx,hz57,6.35) #
    hole_rect_center(kicad_mod,mx,hz57,47,d=3.9,func=non_plated_hole,holes=[0,1,2])
    hole_rect_center(kicad_mod,mx,hz57,47,d=3.9,func=circle)
    
    multi_dot_line(kicad_mod,[(mx-22,30),(mx+22,30)],layers=glayers_silk)
    multi_dot_line(kicad_mod,[(mx,0),(mx,100)],layers=glayers_silk)
    
    rectline_center(kicad_mod,mx,hz57,w57,w57,layers=glayers_silk) 
    
    
    
    mx10=-16.1
    my10=1.2+18.3+5 #19.5+5 =24.5
    x1,y1=mx+mx10,ktop+my10
    non_plated_hole(kicad_mod,x1,y1,9.9)
    circle(kicad_mod,x1,y1,diameter=[9.9,11,12,13,14,15,16,75,115,y1*2])
    multi_dot_line(kicad_mod,[(0,y1),(100,y1)],layers=glayers_silk)
    
    bj=(38+6.5)/2+0.2#菱形轴承座
    # non_plated_hole(kicad_mod,x1,y1-bj,5.9)
    # non_plated_hole(kicad_mod,x1,y1+bj,5.9)
    hole_rect_center(kicad_mod,x1,y1,(bj*2)/1.4142,d=5.85,angle=45,holes=(0,2),) # 45°  右下变正右，逆时针转45
    # hole_rect_center(kicad_mod,x1,y1,(bj*2)/1.4142,d=[0.1,1,3,5.85,6.5],angle=45,func=circle,) # 45°  右下变正右，逆时针转45
    
    # hole_square_vertice_start(kicad_mod,x1,y1,47,3.9,angle=45,func=non_plated_hole)
    hole_rect_center(kicad_mod,x1,y1,47,d=3.9,angle=45,func=circle)# 依赖circle默认参数 layers=glayers_silk
    
    hole_rect_center(kicad_mod,x1,y1,16,d=[0.1,1,2,3,4,5],angle=45,func=circle,)# 齿轮中心固定
    
    # circle(kicad_mod,x1,y1,radius=48.155,layers=['F.SilkS','B.SilkS',])  #2gt-194
    # circle(kicad_mod,x1,y1,radius=65.922,layers=['F.SilkS','B.SilkS',]) #228
    x228=x1+(65.922**2-(y1-hz57)**2)**0.5
    circle(kicad_mod,x228,hz57,6.35)  #non_plated_hole
    hole_rect_center(kicad_mod,x228,hz57,47,d=3.9,angle=0,holes=(0,1)) #  右下0逆时针
    hole_rect_center(kicad_mod,x228,hz57,47,d=3.9,angle=0,holes=(2,3),func=circle) 
    # circle(kicad_mod,x1,y1,radius=96.582,layers=['F.SilkS','B.SilkS',]) #288
    
    # m=2
    # ym=int(35/m)
    # for x in range(1,int(100/m)):
        # for y in  range(1,ym):
            # non_plated_hole(kicad_mod,x*m,(100-m*ym)+y*m,0.8)
    
    
    file_handler = KicadFileHandler(kicad_mod)
    fname=f'{T.file_legalized(name)}.kicad_mod'
    file_handler.writeFile(fname)
    return kicad_mod,fname
    
    