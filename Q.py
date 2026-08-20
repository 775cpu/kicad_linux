#coding=utf-8
try:
    from qgb import py
    U,T,N,F=py.importUTNF()
except:raise
# try:
    # from qgb.kicad import *
    # import qgb.kicad
# except:
    # from kicad import *
    # import kicad
import sys,os
py=sys.modules['qgb.py']
from kicad import *
import kicad
try:
    
    from memory_detect import rpc_get_memory_report,rpc_check_container_contents
except Exception as e:
    rpc_check_container_contents=e
#

import os

def board_to_svg(board, layers=None, output_dir=None):
    """
    适配 KiCad 10.0 的 PCB 图层导出 SVG 函数
    
    :param board: pcbnew.BOARD 对象
    :param layers: 图层名称列表或单图层，支持 ['F.Cu', 'Edge.Cuts'] 或 ['F_Cu'] 等写法
    :param output_dir: 输出目录路径（默认输出至 PCB 所在目录）
    :return: 生成的 SVG 文件路径列表
    """
    if not board:
        raise ValueError("请传入有效的 BOARD 对象 (例如通过 pcbnew.GetBoard() 或 pcbnew.LoadBoard())")

    # 1. 规范化 layers 参数（默认导出常用图层）
    if layers is None:
        layers = ["F.Cu", "B.Cu", "F.SilkS", "B.SilkS", "F.Mask", "B.Mask", "Edge.Cuts"]
    elif isinstance(layers, (str, int)):
        layers = [layers]

    # 2. 确定输出路径
    board_path = board.GetFileName()
    if not output_dir:
        output_dir = os.path.dirname(board_path) if board_path else "."
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 3. 配置 KiCad 10.0 绘图参数
    pc = pcbnew.PLOT_CONTROLLER(board)
    popt = pc.GetPlotOptions()

    popt.SetOutputDirectory(output_dir)
    popt.SetPlotFrameRef(False)                            # 禁用边框基准线
    
    # [已修复]: KiCad 10.0 中已移除 SetLineWidth
    # popt.SetLineWidth(pcbnew.FromMM(0.1))                
    
    popt.SetPlotValue(True)                                # 导出元件 Value 文本
    popt.SetPlotReference(True)                            # 导出元件 Reference (位号)
    popt.SetPlotFPText(True)                               # 导出封装属性文本
    
    try:
        popt.SetDrillMarksType(pcbnew.PCB_PLOT_PARAMS.FULL_DRILL_SHAPE) 
    except AttributeError:
        pass

    # 兼容性处理：KiCad 10.0 已废弃并移除 SetPlotInvisibleItem
    if hasattr(popt, 'SetPlotInvisibleItem'):
        popt.SetPlotInvisibleItem(True)

    # 4. 执行图层导出
    generated_files = []

    for item in layers:
        # 解析图层 ID 与名称
        if isinstance(item, str):
            clean_item = item.strip().replace(' ', '.')
            layer_id = board.GetLayerID(clean_item)
            
            if layer_id == pcbnew.UNDEFINED_LAYER:
                alt_item = clean_item.replace('_', '.')
                layer_id = board.GetLayerID(alt_item)

            layer_name = item
        else:
            layer_id = item
            layer_name = board.GetLayerName(layer_id)

        # 图层合法性校验
        if layer_id == pcbnew.UNDEFINED_LAYER:
            print(f"[WARN] 无法识别的图层名称: {item}，已跳过")
            continue

        if not board.IsLayerEnabled(layer_id):
            print(f"[INFO] 图层 {layer_name} 未在当前板子上启用，已跳过")
            continue

        # 设置绘图图层并输出 SVG
        pc.SetLayer(layer_id)
        
        # 格式化文件名，避免路径分隔符号干扰
        file_suffix = str(layer_name).replace('.', '_').replace('/', '_').replace(' ', '_')
        pc.OpenPlotfile(file_suffix, pcbnew.PLOT_FORMAT_SVG, f"{layer_name} Layer")
        pc.PlotLayer()
        
        # [已修复]: PLOT_CONTROLLER 在 API 中正确的方法名称是 ClosePlot()
        pc.ClosePlot()

        out_path = pc.GetPlotFileName()
        generated_files.append(out_path)
        print(f"[OK] 已导出: {out_path}")

    return generated_files



def IBT_2x4(kicad_mod=None, x=0, y=0, angle=0, zip=0):
    ''' 
    IBT H桥 
    '''
    if not kicad_mod:
        assert x == y == 0
        kicad_mod = new_kicad_mod(w=30,h=20, start='-w/2,-h/2', text_at=[-9,'-h/2+1'], ) # x,y[0,0]坐标 是  板子w，h中心
        
    # plated_hole_line(kicad_mod,x,y,pitch=2.54,n=4,d=0.9,size=1.2,smt_pad=1,angle=angle)# 
    # plated_hole_line(kicad_mod,x,y+2.54,pitch=2.54,n=4,d=1,size=1.2,smt_pad=1,angle=angle)# 
    # 上排：SMT 焊盘中心向上 (Y 轴负方向) 偏移 
    size=1.2
    dy=0.7
    psize=[1,dy*2]
    x=0
    y=-8
    
    cs=plated_hole_line(kicad_mod, x, y, pitch=2.54, n=4, d=0.9, size=size,angle=angle, smt_pad_ka=dict(at_delta=[0,-dy],size=psize)  )

    # 下排：SMT 焊盘中心向下 (Y 轴正方向) 偏移 
    plated_hole_line(kicad_mod,x,y+2.54,pitch=2.54,n=4,d=1.0, size=size,angle=angle, smt_pad_ka=dict(at_delta=[0,dy],size=psize)  ,)

    cs8=plated_hole_line(kicad_mod,x-10,y+5,pitch=3.5,n=8)
    
    #怎么走线 cs[0]  和 cs[8][0]
    
    rectangle_full(kicad_mod,0,5, w=9, h=2, layers=['F.Cu',]) 
    rectline_center(kicad_mod,0,-5, w=9, h=2, layers=['F.Cu',]) 
    
    return write_kicad_mod(kicad_mod, zip=zip)

def h_bridge_module(kicad_mod=None, x=0, y=0, angle=0, w=24.8, h=21.2, d=1.6, plated_size_delta=0.1, zip=0):
    ''' 
    红色 H桥 MX1508小功率电机驱动模块  电压范围2.0 V ~ 9.6 V
    - 尺寸: w=24.8mm, h=21.2mm
    - 孔径: d
    - 坐标系: KiCad (+X 向右, +Y 向下, 原点位于中心)
    '''
    if not kicad_mod:
        assert x == y == 0
        kicad_mod = new_kicad_mod(w=w, h=h, start='-w/2,-h/2', text_at=[-5, -13], d=d)

    # 1. 模块外形丝印边框与中心十字
    rectline_center(kicad_mod, x, y, w=w, h=h, angle=angle, crosshair=1, layers=glayers_silk)

    # 基础参数定义 (全基于 x, y 相对坐标)
    pitch = 2.54                # 标准排针间距 2.54mm
    x_left = x - w/2 + 5.5      # 左侧排针/焊盘 X 坐标
    x_right = x + w/2 - 5.5     # 右侧排针/焊盘 X 坐标
    y_top_start = y - 8.5       # 上部第一排孔 Y 坐标 (-Y 向上)
    gap_3 = 3.5

    # 统一焊盘参数：通孔 + 辅助 SMT 焊盘（X 方向拉长、Y 方向减小 便于焊接并避免连锡。）
    plated_ka = dict(diameter=d, size=d+plated_size_delta,
                     smt_pad_ka=dict(size=[d+1,d]))

    # --- 2. 右上角信号输入孔 (IN4 -> IN1, 从上往下) ---
    # 孔间距：第1-2孔 2.54，第2-3孔 gap_3，第3-4孔 2.54
    y_in1 = y_top_start
    y_in2 = y_top_start + 2.54
    y_in3 = y_top_start + 2.54 + gap_3
    y_in4 = y_top_start + 2.54 + gap_3 + 2.54

    # IN4 (第1孔)
    plated_hole(kicad_mod, x_right, y_in1, **plated_ka)
    text(kicad_mod, 'IN4', at=[x_right - 3.2, y_in1], size=[1.2, 1.0], layers=glayers_silk)

    # IN3 (第2孔)
    plated_hole(kicad_mod, x_right, y_in2, **plated_ka)
    text(kicad_mod, 'IN3', at=[x_right - 3.2, y_in2], size=[1.2, 1.0], layers=glayers_silk)

    # IN2 (第3孔)
    plated_hole(kicad_mod, x_right, y_in3, **plated_ka)
    text(kicad_mod, 'IN2', at=[x_right - 3.2, y_in3], size=[1.2, 1.0], layers=glayers_silk)

    # IN1 (第4孔)
    plated_hole(kicad_mod, x_right, y_in4, **plated_ka)
    text(kicad_mod, 'IN1', at=[x_right - 3.2, y_in4], size=[1.2, 1.0], layers=glayers_silk)

    # --- 3. 左上角电机输出孔 (MOTOR-B, MOTOR-A, 从上往下) ---
    y_m1 = y_top_start
    y_m2 = y_top_start + 2.54
    y_m3 = y_top_start + 2.54 + gap_3
    y_m4 = y_top_start + 2.54 + gap_3 + 2.54

    plated_hole(kicad_mod, x_left, y_m1, **plated_ka)
    plated_hole(kicad_mod, x_left, y_m2, **plated_ka)
    plated_hole(kicad_mod, x_left, y_m3, **plated_ka)
    plated_hole(kicad_mod, x_left, y_m4, **plated_ka)

    # 左侧竖向丝印文字
    text(kicad_mod, 'MOTOR-B', at=[x - 6, y_top_start + 0.5 * pitch], size=[1.2, 1.0], angle=90, layers=glayers_silk)
    text(kicad_mod, 'MOTOR-A', at=[x - 6, y_top_start + 2.5 * pitch], size=[1.2, 1.0], angle=90, layers=glayers_silk)

    # --- 4. 中上部主控芯片丝印外框 ---
    rectline_center(kicad_mod, x, y - 4.5, w=5.0, h=9.5, angle=angle, layers=glayers_silk)

    # --- 5. 右下角非电镀安装孔 (NPTH, d=2.5) ---
    non_plated_hole(kicad_mod, x + w/2 - 2.5, y + 2.2, d=2.5)

    # --- 6. 右下角电源孔 (- 和 +, 从上往下) ---
    xp = x + w/2 - 2
    y_p_neg = y + 5.2
    y_p_pos = y_p_neg + pitch

    plated_hole(kicad_mod, xp, y_p_neg, **plated_ka)
    text(kicad_mod, '-', at=[xp - 3.0, y_p_neg], size=[1.5, 1.2], layers=glayers_silk)

    plated_hole(kicad_mod, xp, y_p_pos, **plated_ka)
    text(kicad_mod, '+', at=[xp - 3.0, y_p_pos], size=[1.5, 1.2], layers=glayers_silk)

    # --- 7. 左下角元件丝印方框标记 (D1, R1) ---
    y_comp = y + 6.0
    xd = x - 10.5

    rectline_center(kicad_mod, xd, y_comp, w=1.8, h=3.2, angle=angle, layers=glayers_silk)
    text(kicad_mod, 'R1', at=[xd, y + 9.2], size=[1.2, 1.0], layers=glayers_silk)

    rectline_center(kicad_mod, xd + 2.5, y_comp, w=1.8, h=4, angle=angle, layers=glayers_silk)
    text(kicad_mod, 'D1', at=[xd + 2.5, y + 9.2], size=[1.2, 1.0], layers=glayers_silk)

    # 电容开槽
    non_plated_hole(kicad_mod, x - 3.5, y + 5.8, 6.5 + 0.55)
    non_plated_hole(kicad_mod, x + 3.5, y + 5.8, 6.5 + 0.55)

    return write_kicad_mod(kicad_mod, zip=zip)

def steering_gear_1m(teeth=23,y=20,w=100, zip=0):
    # y = 20
    kicad_mod = new_kicad_mod(w=w, h=w,teeth=teeth,y=y)

    # ==================== 3. 坐标与位置计算 ====================
    x = w / 2
    
    # ==================== 1. 参数定义区 ====================
    m = 1             # 模数 (Module)
            # 齿数 (Teeth)

    rack_w = 200      # 齿条宽度 (mm)
    rack_h = 10       # 齿条截面高度 (10mm 正方形齿条)
    outer_margin = 3  # 避空圆/外圆相比齿顶圆增加的直径边距 (24 + 3 = 27)
    
    # 紧密啮合偏移量 (单位: mm，填 0.2 即向前压紧 0.2mm，填 0 则为理论啮合距离)
    tightness_offset = 0.2  

    # ==================== 2. 几何与尺寸计算 ====================
    d_pitch = m * teeth               # 分度圆直径 ( 22 mm )
    d_addendum = m * (teeth + 2)      # 齿顶圆直径 ( 24 mm )
    d_outer = d_addendum + outer_margin # 外围辅助圆直径 ( 27 mm )

    r_pitch = d_pitch / 2.0       # 齿轮分度圆半径 ( 11 mm )

    # 【推导逻辑】
    # 1. 齿条节线到齿条底面距离 hp = rack_h - m (10 - 1 = 9mm)
    # 2. 齿轮中心到齿条底面距离 dgr = y + r_pitch + (rack_h - m) - tightness_offset
    #    即: y + 11 + 9 - 0.2 = y + 19.8 mm
    # 3. 齿条中心 yg = dgr - (rack_h / 2.0) = y + 19.8 - 5 = y + 14.8 mm
    
    # 通用化一句话公式：
    yg = y + r_pitch + (rack_h / 2.0) - m - tightness_offset

    # ==================== 4. KiCad 绘图逻辑 ====================
    flange_bearing_outline_KFL8(kicad_mod, x, y, layers=glayers_silk)
    # two_hole(kicad_mod, x, y, 36.5, 5, angle=0, holes=[0, 1], hole_func=non_plated_hole) # 8 mm 轴承座

    flange_bearing_outline_KFL8(kicad_mod, x, y, layers=glayers_silk, angle=90, hole_func=circle)
    # two_hole(kicad_mod, x, y, 36.5, 4, angle=90, holes=[0], hole_func=non_plated_hole) # 竖向

    # 参数化非镀铜孔 (匹配齿顶圆尺寸 24mm)
    non_plated_hole(kicad_mod, x, y, d_addendum)

    # 参数化外围辅助圆 (27mm)
    circle(kicad_mod, x, y, d_outer)

    rectline_center(kicad_mod, x, y, w=47.5, h=4, crosshair=1) # 最长十字线

    # 参数化齿条绘制
    rectline_center(kicad_mod, x, yg, w=rack_w, h=rack_h, crosshair=0) # 齿条    
    
    xd=30
    rectline_center(kicad_mod,x+xd,yg,34,10,angle=0,layers=glayers_edge_pure)
    rectline_center(kicad_mod,x-xd,yg,34,10,angle=0,layers=glayers_edge_pure)
    
    hole_rect_center(kicad_mod,x,yg,side_len_x=84,side_len_y=16,angle=0,d=4)
    
    d=4
    M =6
    for i in range(M): # 
        continue
        xi = (i + 0.5) * (w/ M) #  直接计算第i个元件的中心X坐标
        non_plated_hole(kicad_mod,xi,dgr+d/2,d)
        
        if i in [0,5]:
            non_plated_hole(kicad_mod,xi,dgr-10-d/2-0.5,d)
        
        # if i not in [1,4]:
            # non_plated_hole(kicad_mod,xi,dgr+d+10+d/2+0.5,d)
    
    two_hole(kicad_mod,x,y-4,60,6,angle=0,holes=[0,1,],hole_func=non_plated_hole) #上固定孔
    # hole_rect_center(kicad_mod,50,50,side_len_x=60,angle=0,d=6)
    
    
    
    x=75/2
    y=w-44/2
    hgr20_block(kicad_mod,x,y,hole=4.9,angle=0,mid_hole=2) #def hgr20_block
    ty=w-44-0.8
    tx=75+0.8
    multi_dot_line(kicad_mod,[(0,ty),(tx,ty)],width=1.6,layers=glayers_edge_pure,segments=10)
    multi_dot_line(kicad_mod,[(tx,ty),(tx,y-7)],width=1.6,layers=glayers_edge_pure,segments=10)
    multi_dot_line(kicad_mod,[(tx,w),(tx,y+7)],width=1.6,layers=glayers_edge_pure,segments=10)
    
    return write_kicad_mod(kicad_mod,zip=zip)
    
def tht_pad_array(kicad_mod, x, y, rows, cols, row_spacing=2.54, col_spacing=2.54, d=0.95, size=1.2, angle=0,number_array=None):
    size = min(size, row_spacing-0.2, col_spacing-0.2) #强制校验焊盘外径不得大于行列最小间距zs
    x_start = x - (cols - 1) * col_spacing / 2 #严格计算整体矩阵的X轴中心起始点zs
    y_start = y - (rows - 1) * row_spacing / 2 #严格计算整体矩阵的Y轴中心起始点zs
    for r in range(rows):
        for c in range(cols):
            px = x_start + c * col_spacing #计算当前阵列点的原始X坐标zs
            py = y_start + r * row_spacing #计算当前阵列点的原始Y坐标zs
            px, py = rotate_point(px, py, angle, x, y) #若有角度则绕整体中心旋转zs
            
            if number_array:
                try:t=number_array[r][c]
                except Exception:t=None
            else:t=None
            plated_hole(kicad_mod, px, py, d, size,number=t) #在最终定位点生成带外径尺寸的通孔焊盘zs    
    
def plug3(kicad_mod, x, y,angle=0):
    rectline_center(kicad_mod,x,y,6,13.8,angle=180,layers=glayers_silk)
    
    number_array=[['Gl','Gr'],['Bl','Br'],['Rl','Rr']]
    tht_pad_array(kicad_mod,*rotate_point(x,y-0.9,angle,x,y),rows=3,cols=2,row_spacing=4,angle=angle,number_array=number_array)
    # non_plated_hole(kicad_mod,*rotate_point(x-3-1.5,y,angle,x,y),d=3)
    circle(kicad_mod,*rotate_point(x-3-1.5,y,angle,x,y),d=3)
    # array
    # for yi in range(3):
        # plated_hole()
    
def plug3_2(w=56,zip=0):
    kicad_mod = new_kicad_mod(w=w, h=w,)
    x=y=w/2
    
    circle(kicad_mod,x,y,w)
    non_plated_hole(kicad_mod,x,y,19)
    
    # dy=-3
    non_plated_hole_circle(kicad_mod,x,y,8,D=41,d=3,angle=22.5)
    
    dyp=7+9.5+2.4 #18.6-13.8
    yp=y+dyp
    plug3(kicad_mod,x-3,yp)
    plug3(kicad_mod,x+3,yp,angle=180)
    
    rectline_center(kicad_mod,x-3,y-dyp,w=6, h=13.8, crosshair=0,layers=glayers_edge_pure)
    rectline_center(kicad_mod,x+3,y-dyp,w=6, h=13.8, crosshair=0,layers=glayers_edge_pure)
    
    return write_kicad_mod(kicad_mod,zip=zip)
    
def flange_bearing_outline_KFL8(kicad_mod, x, y, layers=glayers_edge_pure, angle=0,hole_func=non_plated_hole):
    q1 = [(24.00, 0.00), (23.55, 2.28), (22.26, 4.22), (20.33, 5.53), (5.06, 12.2), (4.08, 12.5), (3.09, 12.8), (2.07, 13), (1.04, 13.17), (0.00, 13.3)] #1/4特征字面量zs
    top = [(x + dx, y + dy) for dx, dy in q1] + [(x - dx, y + dy) for dx, dy in reversed(q1[:-1])] #镜像拼接上半轴线
    path = top + [rotate_point(px, py, 180, x, y) for px, py in top[1:]] #利用180度旋转闭合完整轮廓
    if angle: path = [rotate_point(px, py, angle, x, y) for px, py in path] #若存在旋转角度则整体旋转外廓
    multi_dot_line(kicad_mod, path, width=0.15, layers=layers) #生成外轮廓
    circle(kicad_mod, x, y, 26.6, layers=layers) #中央圆形凸起
    non_plated_hole(kicad_mod, x, y, 8) #中心轴承安装孔
    lx, ly = rotate_point(x - 18.25, y, angle, x, y) if angle else (x - 18.25, y) #计算左固定孔旋转后坐标
    rx, ry = rotate_point(x + 18.25, y, angle, x, y) if angle else (x + 18.25, y) #计算右固定孔旋转后坐标
    hole_func(kicad_mod, lx, ly, 5) #左固定孔
    hole_func(kicad_mod, rx, ry, 5) #右固定孔

    
def gear_rack_1m_20(gear=22,w=100,zip=0):
    kicad_mod = new_kicad_mod(w=w, h=w,)
    y=28.2
    y=w-2-47.5/2
    # y=47.5/2
    x=50
    # flange_bearing_outline_KFL8(kicad_mod,x,y)
    # return write_kicad_mod(kicad_mod, zip=zip)
    
    
    rectline_center(kicad_mod,x,y,w=111, h=47.5, crosshair=1,layers='F.Cu',width=0.2)
    rectline_center(kicad_mod,x,y,w=47.5, crosshair=1,layers='F.Cu',width=0.2)
    
    y1=y-(47.5/2+10)
    rectline_center(kicad_mod,x,y1,w=222, h=20, crosshair=1,layers='F.Cu',width=0.2)
    y1h=y1-13.5
    non_plated_hole(kicad_mod,x,y1h,6,) #上固定孔
    two_hole(kicad_mod,x,y1h,70,6,angle=0,holes=[0,1,],hole_func=non_plated_hole) #上固定孔
    y2=y1-30
    rectline_center(kicad_mod,x,y2,w=222, h=20, crosshair=1,layers='F.Cu',width=0.2)
    dx2=20/2+6
    wg=24
    rectline_center(kicad_mod,x-dx2,y2,w=wg, h=wg, crosshair=0,layers=glayers_edge_pure)
    rectline_center(kicad_mod,x-dx2,y2+wg/2,w=10, crosshair=0,layers=glayers_edge_pure)
    rectline_center(kicad_mod,x-dx2,y2+wg/2+5,w=6, crosshair=0,layers=glayers_edge_pure)
    rectline_center(kicad_mod,x+dx2,y2,w=wg, h=wg, crosshair=0,layers=glayers_edge_pure)
    rectline_center(kicad_mod,x+dx2,y2+wg/2,w=10, crosshair=0,layers=glayers_edge_pure)
    rectline_center(kicad_mod,x+dx2,y2+wg/2+5,w=6, crosshair=0,layers=glayers_edge_pure)
    
    dgr=y+20-0.2
    
    two_hole(kicad_mod,x,y,36.5,5,angle=0,holes=[0,1,],hole_func=non_plated_hole) #  8 mm 轴承座
    # two_hole(kicad_mod,x,y,36.5,4,angle=90,holes=[0,],hole_func=non_plated_hole)#竖向
    
    # non_plated_hole(kicad_mod,x,y,24) def copper_lug_shape
    flange_bearing_outline_KFL8(kicad_mod,x,y)
    
    circle(kicad_mod,x,y,27)
    rectline_center(kicad_mod,x,y,w=47.5, h=4, crosshair=1) #最长
    
    rectline_center(kicad_mod,x,dgr-5,w=200, h=10, crosshair=1)
    
    
    d=4
    M =6
    for i in range(M): # 
        xi = (i + 0.5) * (w/ M) #  直接计算第i个元件的中心X坐标
        if i in [0,5]:
            hex_nut_hole(kicad_mod,xi,dgr+d/2,7,layers=glayers_edge_pure,angle=30)
        
    two_hole(kicad_mod,x,y-4,60,6,angle=0,holes=[0,1,],hole_func=non_plated_hole) #上固定孔
    return write_kicad_mod(kicad_mod, zip=zip)

        # non_plated_hole(kicad_mod,xi,dgr+d/2,d)
            # non_plated_hole(kicad_mod,xi,dgr-10-d/2-0.5,d)
            # non_plated_hole(kicad_mod,xi,dgr+d/2,d)
        
        # if i not in [1,4]:
            # non_plated_hole(kicad_mod,xi,dgr+d+10+d/2+0.5,d)
    
    # hole_rect_center(kicad_mod,50,50,side_len_x=60,angle=0,d=6)
    
    rectline_center(kicad_mod,x,y+5,w=100, h=38, crosshair=1,layers=glayers_F_Cu)
    
    # assert dgr+d/2==50  #下 10mm 轴承座
    
    # y=100-28.2
    yb=dgr+d
    # dgr=y-20+0.2
    rectline_center(kicad_mod,x,yb+5,w=200, h=10, crosshair=1)
    
    y=yb+19.9
    two_hole(kicad_mod,x,y,45,6,angle=0,holes=[0,1,],hole_func=non_plated_hole)
    
    non_plated_hole(kicad_mod,x,y,10)
    circle(kicad_mod,x,y,30.5)
    
    return write_kicad_mod(kicad_mod, zip=zip)


def cc_voltmeter(w=100,zip=0):
    kicad_mod = new_kicad_mod(w=w, h=w,)
    
    x=w-26
    y=14
    
    cc_module(kicad_mod,x,y)
    voltmeter(kicad_mod,x,y+13.2+14.2)
    
    return write_kicad_mod(kicad_mod,zip=zip)

def cc_module(kicad_mod=None,x=0,y=0,angle=0,w=51,h=26.3,zip=0):
    ''' CC/CV（Constant Current / Constant Voltage，恒流 / 恒压） '''
    if not kicad_mod:
        assert x==y==0
        kicad_mod = new_kicad_mod(w=w,h=h,start='-w/2,-h/2')
    # w=kicad_mod.qgb_dict['w']
    # h=kicad_mod.qgb_dict['h']
    rectline_center(kicad_mod,x,y,w=w, h=h,angle=angle, crosshair=1,layers=glayers_silk)
    
    non_plated_hole_square(kicad_mod,x,y,47,h=22.3,angle=angle,d=2.5)
    
    ix=x-w/2+3.5
    ya=y-h/2
    plated_hole(kicad_mod,ix, ya+6,1.5)
    text(kicad_mod,f'I+', at=[ix+3, ya+6], size=[2,1.5], layers=glayers_silk)
    plated_hole(kicad_mod,ix, ya+11,1.5)
    
    
    ox=x-w/2+w-4
    plated_hole(kicad_mod,ox, y+h/2-6,1)# o-
    plated_hole(kicad_mod,ox, y+h/2-11,1)#o+
    text(kicad_mod,f'o+', at=[ox-3, y+h/2-11], size=[2,1.5], layers=glayers_silk)
    return write_kicad_mod(kicad_mod,zip=zip)

    
def voltmeter(kicad_mod=None,x=0,y=0,angle=0,W=47.6,H=28.4,zip=0):
    if not kicad_mod:
        assert x==y==0
        kicad_mod = new_kicad_mod(w=w,h=h,start='-w/2,-h/2')
    
    h=26
    rectline_center(kicad_mod,x,y,w=45, h=h,angle=angle, crosshair=0,layers=glayers_edge_pure)
    # rectline_center(kicad_mod,x,y,w=kicad_mod.qgb_dict['w'], h=kicad_mod.qgb_dict['h'],angle=angle, crosshair=1,layers=glayers_silk)
    rectline_center(kicad_mod,x,y,w=W,h=H,angle=angle, crosshair=1,layers=glayers_silk)
    
    
    dx=22.6/2
    ka_l=dict(width=1.6, layers=glayers_edge_pure,)
    dy=0.5  
    y1=y-h/2-dy
    multi_dot_line(kicad_mod, [[x-dx,y1],(x-dx+9,y1)],**ka_l)
    multi_dot_line(kicad_mod, [[x+dx,y1],(x+dx-9,y1)],**ka_l)
    
    y2=y+h/2+dy
    multi_dot_line(kicad_mod, [[x-dx,y2],(x-dx+9,y2)],**ka_l)
    multi_dot_line(kicad_mod, [[x+dx,y2],(x+dx-9,y2)],**ka_l)
    
    # rectline_center(kicad_mod,x,y,w=45, h=26,angle=angle, crosshair=0,layers=glayers_edge_pure)
    return write_kicad_mod(kicad_mod,zip=zip)

    
def lug_kp_charger(zip=0):
    dx=15
    dy=20
    w=dx*2+10
    h=dy*2+16
    kicad_mod = new_kicad_mod(w=w, h=h,)
    x,y=w/2,h/2
    
    angle=66
    rectline_center(kicad_mod, x, y, w=14.4, h=3.6, crosshair=1,angle=angle)
    cs=plated_hole_line(kicad_mod,x,y,pitch=3,n=4,d=0.85,size=1.4,angle=angle)#kp 整流桥


    ka=dict(mask=['F.Mask',])
    ka_l=dict( width=1, layers='F.Cu',)

    xy = copper_lug(kicad_mod,x-dx,y-dy,angle=180,**ka)
    multi_dot_line(kicad_mod, [cs[0],xy],**ka_l)

    xy = copper_lug(kicad_mod,x+dx,y-dy,angle=180,**ka)
    multi_dot_line(kicad_mod, [cs[3],xy],**ka_l) #+

    xy = copper_lug(kicad_mod,x-dx,y+dy,**ka)
    multi_dot_line(kicad_mod, [cs[1],xy],**ka_l) #ac

    xy = copper_lug(kicad_mod,x+dx,y+dy,angle=0,**ka)
    multi_dot_line(kicad_mod, [cs[2],xy],**ka_l) #ac

    
    return write_kicad_mod(kicad_mod,zip=zip)

def kart_board_shim(w=100.4,d6=3,d8=8.5, zip=0):
    kicad_mod = new_kicad_mod(w=100, h=w)
    def s20(x,y):
        rectline_center(kicad_mod, x, y, w=20, crosshair=0, layers=glayers_silk,width=1)
        hole_rect_center(kicad_mod,x,y,20,angle=0,d=1)
        
        non_plated_hole(kicad_mod, x, y,6)
    
    for x,y in  [[35, 37.9], [65, 37.9], [35, 72.4], [65, 72.4]]:  #方形中心坐标为：(50, 55.15)
        s20(x,y)
        
    for x,y in  [[35, 37.9], [65, 37.9], ]:    
        non_plated_hole(kicad_mod, x, y+1,6)
        
    two_hole(kicad_mod,50,w-40,80,4,angle=0,holes=[0,1,],hole_func=non_plated_hole,line=1) # 
    
    rectline_center(kicad_mod,50,w-40,80, crosshair=1, layers=glayers_silk,width=0.14)
    rectline_center(kicad_mod,50,w/2,w=100, crosshair=1, layers=glayers_silk,width=0.14)
    
        
    return write_kicad_mod(kicad_mod, zip=zip)
    
    
def kart_board(w=100.4,d6=3,d8=8.5, zip=0):
    kicad_mod = new_kicad_mod(w=100, h=w)
    xc = 50
    yc = w / 2
    
    # ================== 1. 外围轮廓 ==================
    rectline_center(kicad_mod, xc, yc, w=60, h=w, crosshair=1) 
    rectline_center(kicad_mod, xc,yc, w=78, h=w, crosshair=0) 
    
    
    # ================== 2. 孔位生成辅助函数 ==================
    # 标准圆孔辅助函数 (内径6mm，外丝印8.5mm)
    def hole(x, y,d=d6,s20=False):
        non_plated_hole(kicad_mod, x, y,d)
        if d==d6:circle(kicad_mod, x, y, d8)
        if s20:
            # U.get_or_set(20,[]).append([x,y])
            rectline_center(kicad_mod, x, y, w=20, h=20, crosshair=0, layers=glayers_edge_pure)

    # 长条形孔辅助函数 (增加 long 参数控制长度)
    def slot_hole(x, y,long=28,s20=False):
        d=(long-d6)/2
        if s20:ka=dict(s20=True)
        else:ka=dict(d=d6-0.01)
        hole(x,y-d,**ka)
        hole(x,y+d,d=d6-0.01)
        hole(x,y,d=3)
    
        rectline_center(kicad_mod, x, y, w=8.3, h=long-6, crosshair=1, layers=glayers_silk+glayers_F_Cu)
        d=(long-d8)/2
        circle(kicad_mod, x, y-d,d8)
        circle(kicad_mod, x, y+d,d8)
        
    # ================== 3. 极致暴力硬编码 13 孔坐标 ==================

    # 第 1 排 (2孔) - 离顶边 14mm
    hole(xc - 15, 14) 
    hole(xc + 15, 14) 

    # 第 2 排 (3孔) - 离顶边 28mm (你复测的数据)
    hole(xc - 15, 28) 
    hole(xc,      28) 
    hole(xc + 15, 28) 

    # 第 3 排 (3长条孔) - 居中 (即 yc = 50.2)。左右槽长 28mm，中间槽长 18.5mm
    c=27.6
    slot_hole(xc - 15, yc, long=c,s20=True) 
    slot_hole(xc,   yc+(c/2-18.5/2), long=18.5) 
    slot_hole(xc + 15, yc, long=c,s20=True) 

    # 第 4 排 (2孔) - 依据对称性，离底边 28mm
    hole(xc - 15, w - 28,s20=True) 
    hole(xc + 15, w - 28,s20=True) 

    # 第 5 排 (3孔) - 离底边 12.5mm (你复测的数据)
    hole(xc - 15, w - 12.5) 
    hole(xc,      w - 12.5) 
    hole(xc + 15, w - 12.5) 

    hole_rect_center(kicad_mod,xc,yc,80,60,angle=0,hole_func=hole,d=d6)
    two_hole(kicad_mod,xc,yc,80,d6,angle=0,holes=[0,1,],hole_func=non_plated_hole) #  
    two_hole(kicad_mod,xc,w-40,80,d6,angle=0,holes=[0,1,],hole_func=non_plated_hole,line=1) # 
    return write_kicad_mod(kicad_mod, zip=zip)
    
def gear_rack_1m(gear=22,w=100,zip=0):
    kicad_mod = new_kicad_mod(w=w, h=w,)
    y=28.2
    y=47.5/2
    x=50
    
    dgr=y+20-0.2
    
    two_hole(kicad_mod,x,y,36.5,5,angle=0,holes=[0,1,],hole_func=non_plated_hole) #  8 mm 轴承座
    two_hole(kicad_mod,x,y,36.5,4,angle=90,holes=[0,],hole_func=non_plated_hole)#竖向
    
    non_plated_hole(kicad_mod,x,y,24)
    circle(kicad_mod,x,y,27)
    rectline_center(kicad_mod,x,y,w=47.5, h=4, crosshair=1) #最长
    
    rectline_center(kicad_mod,x,dgr-5,w=200, h=10, crosshair=1)
    
    d=4
    M =6
    for i in range(M): # 
        xi = (i + 0.5) * (w/ M) #  直接计算第i个元件的中心X坐标
        non_plated_hole(kicad_mod,xi,dgr+d/2,d)
        
        if i in [0,5]:
            non_plated_hole(kicad_mod,xi,dgr-10-d/2-0.5,d)
        
        if i not in [1,4]:
            non_plated_hole(kicad_mod,xi,dgr+d+10+d/2+0.5,d)
    
    two_hole(kicad_mod,x,y-4,60,6,angle=0,holes=[0,1,],hole_func=non_plated_hole) #上固定孔
    hole_rect_center(kicad_mod,50,50,side_len_x=60,angle=0,d=6)
    
    rectline_center(kicad_mod,x,y+5,w=100, h=38, crosshair=1,layers=glayers_F_Cu)
    
    # assert dgr+d/2==50  #下 10mm 轴承座
    
    # y=100-28.2
    yb=dgr+d
    # dgr=y-20+0.2
    rectline_center(kicad_mod,x,yb+5,w=200, h=10, crosshair=1)
    
    y=yb+19.9
    two_hole(kicad_mod,x,y,45,6,angle=0,holes=[0,1,],hole_func=non_plated_hole)
    
    non_plated_hole(kicad_mod,x,y,10)
    circle(kicad_mod,x,y,30.5)
    
    return write_kicad_mod(kicad_mod, zip=zip)

def copper_lug_test(w=100,zip=0):
    kicad_mod = new_kicad_mod(w=w, h=w,)
    crosshair(kicad_mod,w/2,w/2,w=w*1.5,h=w*1.5,angle=45)
    r=U.set(123,[])
    for n, (x, y) in enumerate(edge_distance_turn(w,w, [10,10])):
        a=[45,135,225,315][n]
        motor_1609(kicad_mod,x,y,angle=a)
        text(kicad_mod,f'{a}', at=[x-9,y], size=[2,1.5], layers=glayers_silk)
    # for a in [0,45,135,225,315]:# range(33):
        ##a=i*0.1
        # r3=motor_1609(kicad_mod,a,0,angle=a)
        # for n,(x,y) in enumerate(r3):
            # d=min(abs(x-y),abs(y-x))
            # r.append([d,n,a])
        # text(kicad_mod,f'{a}', at=[a,5], size=[2,1.5], layers=glayers_silk)
    return write_kicad_mod(kicad_mod, zip=zip)    
    # copper_lug_shape(kicad_mod,11,11)    
    copper_lug(kicad_mod,11,11)    
    
    def generate_regular_hexagon_points(side_length=10.0):
        points = []
        # 正六边形每个内角递增 60 度，r 为中心到顶点的距离（在正六边形中，外接圆半径 r 等于边长 L）
        for i in range(6):
            angle_rad = math.radians(i * 60)
            px = side_length * math.cos(angle_rad)
            py = side_length * math.sin(angle_rad)
            # 结果保留 4 位小数避免浮点误差
            points.append([round(px, 4), round(py, 4)])
        return points

    # 得到边长 10 的正六边形局部坐标点列表：
    # [[10.0, 0.0], [5.0, 8.6603], [-5.0, 8.6603], [-10.0, 0.0], [-5.0, -8.6603], [5.0, -8.6603]]
    hex_vertices = generate_regular_hexagon_points(side_length=10.0)


    # ==========================================
    # 步骤二：精确传入各命名参数，在 (22, 22) 位置生成它
    # ==========================================
    

    THT_shape(
        kicad_mod=kicad_mod,
        path_points=hex_vertices,  # 传入刚生成的完美正六边形相对路径
        x=33,                      # 目标摆放位置 X 绝对坐标
        y=22,                      # 目标摆放位置 Y 绝对坐标
        angle=20,                   # 整体旋转角度 (0度即标准横向放置)
        slot_width=1.0,            # 1.0mm 宽的槽刀
        copper_annular=0.5,        # 环绕槽孔四周 0.5mm 的铜皮
        
    )
    
    return write_kicad_mod(kicad_mod, zip=zip)



def copper_lug(kicad_mod, x, y, angle=0,mask=['F.Mask','B.Mask']):
    w = 9
    offset = w / 2
    # 1. 处理焊盘孔：以(x,y)为中心旋转
    hole_x, hole_y = rotate_point(x, y, angle, x, y)
    plated_hole(kicad_mod, hole_x, hole_y, 3)

    # 原始局部点位（相对局部原点）
    raw_points = [
        (0 - offset, 1.5 - offset),
        (0 - offset, 12.5 - offset),
        (w - offset, 12.5 - offset),
        (w - offset, 1.5 - offset),
        (w - 2 - offset, 0.6 - offset),
        (w / 2 - offset, 0 - offset),
        (2 - offset, 0.6 - offset)
    ]
    shape_fill(kicad_mod, raw_points, x=x, y=y, layers=['F.Cu','B.Cu'],angle=angle, scale=1)
    shape_fill(kicad_mod, raw_points, x=x, y=y, layers=mask,angle=angle, scale=1)
    return x,y
    
    
def copper_lug_shape(kicad_mod, x, y, angle=0):
    '''Anderson connector copper lug'''
    w = 9
    offset = w / 2  # 原点偏移量：所有原始坐标都减去 offset
    
    THT_shape(
        kicad_mod=kicad_mod,
        # 原始路径坐标全部 - offset，原点移到 w/2, w/2
        path_points=[
            (0 - offset, 1.5 - offset),
            (0 - offset, 12.5 - offset),
            (w - offset, 12.5 - offset),
            (w - offset, 1.5 - offset),
            (w - 2 - offset, 0.6 - offset),
            (w / 2 - offset, 0 - offset),
            (2 - offset, 0.6 - offset)
        ],
        x=x,
        y=y,
        angle=angle,
        slot_width=1.0,
        copper_annular=0.5,
    )
    # 焊盘/孔坐标也统一减去 offset，保持相对位置不变
    plated_hole(kicad_mod, x,y, 3)
    hexagon_outline(kicad_mod,x,y,5.5)
    
    d = 6.2
    circle(kicad_mod, x + w/2 - offset, y + 3 + d/2 - offset, d)    
    
    # dx=4.3
    # ka=dict(type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,rotation=0,size=[2,12], drill=[1,11], )
                         
    # kicad_mod.append(Pad(number='4',at=[x-dx, y],**ka))
    # kicad_mod.append(Pad(number='4',at=[x+dx, y],**ka))
                         
    
    # kicad_mod.append(Pad(number='4', type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
                         # at=[x,y-5], size=[10, 13], drill=[9, 13], 
                         # rotation=0))                     
    

def motor_1609(kicad_mod,x,y,angle=-15):
    ''' 1200kv ￥1.8'''
    # kicad_mod = new_kicad_mod()
    non_plated_hole(kicad_mod,x,y,3.6)
    circle(kicad_mod,x=x, y=y, d=13) #
    circle(kicad_mod,x=x, y=y, d=17.4) #
    circle(kicad_mod,x=x, y=y, d=20) #
    return plated_hole_circle(kicad_mod,x,y,r=5.5,d=2,n=3,angle=angle)
    
    
def jk_BD6A24_2512(W=100, zip=0):
    # ***<module>.jk_BD6A24_2512: Failure: Different bytecode  via
    kicad_mod = new_kicad_mod(w=W, h=W,add_time=1)
    def add_2512_pad(x, y, angle=0):
        pad_w, pad_h, center_dist = 1.8, 2, 5.5
        rad = math.radians(angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        def rot(p):
            return (p[0]*cos_a - p[1]*sin_a, p[0]*sin_a + p[1]*cos_a)
        left_rel = (-center_dist/2, 0)
        right_rel = (center_dist/2, 0)
        left_abs = (x + rot(left_rel)[0], y + rot(left_rel)[1])
        right_abs = (x + rot(right_rel)[0], y + rot(right_rel)[1])
        # 公共参数字典
        # ka_dict = dict(type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, size=[pad_w, pad_h], rotation=angle, layers=['F.Cu','F.Mask','F.Paste','*.Cu','B.Cu','In1.Cu','In2.Cu'])
        ka_dict = dict(type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, size=[pad_w, pad_h], rotation=angle, layers=['F.Cu',]) #加上 ,'*.Cu','F.Mask'会导致顶底面都露铜
        pad1 = Pad(number='1', at=left_abs, **ka_dict)
        pad2 = Pad(number='2', at=right_abs, **ka_dict)
        
        rectangle_full(kicad_mod,*left_abs, w=2, h=2, layers=['F.Cu','B.Cu','In1.Cu','In2.Cu','*.Cu',]) 
        rectangle_full(kicad_mod,*right_abs, w=2, h=2, layers=['F.Cu','B.Cu','In1.Cu','In2.Cu','*.Cu',]) 
        
        kicad_mod.append(pad1)
        kicad_mod.append(pad2)
        # 在上下焊盘添加过孔（中心）
        via_params = dict(type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, size=[0.6,0.6], drill=0.3, layers=['*.Cu'])
        kicad_mod.append(Pad(number=0, at=left_abs, **via_params))
        kicad_mod.append(Pad(number=0, at=right_abs, **via_params))
        
        
    rectline_center(kicad_mod, W / 2, W / 2, w=W, h=W, crosshair=1)
    def add_pad_pair(kmod, x, y, size, pin_num, drill_screw, smt_dy=(-0.6)):
        kmod.append(Pad(number=pin_num, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT, at=[x, y], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
        kmod.append(Pad(number=pin_num, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, at=[x, y + smt_dy], size=[size[0], 1.5], drill=0, layers=['F.Cu']))
    def p15_11(x0=W / 2 - 26.0, y0=11, smt_dy=(-0.6)):
        rxy = []
        size = [1, 1]
        drill_screw = 0.9
        groups = [(x0, 15, 0), (x0 + 28.0 + 4, 11, 15)]
        dln = {}
        for start_x, pin_count, start_num in groups:
            for i in range(pin_count):
                n = start_num + i
                x = start_x + 2.0 * i
                add_pad_pair(kicad_mod, x, y0, size, f'{n}', drill_screw=drill_screw, smt_dy=smt_dy)
                rxy.append((x, y0))
        return rxy
    yb = 50
    for i in centered_range(26, center=50, pitch=3.7):
        add_pad_pair(kicad_mod, i, yb, [1, 1], f'{i + 1}', drill_screw=1)
    y11=yb-15
    two_hole(kicad_mod,50,y11,60,3,angle=0,holes=[0,1,],hole_func=non_plated_hole)
    r11 = p15_11(x0=W / 2 - 26.0, y0=y11, smt_dy=(-0.6))
    xs = centered_range(24, center=50, pitch=4)
    x24 = centered_range(14, center=29, pitch=2.4) + centered_range(10, center=65, pitch=2.4)
    x3 = centered_range(14, center=29, pitch=3) + centered_range(10, center=65, pitch=3)
    y9 = 20
    for i in range(24):
        y =y11 + y9
        add_2512_pad(xs[i], y, angle=90)
    y29=yb+15#y11 + y9 + y9
    two_hole(kicad_mod,50,y29,60,3,angle=0,holes=[0,1,],hole_func=non_plated_hole)
    # non_plated_hole(kicad_mod,50,y29+6,3)
    # two_hole(kicad_mod,50,y29,10,3,angle=90,holes=[0,1,],hole_func=non_plated_hole)
    r29 = p15_11(x0=W / 2 - 26.0, y0=y29, smt_dy=0.6)
    return write_kicad_mod(kicad_mod, zip=zip)
    
def naoh(w=100, pitch=1.15, margin=1, D=92, zip=0):
    kicad_mod = new_kicad_mod(w=w, h=w, p=pitch, m=margin)
    xz, yz = (w / 2, w / 2)
    n = 0
    x = margin
    while x <= w - margin:
        y = margin
        while y <= w - margin:
            dist = ((x - xz) ** 2 + (y - yz) ** 2) ** 0.5
            if dist < D / 2:
                non_plated_hole(kicad_mod, x, y, 0.4)
                n += 1
            y += pitch
        x += pitch
    kicad_mod.name += f'n={n}'
    text(kicad_mod, f'n={n}', at=[(-10), 50], size=[3, 2.5], layers='F.Cmts.User')
    if D > 100:
        return write_kicad_mod(kicad_mod, zip=zip)
    else:
        circle_filled(kicad_mod, xz, yz, D + 2, layers=['F.Cu', 'F.Mask'])
        return write_kicad_mod(kicad_mod, zip=zip)
def laser_array(w=100, zip=0):
    kicad_mod = new_kicad_mod(w=w, h=w)
    dx, pin_pitch = (14, 2.54)
    nx, ny_pins = (int(w // dx), 40)
    y_start = (w - (ny_pins - 1) * pin_pitch) / 2
    for i in range(nx):
        xi = w / 2 + (i - (nx - 1) / 2) * dx
        y_end = y_start + (ny_pins - 1) * pin_pitch
        for j in range(ny_pins):
            yi = y_start + j * pin_pitch
            plated_hole(kicad_mod, xi + 2.54, yi, 0.9)
            plated_hole(kicad_mod, xi - 2.54, yi, 0.9)
            if j % 3 == 0:
                plated_hole(kicad_mod, xi, yi, 1)
                rectline_center(kicad_mod, xi, yi + 2, w=14, h=7, crosshair=1)
        multi_dot_line(kicad_mod, [(xi + 2.54, y_start), (xi + 2.54, y_end)], width=1.2, layers='F.Cu', segments=10)
        multi_dot_line(kicad_mod, [(xi - 2.54, y_start), (xi - 2.54, y_end)], width=1.2, layers='B.Cu', segments=10)
    return write_kicad_mod(kicad_mod, zip=zip)
    
def laser_array(w=100, zip=0):
    kicad_mod = new_kicad_mod(w=w, h=w)
    dx, pin_pitch = 14, 2.54
    nx, ny_pins = int(w // dx), 40
    y_start = (w - (ny_pins - 1) * pin_pitch) / 2
    for i in range(nx):
        xi = (w / 2) + (i - (nx - 1) / 2) * dx
        y_end = y_start + (ny_pins - 1) * pin_pitch
        # 1. 绘制两侧连续排母孔（适配整条排母座）
        for j in range(ny_pins):
            yi = y_start + j * pin_pitch
            plated_hole(kicad_mod, xi + 2.54, yi, 0.9)
            plated_hole(kicad_mod, xi - 2.54, yi, 0.9)
            # 2. 每隔 3 针放置一个激光器：中心孔 + 丝印
            if j % 3 == 0:
                plated_hole(kicad_mod, xi, yi, 1)
                rectline_center(kicad_mod, xi, yi + 2, w=14, h=7, crosshair=1)
        # 3. 纵向并联母线：仅使用首尾两点坐标生成直线
        multi_dot_line(kicad_mod, [(xi + 2.54, y_start), (xi + 2.54, y_end)], width=1.2, layers='F.Cu',segments=10)
        multi_dot_line(kicad_mod, [(xi - 2.54, y_start), (xi - 2.54, y_end)], width=1.2, layers='B.Cu',segments=10)
    return write_kicad_mod(kicad_mod, zip=zip)
    
    
def circle8(d=0, w=100,itop=0,zip=0): # d:所有圆直径，w:正方形边长，zip:KiCAD输出参数
    if not d:
        d=-w/2 * (-1 + math.sqrt(5 - 2*math.sqrt(6)))  # 中间圆两两相切条件。
    kicad_mod = new_kicad_mod(w=w, h=w,L=itop,d=d) # 新建正方形轮廓模块
    round_rect(kicad_mod,w,w,a=4,)  # 添加圆角矩形
    r = d/2 # 计算圆半径
    # t = r + math.sqrt(2)*d - r # 推导：对角圆圆心距离√2*d，x坐标偏移=√2*d/2 + (√2*d/2 - r) = √2*d - r，保证相切
    t = r + math.sqrt( (2*r)**2 - (w/2 - r)**2 )
    
    # 8个圆坐标：4角圆+上下中+左右中，所有中间圆与相邻角圆相切
    coords = [
        (r, r), (w-r, r), # 左上、右上：角圆切正方形相邻两边
        (r, w-r), (w-r, w-r), # 左下、右下：角圆切正方形相邻两边
        (t, w/2), (w-t, w/2), # 左中、右中：与上下两个角圆相切
        (w/2, t), (w/2, w-t) # 上中、下中：与左右两个角圆相切
    ]
    
    if itop==0:
        L='B'
        dy_4p=w-1
    else:    
        L='F'
        dy_4p=1
    mask_layer=[L+'.Cu']    
    
    for x,y in coords:
        circle(kicad_mod, x=x, y=y, d=d) # 逐个绘制指定直径圆
        circle(kicad_mod, x=x, y=y, d=33.0) # 逐个绘制指定直径圆
        m4_4j(kicad_mod,x,y,angle=35,D=14.7,one_smt=mask_layer) # def m4_4j(kicad_mod
        crosshair(kicad_mod,x,y,w=33,h=33,angle=0)
        
    center=w/2
    g= (t + w/2 + r) / 3
    def d_hole(kicad_mod, x, y, ad,cd=0):
        non_plated_hole(kicad_mod, x, y,ad)
        if not cd:cd=7
        circle(kicad_mod, x, y,cd)
    hole_rect_center(kicad_mod,center,center,side_len_x=w-g*2,angle=0,d=3,cd=6,func=d_hole)
    
    
    # circle(kicad_mod, x=g, y=g,d=10)
    # circle(kicad_mod, x=w-g, y=w-g,d=10)
    
    # hole_rect_center(kicad_mod,center,center,w=w-15,h=25.4,angle=0,d=6,func=d_hole,cd=10)
    # hole_rect_center_x2(kicad_mod,center,center,w=25.4,h=w-15,angle=0,d=6,func=d_hole,cd=10)
    # hole_rect_center_x2(kicad_mod,center,center,w=28,h=w-10,angle=0,d=6,func=d_hole,cd=10)
    hole_rect_center(kicad_mod,center,center,w=w-10,h=28,angle=0,d=4.2,func=d_hole,cd=10)
    hole_rect_center(kicad_mod,center,center,w=28,h=w-10,angle=0,d=4.2,func=d_hole,cd=10,holes=[1,2])  #   1 右上角     3 左下角  0 右下角
    
    
    hole_rect_center(kicad_mod,center,center,w=95,angle=0,d=1,func=d_hole,cd=7)
    # d_hole(kicad_mod,10,center-b,6)
    d_hole(kicad_mod,center,center,10,cd=14)
    
    
    d=37
    copper_lug_shape(kicad_mod,d,93)
    copper_lug_shape(kicad_mod,w-d,93)    
    # copper_lug(kicad_mod,d,92.2)    
    # copper_lug(kicad_mod,w-d,92.2)    
    
    
    d_hole(kicad_mod,center,96,4,cd=8)
    
    return write_kicad_mod(kicad_mod, zip=zip) # 输出完成模块
    
def hole_rect_center_x2(kicad_mod,x,y,w,h,**ka):
    hole_rect_center(kicad_mod,x,y,w=w,h=h,**ka)
    hole_rect_center(kicad_mod,x,y,w=h,h=w,**ka)
    
def circle50(w=100,zip=0):
    kicad_mod = new_kicad_mod(w=w,h=w)
    t=1.6
    t=0.1
    def cir(kicad_mod,x,y,d,**ka):
        circle(kicad_mod, x=x,y=y,d=d,crosshair=0, layers=glayers_edge_pure, width=t)
        non_plated_hole(kicad_mod,x,y,9.8)
    
    cir(kicad_mod, x=25, y=25, d=50, crosshair=0, layers=glayers_edge_pure, width=t)
    cir(kicad_mod, x=75, y=25, d=50, crosshair=0, layers=glayers_edge_pure, width=t)
    d=56.2
    cir(kicad_mod, x=50, y=75-(d-50)/2, d=d, crosshair=0, layers=glayers_edge_pure, width=t)
    
    
    return write_kicad_mod(kicad_mod,zip=zip)
def hgr20_a(w=100,zip=0):
    kicad_mod = new_kicad_mod(w=w,h=w)
    x=y=w/2
    # y=17.5/2#w-17.5
    hole_rect_center(kicad_mod,x,y,side_len_x=w-10,angle=0,d=3,func=non_plated_hole)
    
    hgr20_section(kicad_mod,x,y,angle=0)    
    # netbox(kicad_mod,1,10)    
    two_hole(kicad_mod,x,y-30,70,5.9,angle=0,holes=[0,1,],hole_func=non_plated_hole)
    two_hole(kicad_mod,x,y-30,72,5.9,angle=0,holes=[0,1,],hole_func=non_plated_hole)
    two_hole(kicad_mod,x,y+30,70,5.9,angle=0,holes=[0,1,],hole_func=non_plated_hole)
    
    # rectline_center(kicad_mod,x,y,w=71,h=60,crosshair=1)    
    
    hgr20_flange_block(kicad_mod,x,y,angle=90)
    hgr20_block(kicad_mod,x,y,hole=4.9,angle=90)
    # hgr20_block(kicad_mod,x-44,y,angle=90)
    def hgr20b(x,y,holes,hole=4.9):    
        hgr20_block(kicad_mod,x,y,hole=hole,holes=holes,angle=90)
        hgr20_block(kicad_mod,x,y,hole=4.9,angle=90)
        
    # dy=20    
    # hgr20b(22,dy,holes=[1,2,])
    # hgr20b(22,w-dy,holes=[1,2,])
    
    hgr20b(x-35,y+20,holes=[1,2,])
    hgr20b(x+35,y+20,holes=[0,3,])
    # hgr20_block(kicad_mod,22,y,hole=4.9,holes=[1,2,],angle=90)
    # hgr20_block(kicad_mod,22,y,hole=2.9,angle=90)
    # hgr20_block(kicad_mod,w-22,y,hole=2.9,angle=90)
    # hgr20_block(kicad_mod,w-22,y,hole=4.9,holes=[0,3,],angle=90)
    
    mgn12c_block(kicad_mod=kicad_mod, x=x-20,y=27/2,up_rail=0.0)
    mgn12c_block(kicad_mod=kicad_mod, x=x+20,y=27/2,)
    non_plated_hole(kicad_mod,x+20,27/2,7.95)
    
    return write_kicad_mod(kicad_mod, zip=zip)
def hgr20_section(kicad_mod,x,y,angle=0):
    #截面 中心 非底面
    z=[0 ,0   ], [0 , 4.4], [3.5, 7.4], [3.5, 10.2], [0 , 13.3], [0 , 17.5],
    symmetric_x(kicad_mod,z,#HGR20
        xm=20,x0=x-10,y0=y-17.5/2,angle=angle,layers=glayers_edge,width=0.01)
    rectline_center(kicad_mod,x,y,w=20,h=17.5,angle=angle,crosshair=1)    
    return kicad_mod
    
def b3x2(w=100,zip=0):
    kicad_mod = new_kicad_mod(w=w,h=w)
    x=w/2
    y=w/2
    round_rect(kicad_mod,w,w,a=4,)  # 添加圆角矩形
    circle(kicad_mod, x, y,138)
    m=3
    d=34.5
    for i in range(m):
        xi=w/2 +(i-(m-1)/2)*(d)
        for j in range(m):
            yi=w/2 +(j-(m-1)/2)*(d)
            m4_4j(kicad_mod,xi,yi,angle=35)
            if i==2 and j==2:
                circle_filled(kicad_mod,xi,yi,8, layers=glayers_FB_Mask)
            else:    
                circle_filled(kicad_mod,xi,yi,6, layers=glayers_FB_Mask)
        # m4_4j(kicad_mod,xi,y+d/2)
        rectangle_full(kicad_mod,xi,w/3, w=15, h=50, layers=glayers_FB_Cu) 
    rectangle_full(kicad_mod,w/3,w/2+d, w=50, h=15, layers=glayers_FB_Cu) 
    
    hole_rect_center(kicad_mod,x,y,side_len_x=d,angle=0,d=6,func=non_plated_hole)
    d3=d*3-8
    hole_rect_center(kicad_mod,x,y,side_len_x=d3,h=d,angle=0,d=4,func=non_plated_hole)
    hole_rect_center(kicad_mod,x,y,side_len_x=d,h=d3,angle=0,d=4,func=non_plated_hole)
    
    for u in [-1,1]:
        x2=w/2+u*d/2
        dx=5.5
        y=1
        for xi in [x2+dx,x2-dx,]:
            kicad_mod.append(Pad(number=f'{U.ct(kicad_mod)+1}', type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, at=[xi,y], size=[1,2], layers=["F.Cu", "F.Paste", "F.Mask"]))
            rectangle_full(kicad_mod,xi,y,w=2.5, layers=['F.Cu'])  #
            plated_hole(kicad_mod,xi,y,0.95,size=1)
    return write_kicad_mod(kicad_mod, zip=zip)

def b3x3_cover(w=100,zip=0):
    kicad_mod = new_kicad_mod(w=w,h=w)
    x=w/2
    y=w/2
    d=34.5
    round_rect(kicad_mod,w,w,a=4,)  # 添加圆角矩形
    hole_rect_center(kicad_mod,x,y,side_len_x=d,angle=0,d=6,func=non_plated_hole)
    d3=d*3-8+2
    hole_rect_center(kicad_mod,x,y,side_len_x=d3,h=d,angle=0,d=4,func=non_plated_hole)
    hole_rect_center(kicad_mod,x,y,side_len_x=d,h=d3,angle=0,d=4,func=non_plated_hole)
    
    def rect(kicad_mod,x,y,d):
        rectangle_full(kicad_mod,x,y,w=10, h=50, layers=glayers_F_Cu) 
        circle_filled(kicad_mod,xi,yi,8, layers=glayers_FB_Cu)
    hole_rect_center(kicad_mod,x,y,side_len_x=d,h=d,angle=0,d=10,func=circle_filled,layers=glayers_FB_Cu)
    
    
    m=3
    for i in range(m):
        xi=w/2 +(i-(m-1)/2)*(d)
        for j in range(m):
            yi=w/2 +(j-(m-1)/2)*(d)
            circle(kicad_mod, xi,yi,[15,32,34.5])
    non_plated_hole(kicad_mod,50+d,50+d,4)
    
    return write_kicad_mod(kicad_mod, zip=zip)
    
def b3x3(w=100,zip=0,itop=0):
    kicad_mod = new_kicad_mod(w=w,h=w,itop=itop,t=U.stime()[12:20])
    x=w/2
    y=w/2
    round_rect(kicad_mod,w,w,a=4,)  # 添加圆角矩形
    circle(kicad_mod, x, y,138)
    m=3
    d=34.5
    if itop==0:
        L='B'
        # mask_layer=['B.Cu']
        dy_4p=w-1
    else:    
        L='F'
        # mask_layer=['F.Cu']
        dy_4p=1
    mask_layer=[L+'.Cu']    
        
    for i in range(m):
        xi=w/2 +(i-(m-1)/2)*(d)
        for j in range(m):
            yi=w/2 +(j-(m-1)/2)*(d)
            m4_4j(kicad_mod,xi,yi,angle=35,one_smt=False)
            kicad_mod.append(Pad(
                number=f'{i},{j}', 
                type=Pad.TYPE_SMT, 
                shape=Pad.SHAPE_CIRCLE,
                at=[xi,yi], 
                size=[9,9], 
                layers=mask_layer
            ))
            circle(kicad_mod, x=xi, y=yi, d=1, crosshair=0, layers=glayers_FB_Cu, width=8)
            
            
            if i==2 and j==2:
                circle_filled(kicad_mod,xi,yi,8, layers=glayers_FB_Mask)
            else:    
                circle_filled(kicad_mod,xi,yi,6, layers=glayers_FB_Mask)
        
        rectangle_full(kicad_mod,xi,w/3, w=15, h=50, layers=glayers_FB_Cu) 
    rectangle_full(kicad_mod,w/3,w/2+d, w=50, h=15, layers=glayers_FB_Cu) 
    
    hole_rect_center(kicad_mod,x,y,side_len_x=d,angle=0,d=6,func=non_plated_hole)
    d3=d*3-8+2
    hole_rect_center(kicad_mod,x,y,side_len_x=d3,h=d,angle=0,d=4,func=non_plated_hole)
    hole_rect_center(kicad_mod,x,y,side_len_x=d,h=d3,angle=0,d=4,func=non_plated_hole)
    
    
    xis=[w/2]
    for u in [-1,1]:
        x2=w/2+u*d#/2
        dx=5.5
        y=dy_4p
        for xi in [x2+dx,x2-dx,]:
            xis.append(xi)
    for xi in xis:    
        kicad_mod.append(Pad(number=f'{U.ct(kicad_mod)+1}', type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, at=[xi,y], size=[1,2], layers=[L+i for i in [".Cu", ".Paste", ".Mask"]],))
        rectangle_full(kicad_mod,xi,y,w=2.5, layers=[L+'.Cu'])  #
        plated_hole(kicad_mod,xi,y,0.95,size=1)
    # m=5
    # for i in range(m):
        # w/2 +(i-(m-1)/2)*(yt-3)
    
    return write_kicad_mod(kicad_mod, zip=zip)

def m12_4m10(w=100,zip=0):
    kicad_mod = new_kicad_mod(w=w,h=w)
    x=w/2
    y=w/2
    hole_rect_center(kicad_mod,x,y,side_len_x=80,angle=0,d=10,func=non_plated_hole)
    non_plated_hole(kicad_mod,x,y,12)
    
    hole_rect_center(kicad_mod,x,y,side_len_x=34.5,angle=0,d=1.18,func=m4_4j,one_smt=1)
    rectline_center(kicad_mod,x,y,w=34.5,crosshair=1)
    rectline_center(kicad_mod,x,y,w=34.5*2,crosshair=0)
    
    def d_hole(kicad_mod, x, y, ad):
        non_plated_hole(kicad_mod, x, y, ad)
        circle(kicad_mod, x, y, 10)
    
    hole_rect_center(kicad_mod,x,y,side_len_x=44,angle=45,d=4,func=d_hole)
    hole_rect_center(kicad_mod,x,y,side_len_x=64,angle=0,d=3,func=d_hole)
    
    rectangle_full(kicad_mod, x-34.5/2, y, w=15, h=50, layers=glayers_FB_Cu) 
    
    return write_kicad_mod(kicad_mod, zip=zip)
    
def m4_4j(kicad_mod=None, x=0, y=0, d=1.2, thickness=1.6, j_long=1,D=15, hole=5.8, 
          inner_delta=0, hole_func=plated_hole, add_text=False, size=6.5, angle=0,one_smt=True, **ka):
    """
    修正版：将所有组件作为一个整体绕 (x,y) 旋转 angle 度
    """
    write_kicad = not kicad_mod
    if not kicad_mod: kicad_mod = new_kicad_mod()
    
    # 1. 绘制不随角度变化的底层结构
    circle(kicad_mod, x=x, y=y, d=D, crosshair=1, layers="F.Cu", width=0.1)
    circle(kicad_mod, x=x, y=y, d=11, crosshair=0, layers="F.Cu", width=0.1)
    
    if one_smt:
        if not py.islist(one_smt):one_smt=["F.Cu"]
        kicad_mod.append(Pad(
                number=f'{x},{y}', 
                type=Pad.TYPE_SMT, 
                shape=Pad.SHAPE_CIRCLE,
                at=[x, y], 
                size=[10,10], 
                layers=one_smt
            ))
    circle(kicad_mod, x=x, y=y, d=1, crosshair=0, layers=glayers_FB_Cu, width=7+0.3)
        # circle_filled(kicad_mod,x,y,D,lceda=1)
    circle(kicad_mod, x=x, y=y, d=34.5, crosshair=0, layers=glayers_silk, width=0.1)
    
    hole_func(kicad_mod, x=x, y=y, diameter=hole, size=size)

    # 2. 旋转矩阵准备
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    def rot(dx, dy):
        """核心：计算相对于 (x,y) 偏移 (dx,dy) 的点旋转 angle 后的新绝对坐标"""
        nx = x + (dx * cos_a - dy * sin_a)
        ny = y + (dx * sin_a + dy * cos_a)
        return nx, ny

    # 3. 计算长条孔和位置参数
    r_end = D/2 - thickness/2
    r_start = r_end - j_long
    mid_r = (r_start + r_end)/2 - inner_delta
    j_long_total = thickness + j_long

    # --- 分别绘制四个 Pad (严谨对应你原始代码的 dx, dy) ---

    # [1号 - 右上] 原始偏移: dx=+d, dy=-mid_r。原始旋转: 0
    p1x, p1y = rot(d, -mid_r)
    kicad_mod.append(Pad(number='1', type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
                         at=[p1x, p1y], size=[thickness, j_long_total], drill=[thickness, j_long_total], 
                         rotation=-angle))

    # [2号 - 左下] 原始偏移: dx=-d, dy=+mid_r。原始旋转: 0
    p2x, p2y = rot(-d, mid_r)
    kicad_mod.append(Pad(number='2', type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
                         at=[p2x, p2y], size=[thickness, j_long_total], drill=[thickness, j_long_total], 
                         rotation=-angle))

    # [3号 - 左上] 原始偏移: dx=-mid_r, dy=-d。原始旋转: 90
    p3x, p3y = rot(-mid_r, -d)
    kicad_mod.append(Pad(number='3', type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
                         at=[p3x, p3y], size=[j_long_total, thickness], drill=[j_long_total, thickness], 
                         rotation=-angle))

    # [4号 - 右下] 原始偏移: dx=+mid_r, dy=+d。原始旋转: 90
    p4x, p4y = rot(mid_r, d)
    kicad_mod.append(Pad(number='4', type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
                         at=[p4x, p4y], size=[j_long_total, thickness], drill=[j_long_total, thickness], 
                         rotation=-angle))

    # --- 分别绘制四个辅助孔 (必须也通过 rot 函数旋转) ---
    d0 = 1.1
    
    # 右上孔: dx=d0, dy=-r_start
    h1x, h1y = rot(d0, -r_start)
    hole_func(kicad_mod, x=h1x, y=h1y, diameter=thickness)
    
    # 左下孔: dx=-d0, dy=r_start
    h2x, h2y = rot(-d0, r_start)
    hole_func(kicad_mod, x=h2x, y=h2y, diameter=thickness)
    
    # 左上孔: dx=-r_start, dy=-d0
    h3x, h3y = rot(-r_start, -d0)
    hole_func(kicad_mod, x=h3x, y=h3y, diameter=thickness)
    
    # 右下孔: dx=r_start, dy=d0
    h4x, h4y = rot(r_start, d0)
    hole_func(kicad_mod, x=h4x, y=h4y, diameter=thickness)

    return write_kicad_mod(kicad_mod, zip=1) if write_kicad else kicad_mod



def single_m4_4j(d=33.9, hole=33.9,d_screw=4,margin=4, zip=0):
    """绘制单个圆模块（居中显示）"""
    
    kicad_mod = new_kicad_mod()
    center=15

    rectangle_full(kicad_mod, center, center, w=30, h=15, layers=glayers_FB_Cu) 
    w, h = 30, 15
    cut = 5  # 切除距离 # 定义八边形顶点（切除四个角后的矩形）
    oct_pts = [
        [w/2, h/2 - cut],    # 右下 1 (垂直边起点)
        [w/2 - cut, h/2],    # 右下 2 (水平边起点)
        
        [-w/2 + cut, h/2],   # 左下 1
        [-w/2, h/2 - cut],   # 左下 2
        
        [-w/2, -h/2 + cut],  # 左上 1
        [-w/2 + cut, -h/2],  # 左上 2
        
        [w/2 - cut, -h/2],   # 右上 1
        [w/2, -h/2 + cut]    # 右上 2
    ]
    polygon_full(kicad_mod, center, center + 20, oct_pts, layers=glayers_FB_Cu, angle=0)
    
    # 调用核心函数
    # m4_4j(kicad_mod, center, center, )
    # m4_4j_angle(kicad_mod, center+20, center,angle=45)
    
    return write_kicad_mod(kicad_mod, zip=zip)
    
    # 1x1 布局，模块大小直接设为 d（或者根据 hole 自定义）
    mod_size = d  +margin*2
    kicad_mod = new_kicad_mod(w=mod_size, h=mod_size,d=d_screw)
    center = mod_size / 2  # 模块物理中心
    
    # 1. 添加辅助中心孔（保留原有的 5 个参考孔逻辑，坐标设为中心）
    dh = d - 3 
    def d_hole(kicad_mod, x, y, ad):
        non_plated_hole(kicad_mod, x, y, ad)
        circle(kicad_mod, x, y, 10)
    
    # 如果只需要最中心的一个孔，可以只保留 center, center 这一行
    # d_hole(kicad_mod, center, center, 5.9)     # 核心中心孔
    hole_rect_center(kicad_mod,center,center,side_len_x=d-3,angle=0,d=d_screw,func=d_hole)
    
    # 2. 铜箔区域修改（改为覆盖中心区域）
    # 原代码中 w=20, h=66 是针对 2x2 布局的，这里改为适配单个模块
    rectangle_full(kicad_mod, center, center, w=15, h=15, layers=glayers_FB_Cu) 

    # 3. 绘制单个 M4 连接器结构
    # 直接使用原 func_d_list 中的参数配置
    # ka = dict(
        # d=1.2, 
        # thickness=1.6, 
        # j_long=1, 
        # hole_func=plated_hole, 
        # hole=5.8, 
        # size=6.5,
        # inner_delta=0.1
    # )
    
    # 在中心位置绘制
    circle(kicad_mod, center, center, hole, layers="F.SilkS", width=0.02)
    circle_filled(kicad_mod, center, center, 20, layers=glayers_FB_Mask)
    
    # 调用核心函数
    m4_4j(kicad_mod, center, center, )
    m4_4j_angle(kicad_mod, center+20, center,angle=45)
    # 4. 添加标注并输出
    text(kicad_mod, f"1x1_d={d}", at=[center, mod_size + 5], size=[3, 2.5], layers="F.Cmts.User")
    return write_kicad_mod(kicad_mod, zip=zip)
    
def pb230(h=206-2,z=0):
    kicad_mod=new_kicad_mod(w=230,h=h,edge_layers=glayers_silk)
    # jk
    for n,(i,d) in enumerate({
    2:0.8,
    2.54:0.8,
    5:1,
    10:2}.items()):
        y=n* (h/4)
        for xi in range(4):
            x=xi* (230/4)
            di=d+(xi*d/16)
            perfboard(kicad_mod,w=50,h=48,x=2.5+x,y=y,interval=i,d=di,size=di*1.2)
    return write_kicad_mod(kicad_mod, zip=z)    

def perfboard(kicad_mod=None, w=100, h=100, x=0, y=0, interval=2.54, d=1, size=1.2, zip=0):
    """
    创建多孔板(洞洞板)封装（左上角原点）
    
    参数:
    kicad_mod: 现有的KiCad模块对象（可选）
    w: 板子宽度(mm)
    h: 板子高度(mm)
    x, y: 左上角原点坐标(默认0,0)
    interval: 孔间距(默认2.54mm)
    d: 孔径(默认1mm)
    size: 焊盘大小(直径, 默认1.2mm)
    zip: 是否压缩输出(默认0)
    
    返回: KicadMod对象
    """
    # 计算孔的行列数
    cols = math.floor(w / interval) + 1
    rows = math.floor(h / interval) + 1
    
    # 创建或使用现有的封装对象
    write_kicad = False
    if kicad_mod is None:
        # 创建新封装，参考文本位置在左上角下方
        kicad_mod = new_kicad_mod(text_at=[x + w/2, y - 2], w=w, h=h,i=interval,d=d)
        write_kicad = True
    
    # 添加孔阵列（从左上角开始）
    for col in range(cols):
        for row in range(rows):
            pad_x = x + col * interval
            pad_y = y + row * interval
            
            # 添加焊盘
            kicad_mod.append(Pad(
                number="",  # 洞洞板不需要引脚号
                type=Pad.TYPE_THT,
                shape=Pad.SHAPE_CIRCLE,
                at=[pad_x, pad_y],
                size=[size, size],
                drill=d,
                layers=Pad.LAYERS_THT
            ))
    
    # 如果需要保存封装
    if write_kicad:
        return write_kicad_mod(kicad_mod, zip=zip)
    else:
        return kicad_mod
        
def draw_trapezoid(kicad_mod, x, y, long_side, short_side, h, angle, layers, 
                  width=1.6, sides=[0,1,2,3],**ka):
    """
    在指定位置绘制旋转梯形
    
    参数:
    kicad_mod: KiCad模块对象
    x, y: 长边中点坐标
    long_side: 长边长度
    short_side: 短边长度
    h: 梯形高度
    angle: 旋转角度(度)
    layers: 绘图层
    width: 线宽(默认1.6)
    sides: 需要绘制的边列表 [0,1,2,3] 分别对应:
        0: 长边（底边）
        1: 右侧斜边
        2: 短边（顶边）
        3: 左侧斜边
        默认绘制所有四条边
    segments: 曲线分段数(默认10)
    """
    # 将角度转换为弧度
    angle_rad = math.radians(angle)
    
    # 计算旋转前的四个顶点坐标
    # 长边端点
    long_left = (x - long_side/2, y)
    long_right = (x + long_side/2, y)
    
    # 短边端点
    short_left = (x - short_side/2, y + h)
    short_right = (x + short_side/2, y + h)
    
    # 旋转所有点
    points = [long_left, long_right, short_right, short_left]
    rotated_points = []
    
    for point in points:
        # 计算相对于旋转中心(x,y)的偏移量
        dx = point[0] - x
        dy = point[1] - y
        
        # 应用旋转矩阵
        new_x = x + dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
        new_y = y + dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
        
        rotated_points.append((new_x, new_y))
    
    # 定义四条边
    edges = [
        (rotated_points[0], rotated_points[1]),  # 长边（底边） - 边0
        (rotated_points[1], rotated_points[2]),  # 右侧斜边 - 边1
        (rotated_points[2], rotated_points[3]),  # 短边（顶边） - 边2
        (rotated_points[3], rotated_points[0])   # 左侧斜边 - 边3
    ]
    
    # 绘制选定的边
    for edge_idx in sides:
        if 0 <= edge_idx < 4:
            start, end = edges[edge_idx]
            multi_dot_line(
                kicad_mod,
                dots=[start, end],
                layers=layers,
                width=width,**ka
            )

def b4x6(rows=4, itop=0, m6=6, zip=0, margin=1.5, cuw=15,cud=9):
    """创建4行6列紧密排列的圆形阵列，直径34.5mm"""
    d =41.5# 34.5  # 圆形直径
    cols = 6  # 列数改为6
    d,cols=34.5,6
    d,cols=41.5,6
    
    spacing = d  # 圆形中心间距等于直径（紧密排列）
    total_width = cols * spacing + 2 * margin  # 计算阵列总尺寸
    total_height = rows * spacing + 2 * margin  # 计算阵列总尺寸
    start_x = margin + spacing / 2  # 起始X位置
    start_y = margin + spacing / 2  # 起始Y位置
    
    kicad_mod = new_kicad_mod(w=total_width, h=total_height, itop=itop, time=U.stime()[12:20])  # 创建新模块
    round_rect(kicad_mod, total_width, total_height, a=5,sides=[1,2])  # 添加圆角矩形
    cx = total_width / 2
    cy = total_height / 2
    rectline_center(kicad_mod, cx, cy, cols * spacing, rows * spacing)  # 原始方形
    
    # 创建电池阵列
    for row in range(rows):
        for col in range(cols):
            x = start_x + col * spacing
            y = start_y + row * spacing
            circle(kicad_mod, x, y, diameter=d, layers=glayers_silk)  # 创建圆形
            circle(kicad_mod, x, y, diameter=20, layers=glayers_silk)  # 创建圆形
            # if col==0:
                # circle_filled(kicad_mod, x, y+0.25, cuw-1, layer=glayers_FB_Cu, lceda=1)  # 创建填充圆
            kicad_mod.append(Pad(
                number=f'{row}-{col}', 
                type=Pad.TYPE_SMT, 
                shape=Pad.SHAPE_CIRCLE,
                at=[x, y], 
                size=[cud,cud], 
                layers=glayers_F_Cu
            ))
            # circle_filled(kicad_mod, x, y, cuw*2, layer=glayers_FB_Cu, lceda=zip)  # 创建填充圆
            # if not zip:kicad_mod.append(KicadModTree.Circle(center=[x, y], radius=1, layer='F.Cu', width=cuw - 4))
            m4_4j(kicad_mod, x, y, d=1.2, thickness=1.6, j_long=1, 
                  hole_func=plated_hole, hole=5.8, size=6.5,angle=35)  # M4连接器
            # plated_hole(kicad_mod, x, y, 5.8, size=6, shape=Pad.SHAPE_CIRCLE)  # 额外镀锡孔
    
    # 添加非镀金孔 - 内部阵列
    for row in range(rows - 1):  # 行索引0到3（共3行孔）
        for col in range(cols - 1):  # 列索引0到5（共5列孔）
            x_hole = start_x + (col + 0.5) * spacing
            y_hole = start_y + (row + 0.5) * spacing
            non_plated_hole(kicad_mod, x_hole, y_hole, m6)
    
    de = 3 + margin
    # 上下边缘的孔
    for y in [de, total_height - de]:
        for x in [start_x + (col + 0.5) * spacing for col in range(cols - 1)]:
            non_plated_hole(kicad_mod, x, y, 4)
    # 左右边缘的孔
    for x in [de, total_width - de]:
        for y in [start_y + (row + 0.5) * spacing for row in range(rows - 1)]:
            non_plated_hole(kicad_mod, x, y, 4)
    # 四个角落的孔
    for n, (x, y) in enumerate(edge_distance_turn(total_width, total_height, [de - 0.3, de - 0.3])):
        non_plated_hole(kicad_mod, x, y, 4)
    
    # 电气连接部分 - 调整为4行6列结构
    n12=[[2,4,6, 12,10,8, 14,16,18, 24,22,20]
         ,[3,5,11,9,15,17,23,21,]]
    for row_group in range(rows  ):  # 处理行组：0,1,2（共3组）
        for col_group in range(0, cols - itop*2, 2):  # 处理列组：0,2,4
            x_center = (col_group + itop + 0.5) * spacing+ start_x  # 保持相同的计算方式
            y_center = start_y+ (row_group + 0.5) * spacing  - spacing/2
            dr = spacing / 2 - 1
            w = spacing + cuw+2
            h = cuw
            # 添加连接片
            # cut = 3  # 切除距离 # 定义八边形顶点（切除四个角后的矩形）
            # oct_pts = [
                # [w/2, h/2 - cut],    # 右下 1 (垂直边起点)
                # [w/2 - cut, h/2],    # 右下 2 (水平边起点)
                
                # [-w/2 + cut, h/2],   # 左下 1
                # [-w/2, h/2 - cut],   # 左下 2
                
                # [-w/2, -h/2 + cut],  # 左上 1
                # [-w/2 + cut, -h/2],  # 左上 2
                
                # [w/2 - cut, -h/2],   # 右上 1
                # [w/2, -h/2 + cut]    # 右上 2
            # ]
            # polygon_full(kicad_mod, x_center,y_center, oct_pts, layers=glayers_FB_Cu, angle=0)
    
            
            rectangle_full(kicad_mod, x_center, y_center, w=w, h=h, layers=glayers_FB_Cu)
            text(kicad_mod, f'{n12[itop][U.ct(kicad_mod)]}', at=[x_center - 5, y_center], 
                 size=[8, 4], layers=glayers_silk)
    
    # 特殊孔位
    if itop == 1:
        ph = 4.9
        dx=-4  # 保持相同的偏移量
        dy=18
        if spacing==41.5:dy=spacing/2
        
        copper_lug(kicad_mod,-1,dy,angle=90,mask=['F.Mask'])    
        copper_lug(kicad_mod,-1,total_height-dy,angle=90,mask=['F.Mask'])    
        
        # plated_hole(kicad_mod, dx, dy, ph, size=ph + 2)
        # plated_hole(kicad_mod, dx, total_height - dy, ph, size=ph + 2)
        # d2=7
        # rectangle_full(kicad_mod, dx+d2,dy+d2, w=7, h=20,layers=glayers_FB_Cu,angle=45+90)  #上
        # rectangle_full(kicad_mod, dx+d2,total_height-dy-d2, w=7, h=20,layers=glayers_FB_Cu,angle=45)  # 下
        
        cx =margin+spacing * 0.5 - 1
        cy= margin+spacing * 0.5-3  #-2齐平
        multi_dot_line(kicad_mod,[(dx,dy),(cx,dy)],width=9,layers=glayers_FB_Cu,segments=0) #
        multi_dot_line(kicad_mod,[(dx,total_height-dy),(cx,total_height-dy)],width=9,layers=glayers_FB_Cu,segments=0) #
        
        
        w = cuw
        h = spacing + cuw+2
        we = cuw+4
        # 调整矩形位置以适应4x6布局
        rectangle_full(kicad_mod, cx,cy, w=we, h=we, layers=glayers_FB_Cu)  # 左开始
        rectangle_full(kicad_mod, cx, total_height-cy, w=we, h=we, layers=glayers_FB_Cu)  # 左结束
        
        cx = margin + spacing * 0.5
        # 调整竖向连接片位置
        rectangle_full(kicad_mod, total_width - cx, start_y+spacing *0.5, w=w, h=h, layers=glayers_FB_Cu)  # 右竖向
        rectangle_full(kicad_mod, total_width - cx,start_y+spacing *2.5, w=w, h=h, layers=glayers_FB_Cu)  # 右竖向（第3行

        
        h = spacing + cuw+2-4
        # rectangle_full(kicad_mod, cx,start_y+spacing *1.5, w=w, h=h, layers=glayers_FB_Cu)  # 左竖向
        cut = 5  # 切除距离 # 定义八边形顶点（切除四个角后的矩形）
        oct_pts = [
                [w/2, h/2 - cut],    # 右下 1 (垂直边起点)
                [w/2 - cut, h/2],    # 右下 2 (水平边起点)
                
                [-w/2 + cut, h/2],   # 左下 1
                [-w/2, h/2 - cut],   # 左下 2
                
                [-w/2, -h/2 + cut],  # 左上 1
                [-w/2 + cut, -h/2],  # 左上 2
                
                [w/2 - cut, -h/2],   # 右上 1
                [w/2, -h/2 + cut]    # 右上 2
            ]
        polygon_full(kicad_mod,cx,start_y+spacing *1.5,oct_pts, layers=glayers_FB_Cu, angle=0)
    
        
        #def rectangle_full(kicad_mod, dx,dy, w=7, h=20,layers=glayers_FB_Cu,angle=45)  # 左
        # multi_dot_line(kicad_mod,[(-1,total_height+1),(total_width+1,total_height+1)],width=1.2,layers=glayers_edge_pure,segments=10)  #
# 在(5, 5)位置绘制梯形，长边10mm，短边6mm，高8mm，旋转30度
    t=20
    draw_trapezoid(
        kicad_mod=kicad_mod,
        x=0,
        y=total_height/2,
        long_side=total_height,
        short_side=77,
        h=t,
        angle=90,
        layers=glayers_edge_pure,
        width=0.254,
        sides=[1,2,3]
    )
    
    two_hole(kicad_mod,-2,total_height/2,64,4,angle=90,holes=[0,1,],hole_func=circle)#,func=0 force reload   
    # multi_dot_line(kicad_mod,[(-t,total_height/2),(-t+17.5,total_height/2)],width=0.254,layers=glayers_F_Cu)  #
    
    
    m=12+itop
    m=14
    # 计算起始y坐标
    yt=8
    if spacing==41.5:yt=9.6
    start_y = (total_height - (m-1) * yt) / 2
    real=[
[4,2,6,'', 10,12,8 , 18,14,16,'', 20,24,22],#[2,4,6, 12,10,8, 14,16,18, 24,22,20]
[1,3,5,7,9,11,13,15,17,19,21,23,25,'+'],# U.range(1,m+1),    
    ]
    for i in range(m):
        if not real[itop][i]:continue
        x1 = -3
        y1 = start_y + i * yt
        text(kicad_mod,f'{real[itop][i]}', at=[x1+3,y1], size=[4,2.5], layers=glayers_silk,)
        if itop==1 and i in [0,m-1]:                
            kicad_mod.append(Pad(number=f'{i}', type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, at=[x1+3, y1], size=[2,1], layers=["F.Cu", "F.Paste", "F.Mask"]))
            # pass
        else:    
            kicad_mod.append(Pad(number=f'{i}', type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, at=[x1, y1], size=[2,1], layers=["F.Cu", "F.Paste", "F.Mask"]))
            rectangle_full(kicad_mod,x1,y1 ,w=3,h=3, layers=['F.Cu'])  #
            plated_hole(kicad_mod,x1,y1,0.95,size=1)
        
        
        # kicad_mod.append(KicadModTree.Circle(center=[x1,y1], radius=1, layer='F.Cu', width=3))
        
        yh = total_height/2 +(i-(m-1)/2)*(yt-1)
        # for k in range(5):
            # non_plated_hole(kicad_mod,x1-6-(0.25*k),yh,1.5)
        dn=2    
        non_plated_hole(kicad_mod,x1-6,yh,dn)
        non_plated_hole(kicad_mod,x1-6.25,yh,dn)
        non_plated_hole(kicad_mod,x1-12,total_height/2 +(i-(m-1)/2)*(yt-3),dn)
        non_plated_hole(kicad_mod,x1-12.25,total_height/2 +(i-(m-1)/2)*(yt-3),dn)
        # non_plated_hole(kicad_mod,-7.25,yh,1.5)
        # non_plated_hole(kicad_mod,-7.5,yh,1.5)
        
        # ya = total_height/2 +(i - (m-1)/2)*3
        # multi_dot_line(kicad_mod,[(-20,ya),(-8,yh)],segments=10,width=1.6,layers=glayers_edge_pure)
        
        text(kicad_mod,f'{real[itop][i]}', at=[x1-5,yh], size=[2,1.5], layers=glayers_silk,)
    
    return write_kicad_mod(kicad_mod, zip=zip)

def b3x8(rows=3, itop=0, m6=6, zip=0, margin=1.5, cuw=20):
    """创建3行8列紧密排列的圆形阵列，直径34.5mm"""
    d = 34.5  # 圆形直径
    cols = 8  # 列数
    spacing = d  # 圆形中心间距等于直径（紧密排列）
    total_width = cols * spacing + 2 * margin  # 计算阵列总尺寸
    total_height = rows * spacing + 2 * margin  # 计算阵列总尺寸
    start_x = margin + spacing / 2  # 起始X位置
    start_y = margin + spacing / 2  # 起始Y位置
    
    kicad_mod = new_kicad_mod(w=total_width, h=total_height, itop=itop, time=U.stime()[12:20])  # 创建新模块
    round_rect(kicad_mod, total_width, total_height, a=5)  # 添加圆角矩形 def round_rect
    cx = total_width / 2
    cy = total_height / 2
    rectline_center(kicad_mod, cx, cy, cols * spacing, rows * spacing)  # 原始方形
    
    # 创建电池阵列
    for row in range(rows):
        for col in range(cols):
            x = start_x + col * spacing
            y = start_y + row * spacing
            circle(kicad_mod, x, y, diameter=d, layers=glayers_silk)  # 创建圆形
            circle_filled(kicad_mod, x, y, cuw - 8, layer=glayers_FB_Cu, lceda=zip)  # 创建填充圆
            if not zip:
                kicad_mod.append(KicadModTree.Circle(center=[x, y], radius=1, layer='F.Cu', width=cuw - 4))
            m4_4j(kicad_mod, x, y, d=1.2, thickness=1.6, j_long=1, 
                  hole_func=plated_hole, hole=5.8, size=6.5)  # M4连接器
            plated_hole(kicad_mod, x, y, 5.8, size=6, shape=Pad.SHAPE_CIRCLE)  # 额外镀锡孔
    
    # 添加非镀金孔 - 内部阵列
    for row in range(rows - 1):  # 行索引0到1（共2行孔）
        for col in range(cols - 1):  # 列索引0到6（共7列孔）
            x_hole = start_x + (col + 0.5) * spacing
            y_hole = start_y + (row + 0.5) * spacing
            non_plated_hole(kicad_mod, x_hole, y_hole, m6)
    
    de = 3 + margin
    # 上下边缘的孔
    for y in [de, total_height - de]:
        for x in [start_x + (col + 0.5) * spacing for col in range(cols - 1)]:
            non_plated_hole(kicad_mod, x, y, 4)
    # 左右边缘的孔
    for x in [de, total_width - de]:
        for y in [start_y + (row + 0.5) * spacing for row in range(rows - 1)]:
            non_plated_hole(kicad_mod, x, y, 4)
    # 四个角落的孔
    for n, (x, y) in enumerate(edge_distance_turn(total_width, total_height, [de - 0.3, de - 0.3])):
        non_plated_hole(kicad_mod, x, y, 4)
    
    # 电气连接部分 - 调整为3行结构
    for row_group in range(2):  # 仅处理奇数行组：0
        for col_group in range(0, cols-itop-itop, 2):  # 仅处理奇数列组：0, 2, 4, 6
            x_center =(col_group+itop+1)*spacing # + (col_group + 0.5 - itop) *spacing
            y_center = start_y + (row_group + 0.5) * spacing
            dr = spacing / 2 - 1
            w = 2 * dr + cuw
            h = cuw
            rectangle_full(kicad_mod, x_center, y_center - dr, w=w, h=h, layers=glayers_FB_Cu)
            rectangle_full(kicad_mod, x_center, y_center + dr, w=w, h=h, layers=glayers_FB_Cu)
            text(kicad_mod, f'{U.ct(kicad_mod) + 1}', at=[x_center - 5, y_center], 
                 size=[8, 4], layers=['F.SilkS'])
    
    # 特殊孔位
    if itop == 1:
        ph = 4.9
        dx=dy=4#37.5
        plated_hole(kicad_mod,dx,dy, ph, size=ph + 2)
        plated_hole(kicad_mod,total_width-dx, total_height-dy, ph, size=ph + 2)
		        
        w=cuw
        h = 2 * dr + cuw
        
        cx=margin+spacing*0.5-1
        we=26
        rectangle_full(kicad_mod,cx,            spacing*0.5, w=we, h=we, layers=glayers_FB_Cu) #左开始
        rectangle_full(kicad_mod,total_width-cx,total_height-spacing*0.5, w=we, h=we, layers=glayers_FB_Cu)
        
        cx=margin+spacing*0.5
        rectangle_full(kicad_mod, total_width-cx,spacing*1, w=w, h=h, layers=glayers_FB_Cu) # 右竖向
        rectangle_full(kicad_mod, cx,            spacing*2, w=w, h=h, layers=glayers_FB_Cu)#左竖向
	
    return write_kicad_mod(kicad_mod, zip=zip)

def jk_BD6A24_bottom(W=73,zip=0):
    kicad_mod = new_kicad_mod(w=73,h=17.5,add_time=1)
    yh5=9
    non_plated_hole(kicad_mod,W-4.5,yh5,3)  
    non_plated_hole(kicad_mod,4.5,yh5,3)  
    
    rectline_center(kicad_mod,W-4.5,1,9,2,layers=glayers_edge_pure)  # 左->右
    rectline_center(kicad_mod,W-(10+4.7),2.7,11,5.6,layers=glayers_edge_pure)  # 左->右
    rectline_center(kicad_mod,8,1,16,2,layers=glayers_edge_pure)  # 右->左
    rectline_center(kicad_mod,22.3,2.4,10,5.6,layers=glayers_edge_pure)  # 镜像
    
    x0,y0=W-10.5,9.3  # 起始坐标(镜像后)
    size=[1,1]  # 焊盘尺寸
    drill_screw=0.9  # 钻孔直径
    
    def add_pad_pair(kmod,x,y,pin_num):  # 添加一对焊盘的内部函数
        kmod.append(Pad(number=pin_num,type=Pad.TYPE_THT,shape=Pad.SHAPE_RECT,at=[x,y],size=size,drill=drill_screw,layers=Pad.LAYERS_THT))  # 通孔焊盘
        kmod.append(Pad(number=pin_num,type=Pad.TYPE_SMT,shape=Pad.SHAPE_RECT,at=[x,y-0.6],size=[1,1.5],drill=0,layers=["F.Cu"]))  # 表面贴装焊盘

    # 定义引脚组: (起始x坐标, 引脚数量, 起始编号) - 已镜像
    groups = [
        (x0, 15, 0),  # 第一组:15针, 起始x=W-10.5
        (x0-2.0*14-2.5-1.5, 11, 15)  # 第二组:11针, 起始x=第一组结束-间隔
    ]
    
    dln={}
    # 遍历所有引脚组
    for start_x, pin_count, start_num in groups:
        for i in range(pin_count):
            n = start_num + i  # 当前引脚编号
            x = start_x - 2.0*i  # 当前引脚x坐标(镜像后从右向左)
            add_pad_pair(kicad_mod,x,y0,f"{n}")  # 添加焊盘对
            
            # 根据引脚编号奇偶性绘制不同方向的线
            layer=['F.Cu',('User.1','In1.Cu'),('User.2','In2.Cu'),'B.Cu'][(n//2)%4]
            if py.istuple(layer):layer=layer[zip]
            if layer in dln:dln[layer]+=0.5
            else:dln[layer]=1.3
            dy=dln[layer]
            dy=1.2
            
            if n%2==1 and n not in [25]:
                dy=0.9
                multi_dot_line(kicad_mod,[(x,y0),(x,y0+dy)],width=1,layers=layer)  # 奇数引脚
            else:
                multi_dot_line(kicad_mod,[(x,y0),(x,y0-dy)],width=1,layers=layer)  # 偶数引脚
    
    multi_dot_line(kicad_mod,[(0,17.8),(W,17.8)],segments=10,width=1.6,layers=glayers_edge_pure)
    return write_kicad_mod(kicad_mod,zip=zip)  # 写入文件

def smt_array(n=12,spacing1=6,spacing2=2.54, spacing_y=3, width=1.0, height=1.5,h2=1, zip=0):  # spacing1: 第一排x间距, spacing2: 第二排x间距, spacing_y: y方向排间距
    """双排SMT焊盘阵列：上排用spacing1，下排用spacing2，垂直间距spacing_y，整体X居中于(0,0)"""
    w1 = (n - 1) * spacing1 if n > 1 else 0  # 上排总宽
    w2 = (n - 1) * spacing2 if n > 1 else 0  # 下排总宽
    total_width = max(w1, w2)  # 取最大宽度用于居中
    total_height=spacing_y + height*2
    kicad_mod = new_kicad_mod(w=total_width+4, h=total_height,start=[-total_width/2-2,total_height/2],spacing1=spacing1,spacing2=spacing2) #自动绘制 外框（包围所有焊盘）
    start_x1 = -w1 / 2  # 上排起始x（居中）0#
    start_x2 = -w2 / 2  # 下排起始x（居中）6*(spacing1-spacing2)#
    y1 = total_height-spacing_y / 2    # x排y
    y2 =total_height+ spacing_y / 2  # 下排y
    
    itop0=[9,5,1, 10,6,2,  3,7,11, 4,8,12]
    real=['4', '5', '12', '3', '6', '11', '10', '7', '2', '9', '8', '1']
    if n==13:
        itop0=U.range(n) # -{itop0[i]}
        real=[5,13, 4,6,12, 11,3,7, 10,8,2, 9,1]
    
    for i in range(n):
        pin_num = i + 1
        x1 = start_x1 + i * spacing1  # 上排x
        x2 = start_x2 + i * spacing2  # 下排x
        
        mid_n=abs(pin_num-6)
        kicad_mod.append(Pad(number=f'{real[i]}-{pin_num}', type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, at=[x1, y1], size=[width, height], layers=["F.Cu", "F.Paste", "F.Mask"]))
        
        text(kicad_mod,f'{real[i]}', at=[x1,y1+3], size=[3,2], layers=glayers_silk,)
        # kicad_mod.append(Pad(number=f'{spacing2}-{pin_num}',type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, at=[x2, y2], size=[width,h2], layers=["F.Cu", "F.Paste", "F.Mask"]))
        
        # multi_dot_line(kicad_mod, [[x1, y1 - height/2+mid_n*0.25], [x2, y2-h2/2+0.1]], layers=["F.Cu"], width=0.15)
    return write_kicad_mod(kicad_mod, zip=zip)
    
    
def hole_array(W=100,zip=0):
    kicad_mod = new_kicad_mod(w=0,h=66,add_time=1)
    round_trapezoid(kicad_mod,150,100,70)                    
    return write_kicad_mod(kicad_mod,zip=zip)  # 写入文件
    
    n=0
    for y in range(6):
        for x in range(10):
            non_plated_hole(kicad_mod,5+x*10,y*10,0.8+n*0.1)
            n+=1
def jk_BD6A24_up(W=73,zip=0):
    kicad_mod = new_kicad_mod(w=73,h=17.5,add_time=1)
    yh5=9
    non_plated_hole(kicad_mod,4.5,yh5,3)
    non_plated_hole(kicad_mod,W-4.5,yh5,3)
    
    rectline_center(kicad_mod,4.5,1,9,2,layers=glayers_edge_pure)  #左
    rectline_center(kicad_mod,10+4.7,2.7,11,5.6,layers=glayers_edge_pure)  #左
    rectline_center(kicad_mod,W-8,1,16,2,layers=glayers_edge_pure)  #右
    rectline_center(kicad_mod,W-22.3,2.4,10,5.6,layers=glayers_edge_pure)  #
    
    x0,y0=10.5,9.3  # 起始坐标(第一pin x
    size=[1,1]  # 焊盘尺寸
    drill_screw=0.9  # 钻孔直径
    
    def add_pad_pair(kmod,x,y,pin_num):  # 添加一对焊盘的内部函数
        kmod.append(Pad(number=pin_num,type=Pad.TYPE_THT,shape=Pad.SHAPE_RECT,at=[x,y],size=size,drill=drill_screw,layers=Pad.LAYERS_THT))  # 通孔焊盘
        kmod.append(Pad(number=pin_num,type=Pad.TYPE_SMT,shape=Pad.SHAPE_RECT,at=[x,y-0.6],size=[1,1.5],drill=0,layers=["F.Cu"]))  # 表面贴装焊盘

    # 定义引脚组: (起始x坐标, 引脚数量, 起始编号)
    groups = [
        (x0, 15, 0),  # 第一组:15针, 起始x=x0, 引脚编号0-14
        (x0+2.0*14+2.5+1.5, 11, 15)  # 第二组:11针, 起始x=第一组结束+间隔, 引脚编号15-25
    ]
    
    dln={}
    # 遍历所有引脚组
    for start_x, pin_count, start_num in groups:
        for i in range(pin_count):
            n = start_num + i  # 当前引脚编号
            x = start_x + 2.0*i  # 当前引脚x坐标
            add_pad_pair(kicad_mod,x,y0,f"{n}")  # 添加焊盘对
            
            # 根据引脚编号奇偶性绘制不同方向的线
            # dy=2+n/2
            layer=['F.Cu',('User.1','In1.Cu'),('User.2','In2.Cu'),'B.Cu'][(n//2)%4]
            if py.istuple(layer):layer=layer[zip]
            if layer in dln:dln[layer]+=0.5
            else:dln[layer]=1.3
            dy=dln[layer]
            dy=1.2
            
            if n%2==1 and n not in [25]:
                dy=0.9
                multi_dot_line(kicad_mod,[(x,y0),(x,y0+dy)],width=1,layers=layer)  # 奇数引脚 12
            else:
                multi_dot_line(kicad_mod,[(x,y0),(x,y0-dy)],width=1,layers=layer)  # 偶数引脚 14
    
    multi_dot_line(kicad_mod,[(0,17.8),(W,17.8)],segments=10,width=1.6,layers=glayers_edge_pure)
    return write_kicad_mod(kicad_mod,zip=zip)  # 写入文件
    
def jk_BD6A24(W=73,zip=0):
    kicad_mod = new_kicad_mod(w=73,h=100)  #
    x=73/2
    
    non_plated_hole(kicad_mod,5,5,4)
    non_plated_hole(kicad_mod,W-5,5,4)
    
    
    
    return write_kicad_mod(kicad_mod, zip=zip) 
    
def box_header_254(kicad_mod=None, pins=16, rows=2, mount_holes=True, add_text=False):
    """
    创建2.54mm间距牛角插座封装
    :param kicad_mod: KiCad模块对象
    :param pins: 总引脚数
    :param rows: 行数 (1或2)
    :param angle: 插座角度 (0=直插, 90=直角)
    :param mount_holes: 是否添加安装孔
    :param add_text: 是否添加文本标签
    :return: KiCad模块对象
    """
    write_kicad = not kicad_mod
    if not kicad_mod: kicad_mod = new_kicad_mod()
    
    # 基本参数
    pitch = 2.54  # 引脚间距
    pad_size = [1, 1.6]  # 焊盘尺寸
    drill_size = 0.9  # 钻孔尺寸
    pin_rows = pins // rows  # 每行引脚数
    
    # 计算封装尺寸
    width = (pin_rows - 1) * pitch
    height = (rows - 1) * pitch
    
    
    # 创建引脚
    for row in range(rows):
        for col in range(pin_rows):
            pin_num = row * pin_rows + col + 1
            
            # 计算位置
            x = col * pitch
            y = row * pitch
            
            # 添加焊盘
            kicad_mod.append(Pad(
                number=pin_num,
                type=Pad.TYPE_THT,
                shape=Pad.SHAPE_RECT,
                layers=Pad.LAYERS_THT,
                at=[x, y],
                size=pad_size,
                drill=drill_size,
                rotation=0
            ))
    
    # 添加安装孔（如果需要）
    if mount_holes:
        mount_hole_dia = 2.0  # 安装孔直径
    
    # 添加丝印层轮廓
    outline_margin = 0.5
    outline_points = [
        [-pitch - outline_margin, -pitch - outline_margin],
        [width + pitch + outline_margin, -pitch - outline_margin],
        [width + pitch + outline_margin, height + pitch + outline_margin],
        [-pitch - outline_margin, height + pitch + outline_margin],
        [-pitch - outline_margin, -pitch - outline_margin]
    ]
    
    for i in range(len(outline_points) - 1):
        kicad_mod.append(Line(
            start=outline_points[i],
            end=outline_points[i+1],
            layer="F.SilkS",
            width=0.12
        ))
    
    # 添加文本标签（如果需要）
    if add_text:
        text_pos = [width/2, height + pitch + 1.5]
        kicad_mod.append(Text(
            text=f"{pins}P {rows}x{pin_rows}",
            at=text_pos,
            layer="F.SilkS",
            size=[1, 1]
        ))
    
    return write_kicad_mod(kicad_mod, zip=1) if write_kicad else kicad_mod    

def mgn12c_rail_2block(kicad_mod=None, cx=0, y=0, wm=34.7, W=100,cut_rail_outline=True, zip=0):
    """创建MGN12C导轨安装模块（包含三角形支架和方块）"""
    # create_new = not kicad_mod
    # if not kicad_mod:
        # kicad_mod = new_kicad_mod(w=W, h=W)
    
    # ===== 三角形支架部分 ====
    hm = 27  # 滑块高度 原名hm_triangle
    # wm_triangle = 34.7  # 滑块宽度
    dh = 50 - 12.5 - hm  # 计算孔位置偏移量
    
    x0 = cx - wm/2  # 使三角形支架中心对齐指定xmid
    
    # cx, cy = x0 + wm/2,
    cy=y + hm/2  # 中心点坐标(x,y)
    
    # 导轨安装孔（向下分布）
    yr = hm + dh  # dh 孔距滑块下边缘
    for i in [-2, -1,2,3]:
        circle(kicad_mod, cx, y+yr+i*25, 3)  # 向上每隔25mm一个丝印
    for i in range(2):  # 0,1,2,3
        non_plated_hole(kicad_mod, cx, y+yr+i*25,2.9)  # 向下每隔25mm一个孔
        
    x2b=cx-wm/2+5
    for x2 in [x2b,x2b+20.8,x2b+21,]:  #cx+wm/2-5    
        non_plated_hole(kicad_mod,x2, 50+25/2,2.9)  # 验证
        non_plated_hole(kicad_mod,x2, 50-25/2,2.9)  # 验证
    
    
    # 闭合外框轮廓（顺时针方向）
    # multi_dot_line(kicad_mod, [
        # (x0, y),            # 左上角起点
        # (x0, y+hm),         # 向下移动到左下角
        # (cx-6, y+hm),       # 滑块边缘导轨 
        # (cx-6, y+100),      # 向右下移动到三角形左顶点
        # (cx+6, y+100),      # 向右移动到三角形右顶点
        # (cx+6, y+hm),       # 滑块边缘导轨 
        # (x0+wm, y+hm), # 向右下移动到右下角
        # (x0+wm, y), # 向上移动到右上角
        # (x0, y)             # 向左移动回起点 - 闭合
    # ], width=1.01, layers=glayers_edge_pure, segments=100)
    
    mgn12c_block(kicad_mod=kicad_mod, x=cx, y=hm/2, wm=wm)
    mgn12c_block(kicad_mod=kicad_mod, x=cx, y=W-hm/2, wm=wm)# 添加方块
    
    if not cut_rail_outline:return
    wa=1.6/2
    wa=0
    multi_dot_line(kicad_mod, [
        (x0+wa, y+hm+wa),        
        (cx-6-wa, y+hm+wa),       
        (cx-6-wa, W-hm-wa),      
        (x0+wa, W-hm-wa),      
        (x0+wa, y+hm+wa),     
    ], width=wa*2, layers=glayers_edge_pure, segments=100)

    multi_dot_line(kicad_mod, [
        (x0+wm-wa, y+hm+wa),         
        (cx+6+wa, y+hm+wa),       
        (cx+6+wa, W-hm-wa),    
        (x0+wm-wa, W-hm-wa),      
        (x0+wm-wa, y+hm+wa),     
    ], width=wa*2, layers=glayers_edge_pure, segments=100)
    
    
    # return write_kicad_mod(kicad_mod, zip=zip) if create_new else kicad_mod    
    
    
def mgn12c_rail_2block_3(W=100,zip=0):
    kicad_mod = new_kicad_mod(w=W,h=W)  #
    
    wm=34.7
    dx=(wm*3-100)/2
    x_spacing=35 #34.5+3
    # x=dx+50-x_spacing
    x=35/2
    mgn12c_rail_2block(kicad_mod,x,0,cut_rail_outline=0)
    x=x+x_spacing #dx+50
    mgn12c_rail_2block(kicad_mod,x,0)
    x=x+x_spacing#dx+50+x_spacing
    mgn12c_rail_2block(kicad_mod,x,0)
    
    round_rect(kicad_mod, W,W,a=3)  # 添加圆角矩形
    round_rect(kicad_mod,35,W,a=2.4,width=1.6)  # def round_rect(
    
    hm=27
    xru=35
    non_plated_hole(kicad_mod,xru,hm/2,2.9)  # 验证
    for xr in [xru-25,xru,xru+25,xru+25*2]:
        non_plated_hole(kicad_mod,xr,hm/2,0.9)  # 验证
        
    # ka=dict(dh=50-12.5-27)
    # mgn12c_rail_triangle(kicad_mod,xmid,y,**ka)
    # ka={}
    # xmid+=34.7/2
    # mgn12c_block(kicad_mod,xmid,W-hm/2,**ka)
    return write_kicad_mod(kicad_mod, zip=zip)
    
    
    
def b6x8(rows=6, itop=0, m6=6, zip=0, margin=1.5,cuw=20):
    """创建6行8列紧密排列的圆形阵列，直径34.5mm"""
    d = 34.5  # 圆形直径
    cols = 8  # 列数
    spacing = d  # 圆形中心间距等于直径（紧密排列）
    total_width = cols * spacing + 2 * margin  # 计算阵列总尺寸
    total_height = rows * spacing + 2 * margin  # 计算阵列总尺寸
    start_x = margin + spacing / 2  # 起始X位置
    start_y = margin + spacing / 2  # 起始Y位置
    
    kicad_mod = new_kicad_mod(w=total_width, h=total_height, itop=itop,time=U.stime()[12:20])  # 创建新模块
    round_rect(kicad_mod, total_width, total_height, a=5)  # 添加圆角矩形
    cx=total_width/2
    cy=total_height/2
    rectline_center(kicad_mod,cx,cy,cols*spacing,rows*spacing,)  #原始方形
    
    for row in range(rows):
        for col in range(cols):
            x = start_x + col * spacing
            y = start_y + row * spacing
            circle(kicad_mod, x, y, diameter=d, layers=glayers_silk)  # 创建圆形
            circle_filled(kicad_mod, x, y,cuw-8, layer=glayers_FB_Cu, lceda=zip)  # 创建填充圆
            if not zip:kicad_mod.append(KicadModTree.Circle(center=[x,y],radius=1, layer='F.Cu',width=cuw-4))
            # kicad_mod.append(KicadModTree.Circle(center=[x,y],radius=1, layer='F.Cu',width=10))
            m4_4j(kicad_mod, x, y, d=1.2, thickness=1.6, j_long=1, hole_func=plated_hole, hole=5.8,size=6.5)  # M4连接器
            plated_hole(kicad_mod, x, y, 5.8, size=6, shape=Pad.SHAPE_CIRCLE)  # 额外镀锡孔
    
    for row in range(rows - 1):  # 行索引0到4（共5行孔）
        for col in range(cols - 1):  # 列索引0到6（共7列孔）
            x_hole = start_x + (col + 0.5) * spacing  # 计算孔位置（在4个圆的中心）
            y_hole = start_y + (row + 0.5) * spacing  # 计算孔位置（在4个圆的中心）
            non_plated_hole(kicad_mod, x_hole, y_hole, m6)  # 添加非镀金孔
    
    de=3+margin
    # xes=[de]+  + [total_width-de]
    for y in [de,total_height-de]:  # 上下最外侧
        for x in [start_x+(col+0.5)*spacing for col in range(cols-1)]:
            non_plated_hole(kicad_mod,x,y,4)
    for x in [de,total_width-de]:  # 左右最外侧    
        for y in [start_y +(row+0.5)* spacing for row in range(rows-1)]:  # 4顶点 xes 已经给出
            non_plated_hole(kicad_mod, x, y, 4)
    for n,(x,y) in enumerate(edge_distance_turn(total_width,total_height,[de-0.3,de-0.3])): #        
        non_plated_hole(kicad_mod, x, y, 4)
    
    for row_group in range(0, rows - 1, 2):  # 仅处理奇数行组：0, 2, 4
        for col_group in range(0, cols + itop * 2, 2):  # 仅处理奇数列组：0, 2, 4, 6
            x_center = start_x + (col_group + 0.5 - itop) * spacing  # 中心位置X
            y_center = start_y + (row_group + 0.5) * spacing  # 中心位置Y
            dr=spacing/2-1
            w =2*dr + cuw  # 矩形宽度
            h =cuw#  22-2  # 矩形高度
            if itop == 1 and col_group in [0, cols]: h = 30  # 特殊列调整高度
            rectangle_full(kicad_mod, x_center, y_center -dr, w=w, h=h, layers=glayers_FB_Cu)  # 上方矩形铜皮
            rectangle_full(kicad_mod, x_center, y_center +dr, w=w, h=h, layers=glayers_FB_Cu)  # 下方矩形铜皮
            rectangle_full(kicad_mod, x_center -dr, y_center, w=h, h=w, layers=glayers_FB_Cu)  # 左侧矩形铜皮
            rectangle_full(kicad_mod, x_center +dr, y_center, w=h, h=w, layers=glayers_FB_Cu)  # 右侧矩形铜皮
            text(kicad_mod,f'{U.ct(kicad_mod)+1}', at=[x_center-5,y_center], size=[8,4], layers=['F.SilkS'],)
    if itop == 1:
        ph=4.9
        plated_hole(kicad_mod,6,37.5,ph,size=ph+2)
        plated_hole(kicad_mod,total_width-6,total_height-37.5,ph,size=ph+2)
    return write_kicad_mod(kicad_mod, zip=zip)  # 生成最终模块
    
def hex_nut_hole(kicad_mod=None, x=0, y=0, across_flats=5.5, angle=0, layers=glayers_edge_pure, crosshair=False):
    """
    创建六边形螺母孔零件
    across_flats: 六边形平行边距离(对边距离/Across Flats)
    """
    write_kicad = not kicad_mod
    if not kicad_mod: kicad_mod = new_kicad_mod()
    
    # 计算外接圆半径 (顶点到中心的距离)
    circumradius = across_flats / math.sqrt(3)  # 正确的外接圆半径
    
    # 计算六边形顶点
    dots = []
    for i in range(6):
        # 计算顶点的角度 (30度偏移使平边在顶部)
        theta = math.radians(30 + angle + i * 60)
        # 计算顶点坐标
        dots.append((x + circumradius * math.cos(theta), 
                     y + circumradius * math.sin(theta)))
    # 闭合多边形(添加第一个点)
    dots.append(dots[0])
    
    # 绘制六边形轮廓
    polyline(kicad_mod, dots, layers=layers, width=0.15)
    
    # 十字标记
    if crosshair:
        cs = across_flats * 0.15  # 十字标记尺寸
        polyline(kicad_mod, [(x - cs, y), (x + cs, y)], layers=layers, width=0.1)
        polyline(kicad_mod, [(x, y - cs), (x, y + cs)], layers=layers, width=0.1)
    
    if write_kicad: return write_kicad_mod(kicad_mod, zip=0)
    return kicad_mod
    
    
def m4_14(kicad_mod=None, x=0, y=50,angle=0,base_hole_x=5.5/2,hole=3):
      #base_hole_x=5.5/2 # 孔在0度时的X偏移
    write_kicad = not kicad_mod  # 是否写入文件标志
    if not kicad_mod: kicad_mod = new_kicad_mod()  # 创建新模块
    # 计算旋转中心(始终为(x,y)，但元素位置会根据角度变化)
    center = (x, y)  # 固定旋转中心为(x,y)
    # 计算0度时的元素位置(相对于旋转中心)
    base_center_x = 7  # 矩形中心在0度时的X偏移
    # 创建旋转后的孔(基于旋转中心)
    hole_pos = rotate_point(x + base_hole_x, y, angle, *center)
    non_plated_hole(kicad_mod, *hole_pos, hole)  # 非镀金孔
    # 创建旋转后的圆(基于旋转中心)
    circle_pos = rotate_point(x + base_center_x, y, angle, *center)
    circle(kicad_mod, *circle_pos, 4)  # 圆
    # 创建旋转矩形(基于旋转中心)
    rect_pos = rotate_point(x + base_center_x, y, angle, *center)
    rectline_center(kicad_mod, *rect_pos, 14, angle=angle)  # 14mm正方形
    if write_kicad: return write_kicad_mod(kicad_mod, zip=1)  # 返回模块文件
    return kicad_mod  # 返回模块对象
def mgn12c_bottom_gear(w=100, zip=0):
    kicad_mod = new_kicad_mod(w=w, h=w)
    wm = 34.7
    hm = 27
    dx = 5.85
    ka = dict(up_rail=2.5)
    mgn12c_block(kicad_mod, wm / 2 - dx, hm / 2, **ka)
    mgn12c_block(kicad_mod, 100 - wm / 2 + dx, hm / 2, angle=180, **ka)
    mgn12c_block(kicad_mod, wm / 2 - dx, 100 - hm / 2, **ka)
    mgn12c_block(kicad_mod, 100 - wm / 2 + dx, 100 - hm / 2, angle=180, **ka)
    dcube = 5
    dy = 12.5
    non_plated_hole(kicad_mod, dcube, 50 + dy, 2.9)
    rectline_center(kicad_mod, dcube, 50 + dy, 10)
    non_plated_hole(kicad_mod, dcube, 50 - dy, 2.9)
    rectline_center(kicad_mod, dcube, 50 - dy, 10)
    non_plated_hole(kicad_mod, 100 - dcube, 50 + dy, 2.9)
    rectline_center(kicad_mod, 100 - dcube, 50 + dy, 10)
    non_plated_hole(kicad_mod, 100 - dcube, 50 - dy, 2.9)
    rectline_center(kicad_mod, 100 - dcube, 50 - dy, 10)
    n = 4
    W, x0, y0 = (100, 50, 50)
    R = 35
    non_plated_hole(kicad_mod, x0, y0, 7.9)
    circle(kicad_mod, x0, y0, d=2 * R, crosshair=0, layers=glayers_Cmts)
    for i in range(4):
        angle = i * (2 * math.pi / 4)
        x, y = (x0 + R * math.cos(angle), y0 + R * math.sin(angle))
        circle(kicad_mod, x, y, d=17)
        non_plated_hole(kicad_mod, x, y, 5.9)
        text(kicad_mod, f'{i}', at=[x - 6, y], size=[2, 1.6], layers=glayers_silk)
    x0 = y0 = w / 2
    return write_kicad_mod(kicad_mod, zip=zip)
   
def mgn12c_bottom_m6(w=100, hole=43, bear_hole=5.9, zip=0):
    kicad_mod = new_kicad_mod(w=w, h=w, d=hole, b=bear_hole)
    wm = 34.7
    hm = 27
    dx = 5.85
    ka = dict(up_rail=2.5)
    mgn12c_block(kicad_mod, wm / 2 - dx, hm / 2, **ka)
    mgn12c_block(kicad_mod, 100 - wm / 2 + dx, hm / 2, angle=180, **ka)
    mgn12c_block(kicad_mod, wm / 2 - dx, 100 - hm / 2, **ka)
    mgn12c_block(kicad_mod, 100 - wm / 2 + dx, 100 - hm / 2, angle=180, **ka)
    dcube = 5
    dy = 12.5
    non_plated_hole(kicad_mod, dcube, 50 + dy, 2.9)
    rectline_center(kicad_mod, 7, 50, 14)
    non_plated_hole(kicad_mod, dcube, 50 - dy, 2.9)
    non_plated_hole(kicad_mod, 100 - dcube, 50 + dy, 2.9)
    non_plated_hole(kicad_mod, 100 - dcube, 50 - dy, 2.9)
    n = 4
    W, x0, y0 = (100, 50, 50)
    R = 35
    circle(kicad_mod, x0, y0, d=2 * R, crosshair=1)
    non_plated_hole(kicad_mod, x0, y0, hole)
    for i in range(4):
        angle = i * 1.5708
        x, y = (x0 + R * math.cos(angle), y0 + R * math.sin(angle))
        circle(kicad_mod, x, y, d=17)
        if i == 0:
            circle(kicad_mod, x, y, d=25)
        non_plated_hole(kicad_mod, x, y, bear_hole)
        text(kicad_mod, f'{i}', at=[x - 6, y], size=[2, 1.6], layers=glayers_silk)
    text(kicad_mod, f'n=4,d=49.5,D={2 * R}', at=[x - 40, (-10)], size=[4, 3], layers=glayers_Cmts)
    x, y = (x0 + R, y0)
    step_motor_42(kicad_mod, *rotate_point(x + 12.5, y, 0, x, y), d=5, angle=45)
    return write_kicad_mod(kicad_mod, zip=zip)
   
   
def mgn12c_z_board_m6(n=4,**ka):
    g2=2**0.5
    #return mgn12c_z_board(n=4,d=35*g2,hex_a=7.9,angle_offset=0,**ka)
    return mgn12c_z_board(n=4,d=35*g2,hex_a=0,hole=5.9,angle_offset=0,**ka)

def mgn12c_z_board(n=10,d=24.12,hex_a=4.45,hole=3,bear_hole=8.9,angle_offset=18, zip=0):
    W = 100
    kicad_mod = new_kicad_mod(w=W, h=W,n=n,d=d) # 创建 KiCad 模块
    r = d / 2 # 小圆半径
    r2=5
    R = r / math.sin(math.pi / n) # 计算中心圆半径
    D = 2 * R # 计算中心圆直径
    Ri = R - r # 内切圆半径
    Ri2 = R - r2 # 内切圆半径
    Di2=D-r2*2
    if n == 0:
        return None
    x0,y0 = W/2, W/2
    non_plated_hole(kicad_mod,x0,y0,9.9)
    xd=29/2
    non_plated_hole(kicad_mod,x0-xd,y0,4) #moto
    non_plated_hole(kicad_mod,x0+xd,y0,4) #moto
    non_plated_hole(kicad_mod,x0,y0,17.4)
                    
    kicad_mod.append(Circle(center=[x0,y0], radius=R, layer='F.SilkS', width=0.15)) # 添加中心圆参考
    kicad_mod.append(Circle(center=[x0,y0], radius=Ri, layer='F.SilkS', width=0.15)) # 添加内切圆
    circle(kicad_mod, x0,y0,d=Di2) # 添加内切圆
    theta = 2 * math.pi / n # 计算角度增量
    for i in range(n):
        angle =i*theta + math.radians(angle_offset)  # 角度偏移转换为弧度
        x = x0 + R * math.cos(angle) # 小圆中心 x
        y = y0 + R * math.sin(angle) # 小圆中心 y
        circle(kicad_mod, x, y, d=r) # 添加小圆
        # non_plated_hole(kicad_mod,x,y,2.9)
        if hex_a:hex_nut_hole(kicad_mod,x,y,hex_a,layers=glayers_edge_pure,)
        non_plated_hole(kicad_mod,x,y,hole)
        text(kicad_mod,f'{i}', at=[x-6,y], size=[2,1.6], layers=glayers_silk,)
        
        
        
    text(kicad_mod,f'n={n},d={d},D={D},Di={Ri*2},Di2={Di2}', at=[x-40,-10], size=[4,3], layers=glayers_Cmts,)    
        
    # n=2
    # R=28
    # theta = 2 * math.pi / n # 计算角度增量
    # for i in range(n):    
        # angle=i*theta+math.radians(-90)
        # x = x0 + R* math.cos(angle)
        # y = y0 + R* math.sin(angle)
        # non_plated_hole(kicad_mod,x,y,1)
    # n=10
    # R=30
    # theta = 2 * math.pi / n # 计算角度增量
    # for i in range(n):    
        # angle=i*theta+math.radians(0)
        # x = x0 + R* math.cos(angle)
        # y = y0 + R* math.sin(angle)
        # non_plated_hole(kicad_mod,x,y,1)
        # circle(kicad_mod, x, y, d=2.9)
    
    
    crosshair(kicad_mod,x0,y0,w=W,h=W)
    

    wm=34.7
    hm=27
    
    dcube=5#5.5/2
    dy=25/2
    non_plated_hole(kicad_mod,dcube,50+dy,2.9)
    non_plated_hole(kicad_mod,dcube,50-dy,2.9)
    non_plated_hole(kicad_mod,100-dcube,50+dy,2.9)
    non_plated_hole(kicad_mod,100-dcube,50-dy,2.9)
        
    non_plated_hole(kicad_mod, 50+dy, dcube, 2.9)       # 交换了 dcube 和 50+dy
    non_plated_hole(kicad_mod, 50-dy, dcube, 2.9)       # 交换了 dcube 和 50-dy
    non_plated_hole(kicad_mod, 50+dy, 100-dcube, 2.9)   # 交换了 100-dcube 和 50+dy
    non_plated_hole(kicad_mod, 50-dy, 100-dcube, 2.9)   # 交换了 100-dcube 和 50-dy
    
    
    rectline_center(kicad_mod,5+4,hm/2,8,12,layers=glayers_edge_pure)
    rectline_center(kicad_mod,5+4,100-hm/2,8,12,layers=glayers_edge_pure)
    rectline_center(kicad_mod,100-(5+4),hm/2,8,12,layers=glayers_edge_pure)
    rectline_center(kicad_mod,100-(5+4),100-hm/2,8,12,layers=glayers_edge_pure)
    
    hd=10.1
    rectline_center(kicad_mod,5,hm/2,hd,hm,layers=glayers_edge_pure)
    rectline_center(kicad_mod,100-5,hm/2,hd,hm,layers=glayers_edge_pure)
    rectline_center(kicad_mod,5,100-hm/2,hd,hm,layers=glayers_edge_pure)
    rectline_center(kicad_mod,100-5,100-hm/2,hd,hm,layers=glayers_edge_pure)
    
    return write_kicad_mod(kicad_mod, zip=zip) # 返回模块
def mgn12c_z_board_m6(n=4, **ka):
    g2 = 1.4142135623730951
    return mgn12c_z_board(n=4, d=35 * g2, hex_a=0, hole=5.9, angle_offset=0, **ka)
def mgn12c_z_board(n=10, d=24.12, hex_a=4.45, hole=3, bear_hole=8.9, angle_offset=18, zip=0):
    W = 100
    kicad_mod = new_kicad_mod(w=W, h=W, n=n, d=d)
    r = d / 2
    r2 = 5
    R = r / math.sin(math.pi / n)
    D = 2 * R
    Ri = R - r
    Ri2 = R - r2
    Di2 = D - r2 * 2
    if n == 0:
        return
    else:
        x0, y0 = (W / 2, W / 2)
        non_plated_hole(kicad_mod, x0, y0, 9.9)
        xd = 14.5
        non_plated_hole(kicad_mod, x0 - xd, y0, 4)
        non_plated_hole(kicad_mod, x0 + xd, y0, 4)
        non_plated_hole(kicad_mod, x0, y0, 17.4)
        kicad_mod.append(Circle(center=[x0, y0], radius=R, layer='F.SilkS', width=0.15))
        kicad_mod.append(Circle(center=[x0, y0], radius=Ri, layer='F.SilkS', width=0.15))
        circle(kicad_mod, x0, y0, d=Di2)
        theta = 2 * math.pi / n
        for i in range(n):
            angle = i * theta + math.radians(angle_offset)
            x = x0 + R * math.cos(angle)
            y = y0 + R * math.sin(angle)
            circle(kicad_mod, x, y, d=r)
            if hex_a:
                hex_nut_hole(kicad_mod, x, y, hex_a, layers=glayers_edge_pure)
            non_plated_hole(kicad_mod, x, y, hole)
            text(kicad_mod, f'{i}', at=[x - 6, y], size=[2, 1.6], layers=glayers_silk)
        text(kicad_mod, f'n={n},d={d},D={D},Di={Ri * 2},Di2={Di2}', at=[x - 40, (-10)], size=[4, 3], layers=glayers_Cmts)
        crosshair(kicad_mod, x0, y0, w=W, h=W)
        wm = 34.7
        hm = 27
        dcube = 5
        dy = 12.5
        non_plated_hole(kicad_mod, dcube, 50 + dy, 2.9)
        non_plated_hole(kicad_mod, dcube, 50 - dy, 2.9)
        non_plated_hole(kicad_mod, 100 - dcube, 50 + dy, 2.9)
        non_plated_hole(kicad_mod, 100 - dcube, 50 - dy, 2.9)
        non_plated_hole(kicad_mod, 50 + dy, dcube, 2.9)
        non_plated_hole(kicad_mod, 50 - dy, dcube, 2.9)
        non_plated_hole(kicad_mod, 50 + dy, 100 - dcube, 2.9)
        non_plated_hole(kicad_mod, 50 - dy, 100 - dcube, 2.9)
        rectline_center(kicad_mod, 9, hm / 2, 8, 12, layers=glayers_edge_pure)
        rectline_center(kicad_mod, 9, 100 - hm / 2, 8, 12, layers=glayers_edge_pure)
        rectline_center(kicad_mod, 91, hm / 2, 8, 12, layers=glayers_edge_pure)
        rectline_center(kicad_mod, 91, 100 - hm / 2, 8, 12, layers=glayers_edge_pure)
        hd = 10.1
        rectline_center(kicad_mod, 5, hm / 2, hd, hm, layers=glayers_edge_pure)
        rectline_center(kicad_mod, 95, hm / 2, hd, hm, layers=glayers_edge_pure)
        rectline_center(kicad_mod, 5, 100 - hm / 2, hd, hm, layers=glayers_edge_pure)
        rectline_center(kicad_mod, 95, 100 - hm / 2, hd, hm, layers=glayers_edge_pure)
        return write_kicad_mod(kicad_mod, zip=zip)

def mgn12c_block_up_rail_x(w=100,h=32.2,zip=0):
    ''' 拼板 '''
    kicad_mod=new_kicad_mod(w=w,h=h,edge_layers=glayers_Cmts)
    hm=27
    y=h-hm/2
    wm=34.7
    # y0=(h-3*hm)
    dx=w/3
    x0=dx/2
    mgn12c_block(kicad_mod,x0,y,up_rail=4.75,angle=180)
    mgn12c_block(kicad_mod,x0+dx*1,y,up_rail=4.75)
    mgn12c_block(kicad_mod,x0+dx*2,y,up_rail=4.75)
    # mgn12c_block(kicad_mod,x,dy*4,up_rail)=1)
    multi_dot_line(kicad_mod,[(dx,-1),(dx,h+2)],width=1.6,layers=glayers_edge_pure)
    multi_dot_line(kicad_mod,[(dx*2,-1),(dx*2,h+2)],width=1.6,layers=glayers_edge_pure)
    
    yc=h-hm-0.8
    multi_dot_line(kicad_mod,[(-1,yc),(101,yc)],width=1.6,segments=2,layers=glayers_edge_pure)
    for x in range(1,99,1):
        plated_hole(kicad_mod,x,h-hm-0.4,0.6)
    
    
    return write_kicad_mod(kicad_mod, zip=zip)

def fs100p():
    # 尺寸计算
    min_x, max_x = -24.13984, 30.86016
    min_y, max_y = -12.0926, 12.1074
    W, H = max_x - min_x, max_y - min_y
    
    # W=26.2# 实际测量大小
    # H=11.4 #22.5
    # kicad_mod = new_kicad_mod(w=W, h=H,edge_layers=glayers_Cmts,start=[-23.8,-11.3])#start=[-W/2-18,-H/2-5])
    
    W=50.5# 实际测量大小
    H=22.6
    kicad_mod = new_kicad_mod(w=W, h=H,edge_layers=glayers_Cmts,start=[-24.14,-11.3])

    
    
    
    # 参考标记
    ref_x, ref_y = 3.36016, -12.0926
    kicad_mod.append(Text(type="reference", text="REF-fs100p", at=[ref_x, ref_y], layer="F.SilkS", size=[1,1], thickness=0.15))
    
    # 值标记
    val_x, val_y = 3.36016, 12.1074
    kicad_mod.append(Text(type="value", text="fs100p", at=[val_x, val_y], layer="F.Fab", size=[1,1], thickness=0.15))
    
    # 丝印线条 (关键轮廓)
    silk_lines = [
        [-24.13984, -11.2926, 26.36016, -11.2926], [-24.13984, -8.8726, -21.59984, -8.8726],
        [-24.13984, 8.9074, -24.13984, -8.8726], [-24.13984, 8.9074, -21.59984, 8.9074],
        [-24.13984, 11.3074, -24.13984, -11.2926], [-24.13984, 11.3074, 26.36016, 11.3074],
        [-21.59984, 8.9074, -21.59984, -8.8726], [19.05985, -11.17, 24.13985, -11.17],
        [19.05985, -8.63, 19.05985, -11.17], [19.05985, -8.63, 24.13985, -8.63],
        [19.05985, 8.63, 24.13985, 8.63], [19.05985, 11.17, 19.05985, 8.63],
        [19.05985, 11.17, 24.13985, 11.17], [24.13985, -8.63, 24.13985, -11.17],
        [24.13985, 11.17, 24.13985, 8.63], [26.36016, -7.9926, 30.86016, -7.9926],
        [26.36016, 8.0074, 30.86016, 8.0074], [26.36016, 11.3074, 26.36016, -11.2926],
        [30.86016, 8.0074, 30.86016, -7.9926]
    ]
    # silk_lines=[]
    for line in silk_lines:
        kicad_mod.append(Line(start=line[:2], end=line[2:], layer="F.SilkS", width=0.2))
    
    # 焊盘定义 (简化为圆形，保持位置和孔径)
    pad_size = 1.5  # 焊盘直径
    drill_size = 0.9  # 钻孔直径
    pads = [
        (1, -22.86984, 7.6374, 90), (2, -22.86984, 5.0974, 90), (3, -22.86984, 2.5574, 90),
        (4, -22.86984, 0.0174, 90), (5, -22.86984, -2.5226, 90), (6, -22.86984, -5.0626, 90),
        (7, -22.86984, -7.6026, 90), (8, 20.32985, -9.9, 0), (9, 22.86985, -9.9, 0),
        (10, 22.86985, 9.9, 0), (11, 20.32985, 9.9, 0)
    ]
    for num, x, y, rot in pads:
        kicad_mod.append(Pad(number=num, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
            at=[x, y], rotation=rot, size=[pad_size, pad_size], drill=drill_size, layers=Pad.LAYERS_THT))
    
    return write_kicad_mod(kicad_mod, zip=1)

def b_2x2_m3_4j(d=33.9, hole=33.9, margin=4, zip=0):
    """绘制四个上下左右对称的圆模块（基于圆中心距离d）"""
    mod_size = d*2  # 模块宽度=高度
    kicad_mod = new_kicad_mod(w=mod_size, h=mod_size)
    center = mod_size / 2  # 模块中心
    
    # m4_4j_old(kicad_mod, d-2, d, d=1.2, thickness=1.6, j_long=1, hole_func=non_plated_hole, hole=5.8)  # M4连接器
    # m4_4j(kicad_mod, d, d, d=1.2, thickness=1.6, j_long=1, hole_func=non_plated_hole, hole=5.8)  # M4连接器
    # return write_kicad_mod(kicad_mod, zip=zip)
    
    # 添加中心孔
    dh = d - 3  # 中心孔偏移量
    def d_hole(kicad_mod,x,y,ad):
        non_plated_hole(kicad_mod,x,y,ad)
        circle(kicad_mod,x,y, 10)
    
    d_hole(kicad_mod, center+dh, center, 5.9)  # 右侧孔
    d_hole(kicad_mod, center-dh, center, 5.9)  # 左侧孔
    d_hole(kicad_mod, center, center+dh, 5.9)  # 下方孔
    d_hole(kicad_mod, center, center-dh, 5.9)  # 上方孔
    d_hole(kicad_mod, center, center, 5.9)     # 中心孔
    
    # 计算四个角的位置
    offset = d / 2  # 中心到圆中心的距离
    positions = [
        (center - offset, center - offset),  # 左上
        (center + offset, center - offset),  # 右上
        (center - offset, center + offset),  # 左下
        (center + offset, center + offset)   # 右下
    ]
    rectangle_full(kicad_mod,center-offset,center,w=20,h=66,layers=glayers_FB_Cu) 
    rectangle_full(kicad_mod,center+offset,center,w=20,h=66,layers=glayers_FB_Cu) 
    
    # 为每个位置设置不同的函数和d值
    # func_d_list = [
        # (m3_4j,dict(d=1.2,j_long=1.4,hole_func=plated_hole)),  # 左上
        # (m4_4j,dict(d=1.3,j_long=1.6)),  # 左下
        # (m3_4j,dict(d=1.3,j_long=1.5)),  # 右上
        # (m4_4j,dict(d=1.4,j_long=1.8,hole_func=plated_hole))   # 右下
    # ]
    func_d_list = [
    (m4_4j, dict(d=1.2, thickness=1.6, j_long=1, hole_func=plated_hole, hole=5.8, size=6.5,inner_delta=0.1)),  # 左上
    (m4_4j, dict(d=1.2, thickness=1.6, j_long=1, hole_func=plated_hole, hole=5.8, size=6.5,inner_delta=0.15)), # 右上
    (m4_4j, dict(d=1.2, thickness=1.6, j_long=1, hole_func=plated_hole, hole=5.8, size=6.5,inner_delta=0.2)),  # 
    (m4_4j, dict(d=1.2, thickness=1.6, j_long=1, hole_func=plated_hole, hole=5.8, size=6.5,inner_delta=0.25))   # 右下
    ]
    
    
    # 绘制四个角的孔结构
    for n, (x, y) in enumerate(positions):
        circle(kicad_mod, x, y, hole, layers="F.SilkS", width=0.02)  # 丝印层孔轮廓
        circle_filled(kicad_mod,x,y,20,layers=glayers_FB_Mask) # 在kicad中看偏小是正常。因为lceda=True
        func, ka = func_d_list[n]  # 获取函数和d值
        func(kicad_mod, x, y,**ka)  # 调用不同函数并传递d值
    
    # 添加标注并输出模块
    text(kicad_mod, f"d={d}", at=[center, mod_size + 5], size=[3, 2.5], layers="F.Cmts.User")
    return write_kicad_mod(kicad_mod, zip=zip)
    
    
def m3_4j(kicad_mod=None, x=0, y=0, d=1.4,thickness=1.2, j_long=1.4,hole_func=non_plated_hole):
    """创建M3四爪螺母的Kicad封装"""
    write_kicad = not kicad_mod
    if not kicad_mod: kicad_mod = new_kicad_mod()
    
    # 绘制中心圆和孔
    circle(kicad_mod, x, y, 12.4, crosshair=1, layers=glayers_FB_Cu, width=0.1)  # 外圆1
    circle(kicad_mod, x, y, 12, crosshair=0, layers=glayers_FB_Cu, width=0.1)    # 外圆2
    hole_func(kicad_mod, x, y, 4)  # 中心孔
    
    # 计算长条孔参数
    r_end =12.4/2- thickness/2  # 长条孔结束半径
    r_start =r_end-j_long    # 长条孔起始半径
    num_holes = max(1, int(j_long / 0.2))  # 孔数量（间距约0.2mm）
    
    # 绘制四爪长条孔
    for i in range(num_holes + 1):
        r = r_start + i * (j_long / num_holes)  # 当前半径
        hole_func(kicad_mod, x+d, y-r,thickness)  # 右上孔
        hole_func(kicad_mod, x-d, y+r, 1.2)  # 左下孔
        hole_func(kicad_mod, x-r, y-d, 1.2)  # 左上孔
        hole_func(kicad_mod, x+r, y+d, 1.2)  # 右下孔
    
    # 添加尺寸标注
    text(kicad_mod, f'd={d} j={j_long} t={thickness}', at=[x+14.5, y], size=[2, 1.6], layers=glayers_silk)
    
    return write_kicad_mod(kicad_mod, zip=1) if write_kicad else kicad_mod
    
    
    ka = dict(kicad_mod=kicad_mod,)
    for a in [0,90,180,270]:
        a=math.radians(a)  # 角度偏移转换为弧度
        for R in [4,5,]:
            xi=x+ R * math.cos(a)
            yi=y+ R * math.sin(a)
            non_plated_hole(kicad_mod,xi,yi,1.2)
    # m6_square_16x16 stm32f103_board
    
    if write_kicad:return write_kicad_mod(kicad_mod,zip=1)
    
    
def m4_4j_old(kicad_mod=None, x=0, y=0, d=1.3,thickness=1.8, j_long=1,D=15,hole=5.8,hole_func=non_plated_hole,add_text=False):
    """创建M4四爪螺母的Kicad封装  j_long 实际 是j_long+thickness 圆直径占据 """
    write_kicad = not kicad_mod
    if not kicad_mod: kicad_mod = new_kicad_mod()
    
    # 绘制法兰（盘）的同心圆
    circle(kicad_mod, x=x, y=y, d=D, crosshair=1, layers="F.Cu", width=0.1)  # 外层
    circle(kicad_mod, x=x, y=y, d=11, crosshair=0, layers="F.Cu", width=0.1)  # 内层
    hole_func(kicad_mod, x=x, y=y, diameter=hole)  # 中心孔
    
    # 计算长条孔参数
    r_end = D/2- thickness/2  # 长条孔结束半径
    r_start = r_end-j_long  # 长条孔起始半径
    num_holes = max(1, int(j_long / 0.2))  # 孔数量（间距约0.2mm）
    
    # 绘制四爪长条孔
    for i in range(num_holes + 1):
        r = r_start + i * (j_long / num_holes)  # 当前半径
        hole_func(kicad_mod,x=x+d,y=y-r, diameter=thickness)  # 右上
        hole_func(kicad_mod,x=x-d,y=y+r, diameter=thickness)  # 左下
        hole_func(kicad_mod,x=x-r,y=y-d, diameter=thickness)  # 左上
        hole_func(kicad_mod,x=x+r,y=y+d, diameter=thickness)  # 右下
        if i==0:        
            d0=1.1
            hole_func(kicad_mod,x=x+d0,y=y-r, diameter=thickness)  # 右上
            hole_func(kicad_mod,x=x-d0,y=y+r, diameter=thickness)  # 左下
            hole_func(kicad_mod,x=x-r,y=y-d0, diameter=thickness)  # 左上
            hole_func(kicad_mod,x=x+r,y=y+d0, diameter=thickness)  # 右下
    
            kicad_mod.append(Pad(number=f'{x}-{y-r},{thickness}',type=Pad.TYPE_THT,shape=Pad.SHAPE_OVAL,layers=Pad.LAYERS_THT,at=[x+d,y-r-0.5],size=[1.616, 3],drill=[1.5,2.6],),)
    
    if add_text:text(kicad_mod, f'd={d} j={j_long} t={thickness}', at=[x+16.5, y], size=[2, 1.6], layers="F.SilkS")
    
    return write_kicad_mod(kicad_mod, zip=1) if write_kicad else kicad_mod    

    
    
    
def circle_on_circle(n, d=24.12,bear_hole=8.9,angle_offset=0, zip=0):
    W = 100#D + d # 计算模块大小
    kicad_mod = new_kicad_mod(w=W, h=W,add_time=1) # 创建 KiCad 模块
    r = d / 2 # 小圆半径
    r2=5
    R = r / math.sin(math.pi / n) # 计算中心圆半径
    D = 2 * R # 计算中心圆直径
    Ri = R - r # 内切圆半径
    Ri2 = R - r2 # 内切圆半径
    Di2=D-r2*2
    if n == 0:
        return None
    x0,y0 = W/2, W/2
    non_plated_hole(kicad_mod,x0,y0,9.9)
    xd=29/2
    non_plated_hole(kicad_mod,x0-xd,y0,4) #moto
    non_plated_hole(kicad_mod,x0+xd,y0,4) #moto
    non_plated_hole(kicad_mod,x0,y0,17.4)
    non_plated_hole(kicad_mod,x0,y0,43) # 42.2 扩大让尾部通过
    # ka = dict(kicad_mod=kicad_mod, center=[x0, y0], radius=17.5/2-0.8, layers=glayers_edge_pure, width=1.6)
    # da=15
    # arc_start_end(start_angle=0, end_angle=90-da, **ka)   # 第一象限圆弧
    # arc_start_end(start_angle=90, end_angle=180-da, **ka)  # 第二象限圆弧
    # arc_start_end(start_angle=180, end_angle=270-da, **ka) # 第三象限圆弧
    # arc_start_end(start_angle=270, end_angle=360-da, **ka) # 第四象限圆弧
                    
    kicad_mod.append(Circle(center=[x0,y0], radius=R, layer='F.SilkS', width=0.15)) # 添加中心圆参考
    kicad_mod.append(Circle(center=[x0,y0], radius=Ri, layer='F.SilkS', width=0.15)) # 添加内切圆
    circle(kicad_mod, x0,y0,d=Di2) # 添加内切圆
    theta = 2 * math.pi / n # 计算角度增量
    for i in range(n):
        angle =i*theta + math.radians(angle_offset)  # 角度偏移转换为弧度
        x = x0 + R * math.cos(angle) # 小圆中心 x
        y = y0 + R * math.sin(angle) # 小圆中心 y
        circle(kicad_mod, x, y, d=d) # 添加小圆
        circle(kicad_mod, x, y, d=6,layers=glayers_Cmts) # 添加小圆
        circle(kicad_mod, x, y, d=8.9,layers=glayers_Cmts) # 添加小圆
        #circle(kicad_mod, x, y, d=r2*2,layers=glayers_Cmts) # 添加小圆
        circle(kicad_mod, x, y, d=25) # 添加小圆
        # if i in [1,3,6,8]:
        # non_plated_hole(kicad_mod,x,y,8.9)
        non_plated_hole(kicad_mod,x,y,5.9)
        text(kicad_mod,f'{i}', at=[x-6,y], size=[2,1.6], layers=glayers_silk,)
    text(kicad_mod,f'n={n},d={d},D={D},Di={Ri*2},Di2={Di2}', at=[x-40,-10], size=[4,3], layers=glayers_Cmts,)    
    crosshair(kicad_mod,x0,y0,w=W,h=W)
    
    
        
    wm=34.7
    hm=27
    dx=3.85+2
    ka=dict(up_rail=2.5)
    mgn12c_block(kicad_mod,wm/2-dx,hm/2,**ka)
    mgn12c_block(kicad_mod,100-wm/2+dx,hm/2,angle=180,**ka)
    mgn12c_block(kicad_mod,wm/2-dx,100-hm/2,**ka)
    mgn12c_block(kicad_mod,100-wm/2+dx,100-hm/2,angle=180,**ka)
    
    dcube=5#5.5/2
    dy=25/2
    non_plated_hole(kicad_mod,dcube,50+dy,2.9)
    non_plated_hole(kicad_mod,dcube,50-dy,2.9)
    non_plated_hole(kicad_mod,100-dcube,50+dy,2.9)
    non_plated_hole(kicad_mod,100-dcube,50-dy,2.9)
    
    # circle(kicad_mod,7,50,4)
    # rectline_center(kicad_mod,7,50,14)
    # circle(kicad_mod,100-7,50,4)
    # rectline_center(kicad_mod,100-7,50,14)

    # rectline_center(kicad_mod,5+4,27/2,8,12,layers=glayers_Cmts)
    
    return write_kicad_mod(kicad_mod, zip=zip) # 返回模块
    
    # mgn12c_block(kicad_mod,hm/2,wm/2-dx,angle=90)
       
    
    
def mgn12c_rail_triangle_2(wm=36.5,W=100,zip=0):
    kicad_mod = new_kicad_mod(w=W, h=W,add_time=1)
    # wm=34.7#
    # wm=36.5 # for y0=0
    hm=27
    xmid=50-34.7/2  # +3.85 (100-wm*3)/2
    
    # 两导轨中间空隙 wm-12=23  #34.7
    # 两导轨加滑块中间空隙 wm-27=23  #34.7
    
    y0=(100-2*wm)/2-(hm/2) # 1.8
    ka=dict(dh=50-12.5-27)
    mgn12c_rail_triangle(kicad_mod,xmid-wm,y0,**ka)
    # multi_dot_line(kicad_mod,[(x+wm,+y0),(x+wm,y0+hm)],width=0.1,layers=glayers_Cmts)
    dxm=1.8 # 一绿一黑滑块紧贴 36.5 wm-dxm=34.7  太靠近了，螺丝稍歪，拧入费力。下次考虑最小间距 35
    mgn12c_rail_triangle(kicad_mod,xmid+dxm,y0,**ka)
    mgn12c_rail_triangle(kicad_mod,xmid+wm,y0,**ka)
    
    ka={}
    xmid+=34.7/2
    y0+=hm/2+100-hm
    mgn12c_block(kicad_mod,xmid-wm,y0,**ka)
    mgn12c_block(kicad_mod,xmid+dxm,y0,**ka)
    mgn12c_block(kicad_mod,xmid+wm,y0,**ka)
    return write_kicad_mod(kicad_mod, zip=zip)
    
def jp57_silk_angle_ray(W=570, H=167, zip=0):
    """创建带角度射线的JP57网格丝印（精细版）"""
    import math
    
    # 初始化模块
    kicad_mod = new_kicad_mod(w=W, h=H)
    
    # 网格参数
    grid_spacing = 10  # 网格间距 10mm=1cm
    silk_line_width = 0.1  # 丝印线条宽度
    silk_layer = 'F.SilkS'  # 丝印层
    
    # 3. 添加角度射线（从原点(0,0)发出，覆盖0°到90°）
    text_size = 1.0  # 文本大小
    ray_length =(W**2+H**2)**0.5 # max(W, H) * 1.5  # 射线长度（板子最大尺寸的1.5倍）
    
    # 绘制主要射线（每10°一条）
    for angle in range(0, 91, 10):  # 0°到90°，步长10°
        angle_rad = math.radians(angle)
        end_x = ray_length * math.cos(angle_rad)
        end_y = ray_length * math.sin(angle_rad)
        
        kicad_mod.append(Line(
            start=(0, 0), 
            end=(end_x, end_y), 
            layer=silk_layer, 
            width=0.5
        ))
        
        # 添加角度文本标记（放在射线中间位置）
        # mid_x = end_x / 2
        # mid_y = end_y / 2
        
        # kicad_mod.append(Text(
            # type='user', 
            # text=f"{angle}°", 
            # at=(mid_x, mid_y),
            # layer=silk_layer, 
            # size=(text_size, text_size),
            # halign='center',
            # valign='center'
        # ))
    
    # 4. 添加10°-20°之间的精细刻度（每1°一条）
    fine_ray_length = W-11  # 精细刻度长度 500mm=50cm
    fine_text_offset = -2  # 精细刻度文本偏移量
    
    for fine_angle in range(1, 33):  # 1°到20°，每1°
        angle_rad = math.radians(fine_angle)
        
        
        # 计算射线终点坐标
        end_x = fine_ray_length * math.cos(angle_rad)
        end_y = fine_ray_length * math.sin(angle_rad)
        
        
        if 16<fine_angle: # qgb 控制 不要超出板面
            for ia in range(999):
                text_y = end_y + fine_text_offset * math.sin(angle_rad)
                if text_y> (H-fine_angle):
                    fine_ray_length-=1
                    # 计算射线终点坐标
                    end_x = fine_ray_length * math.cos(angle_rad)
                    end_y = fine_ray_length * math.sin(angle_rad)
                    
                    
                else:break
            
        ap=100
        
        # 添加短线
        kicad_mod.append(Line(
            start=(end_x, end_y), 
            end=(end_x + ap * math.cos(angle_rad), 
                 end_y + ap * math.sin(angle_rad)), 
            layer=silk_layer, 
            width=0.25
        ))
        
        
        
        text_x = end_x + fine_text_offset * math.cos(angle_rad)
        text_y = end_y + fine_text_offset * math.sin(angle_rad)
        
        kicad_mod.append(Text( # 添加角度文本标记（放在短线内侧）
            type='user', 
            text=f"{fine_angle}°", 
            at=(text_x, text_y),
            layer=silk_layer, 
            size=(4,4),
            halign='center',
            valign='center'
        ))
    
    
    fine_ray_length = 580
    for fine_angle in range(130, 170,2):  # 每0.2°
        angle_rad = math.radians(fine_angle/10)
        
        # 计算射线终点坐标（仅到50cm处）
        end_x = fine_ray_length * math.cos(angle_rad)
        end_y = fine_ray_length * math.sin(angle_rad)
        
        # 添加短线（从50cm处开始）
        ap=50
        kicad_mod.append(Line(
            start=(end_x, end_y), 
            end=(end_x + ap * math.cos(angle_rad), 
                 end_y + ap * math.sin(angle_rad)), 
            layer=silk_layer, 
            width=0.1
        ))
        
        
    # 保存模块
    return write_kicad_mod(kicad_mod, zip=zip)

def jp57_silk(W=100, H=100, margin=7, zip=0):
    """创建带1cm×1cm网格丝印及刻度标记的Kicad模块"""
    # 初始化模块
    kicad_mod = new_kicad_mod(w=W, h=H)
    
    # 网格参数
    grid_spacing = 10  # 网格间距 10mm=1cm
    silk_line_width = 0.1  # 丝印线条宽度
    silk_layer = 'F.SilkS'  # 丝印层
    
    # 刻度参数
    unit = 2  # 基本刻度长度 (mm)
    cm = 10   # 1cm=10mm
    
    # 1. 绘制横向水平线条
    for y in range(0, H + 1, grid_spacing):
        kicad_mod.append(Line(start=(0, y), end=(W, y), layer=silk_layer, width=silk_line_width))
    
    # 2. 绘制纵向垂直线条
    for x in range(0, W + 1, grid_spacing):
        kicad_mod.append(Line(start=(x, 0), end=(x, H), layer=silk_layer, width=silk_line_width))
    
    # 3. 添加边缘毫米刻度标记
    for i in range(0, max(W, H) + 1):
        # 确定刻度长度
        iu = unit
        if i % cm == 0:      # 厘米位置
            iu = unit * 3    # 最长刻度
        elif i % (cm // 2) == 0:  # 半厘米位置
            iu = unit * 2    # 中等刻度
        
        # 只在模块边界内绘制
        if i <= W:
            # 顶部边缘刻度
            kicad_mod.append(Line(
                start=(i, H), 
                end=(i, H - iu), 
                layer=silk_layer, 
                width=0.1
            ))
            
            # 底部边缘刻度
            kicad_mod.append(Line(
                start=(i, 0), 
                end=(i, iu), 
                layer=silk_layer, 
                width=0.1
            ))
        
        if i <= H:
            # 左侧边缘刻度
            kicad_mod.append(Line(
                start=(0, i), 
                end=(iu, i), 
                layer=silk_layer, 
                width=0.1
            ))
            
            # 右侧边缘刻度
            kicad_mod.append(Line(
                start=(W, i), 
                end=(W - iu, i), 
                layer=silk_layer, 
                width=0.1
            ))
    
    # 4. 添加每5厘米的文本标记
    text_size = 2.0  # 文本大小
    text_offset = 1.5  # 文本偏移量
    
    # 水平方向每5cm添加文本标记
    for x in range(0, W + 1, 50):  # 每5厘米
        if x > 0 and x < W:  # 避免在角落重复
            # 顶部标记
            kicad_mod.append(Text(
                type='user', 
                text=f"{x//10}",  # 将毫米转换为厘米
                at=(x, H - text_offset),
                layer=silk_layer, 
                size=(text_size, text_size),
                halign='center',
                valign='top'
            ))
            
            # 底部标记
            kicad_mod.append(Text(
                type='user', 
                text=f"{x//10}", 
                at=(x, text_offset),
                layer=silk_layer, 
                size=(text_size, text_size),
                halign='center',
                valign='bottom'
            ))
    
    # 垂直方向每5cm添加文本标记
    for y in range(0, H + 1, 50):  # 每5厘米
        if y > 0 and y < H:  # 避免在角落重复
            # 左侧标记
            kicad_mod.append(Text(
                type='user', 
                text=f"{y//10}", 
                at=(text_offset, y),
                layer=silk_layer, 
                size=(text_size, text_size),
                halign='left',
                valign='center',
                angle=90  # 垂直显示
            ))
            
            # 右侧标记
            kicad_mod.append(Text(
                type='user', 
                text=f"{y//10}", 
                at=(W - text_offset, y),
                layer=silk_layer, 
                size=(text_size, text_size),
                halign='right',
                valign='center',
                angle=90  # 垂直显示
            ))
    
    # 5. 添加顶
    for x in range(0, W+10, 10):
        kicad_mod.append(Text(
                    type='user', 
                    text=f"{(x//10)}", 
                    at=(x-5, margin),
                    layer=silk_layer, 
                    size=(5, 2),
                ))
                
        kicad_mod.append(Text(
                    type='user', 
                    text=f"{(x//10)}", 
                    at=(x-5, H-5-margin),
                    layer=silk_layer, 
                    size=(5, 2),
                ))
                
    
    for x in range(50, W, 50):  # 从50mm开始，每隔50mm
        for y in range(50, H, 50):  # 从50mm开始，每隔50mm
            # 只在网格交点处添加标记
            if x % grid_spacing == 0 and y % grid_spacing == 0:
                
                
                # 添加坐标文本标记
                kicad_mod.append(Text(
                    type='user', 
                    text=f"{x//10},{y//10}", 
                    at=(x, y),
                    layer=silk_layer, 
                    size=(text_size, text_size),
                    halign='center',
                    valign='center'
                ))
    
    # 6. 添加角落坐标标记
    
    # kicad_mod.append(Text( #左s角
        # type='user', 
        # text="0,0", 
        # at=(0, 0),
        # layer=silk_layer, 
        # size=(text_size, text_size),
        # halign='left',
        # valign='bottom'
    # ))
    
    # yx角
    kicad_mod.append(Text(
        type='user', 
        text=f"{W//10},{H//10}", 
        at=(W - margin, H - margin),
        layer=silk_layer, 
        size=(text_size, text_size),
        halign='right',
        valign='top'
    ))
    
    # 保存模块
    return write_kicad_mod(kicad_mod, zip=zip)

    
    
def jp57_cu(W=570,H=170,zip=0):#jp65_heatbed
    kicad_mod = new_kicad_mod(w=W,h=H)    
    simple_serpentine(kicad_mod,W/2,H/2,W,H,w=0.4,interval=0.2)
    return write_kicad_mod(kicad_mod, zip=zip)
    
def simple_serpentine(kicad_mod, x, y, W, H, w=0.4, interval=0.2, layer="F.Cu"):
    """简单蛇形走线函数（起点和终点都在左侧）
    x, y: 蛇形走线区域的中心坐标
    W: 走线区域宽度
    H: 走线区域高度
    w: 线宽
    interval: 线间距
    layer: 走线所在层
    """
    # 边距设置
    margin = max( min(w*2, 1),0.5)  # 边缘留空（最小间距）
    margin_x=margin+w
    # 计算区域起点坐标
    start_x = x - W/2+w*0.5  # 区域左上角X坐标
    start_y = y - H/2 + w*0.8  # 区域左上角Y坐标
    
    # 计算有效区域尺寸
    eff_width = W - 2 * margin
    eff_height = H - 2 * margin
    
    # 计算路径参数
    pitch = w + interval  # 线间距+线宽
    num_lines = max(2, int(eff_height / pitch))  # 走线数量（至少2条）
    
    # 确保线数为偶数（使起点和终点都在左侧）
    if num_lines % 2 != 0:
        num_lines += 1
    
    # 计算实际使用高度（居中）
    actual_height = num_lines * pitch
    center_offset = (eff_height - actual_height) / 2
    
    # 起点Y坐标（区域顶部+边距+居中偏移）
    current_y = start_y + margin + center_offset
    
    # 创建蛇形路径（从左到右开始）
    points = []
    direction = 1  # 1=向右, -1=向左
    
    for i in range(num_lines):
        # 水平线起点和终点
        if direction == 1:  # 向右走线
            x1 = start_x + margin_x
            x2 = start_x  + eff_width
        else:  # 向左走线
            x1 = start_x + eff_width
            x2 = start_x + margin_x
        
        # 添加水平线段
        points.append([(x1, current_y), (x2, current_y)])
        
        # 如果不是最后一条线，添加垂直线段
        if i < num_lines - 1:
            next_y = current_y + pitch
            points.append([(x2, current_y), (x2, next_y)])
            current_y = next_y
            direction *= -1  # 反转方向
    
    # 绘制所有线段
    for start, end in points:
        kicad_mod.append(Line(start=start, end=end, layer=layer, width=w))
    
    # 添加起点和终点标记（都在左侧）
    pdx =5/w
    pdy = 0.2
    # 起点标记（第一条线的起点）
    rectangle_full(kicad_mod, start_x + margin + w*pdx/1.5, points[0][0][1] - w*pdy, 
                  w=w*pdx, h=w*(1+pdy/2), layers=[layer, 'F.Mask'])
    
    # 终点标记（最后一条线的起点）
    last_point = points[-1][0] if points[-1][0][0] < points[-1][1][0] else points[-1][1]
    rectangle_full(kicad_mod, start_x + margin + w*pdx/1.5, last_point[1] + w*pdy, 
                  w=w*pdx, h=w*(1+pdy/2), layers=[layer, 'F.Mask'])
    
    return kicad_mod
    
    
    
def m6_square_16x16(kicad_mod,x,y,d=7,layers=glayers_silk):
    rectline_center(kicad_mod,x,y,w=16,width=0.1,crosshair=1,layers=layers) # test 
    non_plated_hole(kicad_mod,x,y,d=d)
    


def round_rect(kicad_mod=None, mod_w=100, mod_h=100, a=8, width=0.254, zip=1, sides=None,arc_angle = 60,**ka):
    """绘制圆角边框
    参数:
        mod_w: 矩形宽度 (mm)
        mod_h: 矩形高度 (mm)
        a: 圆角半径 (mm)
        width: 线宽 (mm)
        sides: 需要绘制的圆角边 [0:左上, 1:右上, 2:右下, 3:左下]
        
    通用说明:
        仅需修改下方的 arc_angle 即可切换圆弧角度，自动保证中心对称
        支持0~90之间任意角度，改完不用动其他参数
    """
    write_kicad=False
    if not kicad_mod:
        kicad_mod = new_kicad_mod(f"round_rect {mod_w},{mod_h},{a} {U.stime()[12:17]}", w=mod_w, h=mod_h)
        write_kicad=True
    
    wa = width  # 线宽
    if not sides:sides=[0,1,2,3]
    
    # --------------------------
    # 你只需要改这里的 arc_angle 即可！
    # 比如要88度就写88，要2度就写2，其他自动算
    
    # --------------------------
    
    offset_angle = (90 - arc_angle) / 2  # 自动计算两端偏移量，保证中点不变
    offset_rad = math.radians(offset_angle)
    r = a + wa / 2  # 自动补偿线宽，保证外边缘对齐
    
    # 1. 左上角：x/y都自动计算，不再硬编码固定值
    if 0 in sides:
        start_x = a - r * math.cos(offset_rad)
        start_y = a - r * math.sin(offset_rad)
        arc(kicad_mod, center=[a, a], start=[start_x, start_y], angle=arc_angle, layers=glayers_edge_pure, width=wa)
    
    # 2. 右上角：x/y都自动计算
    if 1 in sides:
        start_x = (mod_w - a) + r * math.sin(offset_rad)
        start_y = a - r * math.cos(offset_rad)
        arc(kicad_mod, center=[mod_w-a, a], start=[start_x, start_y], angle=arc_angle, layers=glayers_edge_pure, width=wa)
    
    # 3. 右下角：x/y都自动计算
    if 2 in sides:
        start_x = (mod_w - a) + r * math.cos(offset_rad)
        start_y = (mod_h - a) + r * math.sin(offset_rad)
        arc(kicad_mod, center=[mod_w-a, mod_h-a], start=[start_x, start_y], angle=arc_angle, layers=glayers_edge_pure, width=wa)
    
    # 4. 左下角：x/y都自动计算
    if 3 in sides:
        start_x = a - r * math.sin(offset_rad)
        start_y = (mod_h - a) + r * math.cos(offset_rad)
        arc(kicad_mod, center=[a, mod_h-a], start=[start_x, start_y], angle=arc_angle, layers=glayers_edge_pure, width=wa)
    
    if write_kicad:return write_kicad_mod(kicad_mod, zip=zip)
    return kicad_mod
    
        
def filled_circle(W=100,zip=0):
    kicad_mod = new_kicad_mod()
    circle(kicad_mod, 0,0, 33, crosshair=0, layers=glayers_FB_Cu,width=0)
    return write_kicad_mod(kicad_mod, zip=zip)
    
def pcbnew_filled_circle(W=100,):
    # 创建footprint
    footprint = pcbnew.FOOTPRINT(None)
    footprint.SetReference("FILLED_CIRCLE")   # 必须设置参考，否则无法保存
    footprint.SetValue("FilledCircle")
    # 设置位置为0,0
    footprint.SetPosition(pcbnew.VECTOR2I(0,0))

    # 创建圆
    circle = pcbnew.PCB_SHAPE()
    circle.SetShape(pcbnew.S_CIRCLE)
    circle.SetCenter(pcbnew.VECTOR2I(0,0))
    # 半径设置为W/2毫米，转换为纳米
    radius_nm = int(pcbnew.FromMM(W/2))
    circle.SetStart(pcbnew.VECTOR2I(radius_nm, 0))
    circle.SetLayer(pcbnew.F_Cu)
    circle.SetWidth(99999)   # 实心填充

    footprint.Add(circle)
    return footprint
    return footprint,circle

def b_8x6(d=35.5,hole=33.9,aluminum=False, margin=4, zip=0,cols=8,rows=6,round_edge=True):
    """绘制8列×6行的圆网格函数（无间隙、无颜色区分、带序号文本和模块中心大圆）"""
      # 列数×行数
    # 计算模块尺寸（边距×2 + 列/行数×直径）
    mod_w = 2 * margin + cols * d # 296
    mod_h = 2 * margin + rows * d -margin # 224
    # mod_h = 217
    
    kicad_mod = new_kicad_mod(f"b{cols}x{rows}_d{d}_margin{margin}_a{aluminum}_{U.stime()[12:17]}", w=mod_w, h=mod_h)
    if round_edge:
        a = 12    # 圆角半径（mm）
        day=0#2
        ay=a+day
        wa = 1   # 线宽（mm）
        # 1. 左上角圆角（中心(a,a)，从左边界顺时针画90°）
        arc(kicad_mod, center=[a, ay], start=[0 - wa/2, ay], angle=90, layers=glayers_edge_pure, width=wa)
        # 2. 右上角圆角（中心(mod_w - a,a)，从顶边界顺时针画90°）
        arc(kicad_mod, center=[mod_w - a, ay], start=[mod_w - a, 0 - wa/2+day], angle=90, layers=glayers_edge_pure, width=wa)
        # 3. 右下角圆角（中心(mod_w - a, mod_h - a)，从右边界顺时针画90°）
        arc(kicad_mod, center=[mod_w - a, mod_h - ay], start=[mod_w + wa/2, mod_h - ay], angle=90, layers=glayers_edge_pure, width=wa)
        # 4. 左下角圆角（中心(a, mod_h - a)，从底边界顺时针画90°）
        arc(kicad_mod, center=[a, mod_h - ay], start=[a, mod_h + wa/2-day], angle=90, layers=glayers_edge_pure, width=wa)
    
    

    # 绘制圆和序号文本（使用嵌套循环代替列表生成式）
    idx = 1
    da=(d-hole)/2+0.05
    # da=-4
    dy=-(margin/2)
    for yi in range(rows):  # 行循环
        # 1. 计算基础y坐标（未加偏移）
        base_y = margin + d/2 + yi * d +dy
        # 2. 根据行号调整偏移（偶数行加da，奇数行减da）
        if yi % 2 == 0:
            current_y = base_y + da  # 偶数行实际y
        else:
            current_y = base_y - da  # 奇数行实际y
        
        # 4. 处理每组第二行（奇数行，yi=1、3、5...）：计算midpoint_y并绘制矩形线
        if yi % 2 == 1:
            # 前一行（yi-1，偶数行）的基础y和实际y
            prev_base_y = margin + d/2 + (yi-1) * d  +dy
            prev_y = prev_base_y + da  # 前一行实际y（偶数行加da）
            midpoint_y = (prev_y + current_y) / 2# 计算中点y（直接用上下行实际y的平均）
            # 绘制矩形线（居中于PCB宽度）
            rectline_center(
                kicad_mod,mod_w/2,midpoint_y,       # 矩形线中心y坐标（两行中间）
                w=mod_w-6,          # 矩形线宽度（比PCB宽度小6，避免超出边界）
                h=50,               # 矩形线高度
                width=0.1,          # 线宽
                crosshair=1,        # 显示十字准星（可选）
                layers=glayers_silk # 绘制在丝印层
            )
        
        # 5. 列循环：绘制每个列的圆和钻孔
        for xi in range(cols):
            x = margin + d/2 + xi * d  # 计算x坐标
            # 绘制圆（使用当前行的实际y坐标）
            circle(kicad_mod, x, current_y, hole, crosshair=not aluminum, layers=glayers_silk,width=0.02)
            circle(kicad_mod, x, current_y, 16, crosshair=1, layers=glayers_Cmts,width=0.1)
            # 绘制非plated孔（若开启）
            if aluminum:
                # non_plated_hole(kicad_mod, x, current_y, d=hole)
                circle(kicad_mod, x, current_y, hole, crosshair=0, layers=glayers_edge_pure,)#
                # 绘制圆弧（仅奇数行）
                if yi % 2 == 1:
                    xd=18
                    cr=8
                    ca=33
                    arc_start_end(
                        kicad_mod,
                        center=[x-xd, midpoint_y],  # 圆弧中心（x偏移-10，y为中点）
                        radius=cr,                  # 圆弧半径
                        start_angle=-ca,            # 开始角度（-30°）
                        end_angle=ca,               # 结束角度（30°）
                        layers=glayers_edge_pure,        
                        # width=0.2                   # 线宽
                    )
                    arc_start_end(
                        kicad_mod,
                        center=[x+xd, midpoint_y],  # 圆弧中心（x偏移-10，y为中点）
                        radius=cr,                  # 圆弧半径
                        start_angle=-ca-180,            # 开始角度（-30°）
                        end_angle=ca-180,               # 结束角度（30°）
                        layers=glayers_edge_pure,        
                        # width=0.2                   # 线宽
                    )
            else:
                n=yi*rows+xi
                m3_4j(kicad_mod,x,current_y,d=1.3+n*0.06)
                # m6_square_16x16(kicad_mod,x-8,current_y,layers=glayers_FB_Cu)
                # m6_square_16x16(kicad_mod,x+8,current_y,layers=glayers_FB_Cu)
                # idx+=1;continue
                # non_plated_hole(kicad_mod, x, current_y, d=2.9)
                dia=hole
                circle_filled(kicad_mod,x,current_y,dia  , layers=glayers_FB_Cu,lceda=zip) #lceda 解析时 width=r  ,  kicad 显示 width=r*2-2 
                circle_filled(kicad_mod,x,current_y,dia-6, layers=glayers_FB_Mask ,lceda=zip)
                if yi % 2 == 1:
                    rectangle_full(kicad_mod,x,midpoint_y,w=24,h=50,layers=glayers_FB_Cu) 
                    # pass
            idx+=1
                
            # arc start=[x,midpoint_y],angle=60,layers=glayers_edge_pure,width=0.1)

    
    for yi in range(rows+1):  # 行循环（rows-1）
        for xi in range(cols+1):  # 列循环（cols-1）
            # 计算无铅孔坐标（位于4个圆中间）
            x = margin+ xi * d
            y = margin+ yi * d  +dy
            # 绘制无铅孔
            # non_plated_hole(kicad_mod, x, y, d=3.9)
            ds=4
            if xi in [0,]:x+=2
            if xi in [cols]:x-=2
            if yi in [0]:y+=ds
            if yi in [rows]:y-=ds
            # if xi in [0,cols]:x-=(xi-cols/2)
            # if yi in [0,rows]:y-=(xi-rows/2)*2
            
            # text(kicad_mod,f'{xi}={yi}', at=[x, y], size=[2,5], layers=glayers_silk+glayers_Cmts,)
            bx=xi%2==1
            by=yi%2==1
            if (bx or by) and not(bx and by):
                # y-=
                circle(kicad_mod, x,y,12, layers=glayers_silk)
                if yi in [1,3,5] and xi not in [0,8]:
                    pass
                    if aluminum:non_plated_hole(kicad_mod, x, y, d=5.9)
                else:    
                    non_plated_hole(kicad_mod, x, y, d=5.9)
                non_plated_hole(kicad_mod, x, y, d=5.9) #m3_4j    
    # 绘制模块标注（底部居中）
    text(kicad_mod, f"{mod_w}x{mod_h} d={d} margin={margin}", at=[mod_w/2, mod_h+5], size=[d/5, d/5], layers=glayers_Cmts)
    
    return write_kicad_mod(kicad_mod, zip=zip)


def hexagonal_packing(n=37, d=33, zip=0):
    """生成1，7，19，37，61，91，127，169，217，271...（OEIS:A003215） 数量圆的六边形密堆积（基于中心六边形数规律）"""
    import math
    r = d / 2  # 半径
    circles = []  # 存储圆心坐标

    # -------------------------- 步骤1：确定壳层数k（使总圆数最接近n） --------------------------
    # 中心六边形数公式：total = 1 + 3k(k+1)，反解k ≈ sqrt((total-1)/3) - 0.5
    if n < 1:
        raise ValueError("圆数量n必须≥1")
    if n == 1:
        k = 0  # 0个壳层（仅中心圆）
    else:
        # 计算最大可能的壳层数k（确保1+3k(k+1) ≤ n）
        k = int((math.sqrt((n - 1) / 3 + 0.25) - 0.5))
        # 若计算的总圆数小于n，尝试k+1（避免因四舍五入漏算）
        while 1 + 3 * (k + 1) * (k + 2) <= n:
            k += 1
        # 最终总圆数（可能小于n，取最接近的中心六边形数）
        total = 1 + 3 * k * (k + 1)
        if total != n:
            print(f"警告：n={n}不是中心六边形数，自动生成最接近的{total}个圆（壳层数k={k}）")

    # -------------------------- 步骤2：生成k个壳层的所有圆（共total个） --------------------------
    # 六边形网格坐标（q, r, s），范围|q|≤k, |r|≤k, |s|≤k且q+r+s=0
    for q in range(-k, k + 1):
        for r_coord in range(-k, k + 1):
            s = -q - r_coord
            if abs(s) > k:
                continue  # 限制在k个壳层内
            # 坐标转换公式（确保相邻圆心距=d）
            x = (2 * q + r_coord) * r
            y = math.sqrt(3) * r_coord * r
            circles.append((x, y))

    # 验证总圆数
    assert len(circles) == total, f"生成失败：{len(circles)}个圆（应为{total}个）"

    # -------------------------- 步骤3：Kicad模块生成（复用127圆代码的布局逻辑） --------------------------
    # 计算边界与偏移
    min_x = min(p[0] for p in circles)
    max_x = max(p[0] for p in circles)
    min_y = min(p[1] for p in circles)
    max_y = max(p[1] for p in circles)
    module_w = (max_x - min_x + d) * 1.02  # 2%边距
    module_h = (max_y - min_y + d) * 1.02
    offset_x = module_w / 2 - (max_x + min_x) / 2
    offset_y = module_h / 2 - (max_y + min_y) / 2
    circles_abs = [(x + offset_x, y + offset_y) for x, y in circles]

    # 创建Kicad模块
    kicad_mod = new_kicad_mod(name=f'hex_{total}circles_d{d}', w=module_w, h=module_h)
    colors = [[0, 0, 0]] + [[1 - i/k, i/k, 0] for i in range(1, k+1)]  # 壳层颜色（从红到绿渐变）
    if len(colors) < k + 1:
        colors += [[0, 0, 1]] * (k + 1 - len(colors))  # 颜色不足时用蓝色补充

    skip_count=0
    # 绘制圆与标注
    for idx, (x, y) in enumerate(circles_abs, 1):
        circle(kicad_mod, x, y, d, layers=glayers_silk)  # 绘制圆形（直径d）
        # 计算当前圆的壳层（基于六边形坐标）
        q = (x - offset_x)/d - (y - offset_y)/(math.sqrt(3)*d)
        r_coord = (y - offset_y)/(math.sqrt(3)*d)
        shell = max(abs(round(q)), abs(round(r_coord)), abs(round(-q - r_coord)))
        if idx in [
1,5,35,61,57,27,
36,44,51,
  28,37,45,52,#19 58,
        ]:
            skip_count+=1
        else:    # {idx}
            text(kicad_mod, f'{(idx-skip_count)} ', at=[x, y], size=[d/10, d/10], layers=glayers_FB_Cu, color=colors[min(shell, k)])
        if len(circles_abs)==61 and idx==31:
            circle(kicad_mod, x, y, 135*2, layers=glayers_FB_Cu)  # 绘制test 圆形（直径d）
        
    # 添加标注文本
    text(kicad_mod, f'密堆积：{total}圆（壳层数k={k}，直径{d}mm）', 
         at=[module_w/2, module_h + 5], size=[d/8, d/8], layers=glayers_FB_Cu)
    text(kicad_mod, f'中心六边形数：1 + 3k(k+1) = {total}（相邻间距={d}mm）', 
         at=[module_w/2, module_h + 15], size=[d/8, d/8], layers=glayers_FB_Cu)

    return write_kicad_mod(kicad_mod, zip=zip)

def c127(d=33, zip=0):
    """生成127个圆的密堆积（修正间距错误，确保相邻圆心距=直径d）"""
    import math
    r = d / 2  # 半径（核心修正：以半径为基准推导公式）
    circles = []  # 存储所有圆心坐标

    # -------------------------- 核心：修正坐标转换公式（确保间距=d） --------------------------
    # 六边形网格坐标（q, r），范围：|q| ≤ 6, |r| ≤ 6, |q + r| ≤ 6（共127个点）
    for q in range(-6, 7):        # q: -6~6
        for r_coord in range(-6, 7):  # r_coord: -6~6（避免与半径r重名）
            s = -q - r_coord
            if abs(s) > 6:        # 限制壳层=6
                continue
            # 修正后的坐标转换公式（确保相邻圆心距=d）
            # x = (2q + r_coord) * r，y = (√3 * r_coord) * r
            x = (2 * q + r_coord) * r
            y = math.sqrt(3) * r_coord * r
            circles.append((x, y))

    # 验证总圆数=127
    assert len(circles) == 127, f"总圆数错误：{len(circles)}（应为127）"
    # 验证相邻圆心距=直径d（以中心圆和第1壳层第1个圆为例）
    if len(circles) > 1:
        dx = circles[1][0] - circles[0][0]
        dy = circles[1][1] - circles[0][1]
        dist = math.hypot(dx, dy)
        assert abs(dist - d) < 0.1, f"间距错误：{dist:.1f}mm（应为{d}mm）"

    # -------------------------- Kicad模块生成（修正坐标偏移） --------------------------
    # 计算边界（确保所有圆在模块内）
    min_x = min(p[0] for p in circles)
    max_x = max(p[0] for p in circles)
    min_y = min(p[1] for p in circles)
    max_y = max(p[1] for p in circles)
    # 模块尺寸=边界范围+直径（含边距）
    module_w = (max_x - min_x + d) * 1.02  # 2%边距
    module_h = (max_y - min_y + d) * 1.02
    # 偏移量=模块中心 - 圆的中心
    offset_x = module_w/2 - (max_x + min_x)/2
    offset_y = module_h/2 - (max_y + min_y)/2
    circles_abs = [(x + offset_x, y + offset_y) for x, y in circles]

    # 创建Kicad模块
    kicad_mod = new_kicad_mod(name=f'hex_127密堆积_d{d}', w=module_w, h=module_h)
    colors = [[0,0,0], [1,0,0], [0,1,0], [0,0,1], [1,1,0], [1,0,1], [0,1,1]]  # 壳层颜色

    for idx, (x, y) in enumerate(circles_abs, 1):
        # 绘制圆形（直径d，确保相切）
        circle(kicad_mod, x, y, d, layers=glayers_silk)
        # 计算壳层（基于六边形坐标的模长）
        q = (x - offset_x)/(d) - (y - offset_y)/(math.sqrt(3)*d)  # 反推q
        r_coord = (y - offset_y)/(math.sqrt(3)*d)  # 反推r_coord
        shell = max(abs(round(q)), abs(round(r_coord)), abs(round(-q - r_coord)))
        text(kicad_mod, str(idx), at=[x, y], size=[d/10, d/10], layers=glayers_FB_Cu, color=colors[min(shell,6)])

    # 添加标注（显示间距验证结果）
    text(kicad_mod, f'密堆积：127圆（直径{d}mm，间距{d}mm，完美相切）', 
         at=[module_w/2, module_h + 5], size=[d/8, d/8], layers=glayers_FB_Cu)
    text(kicad_mod, f'验证：相邻圆心距={dist:.1f}mm（理论{d}mm）', 
         at=[module_w/2, module_h + 15], size=[d/8, d/8], layers=glayers_FB_Cu)

    return write_kicad_mod(kicad_mod, zip=zip)

def hexagonal_packing_3layer(d=33, zip=0):
    import math
    a = d  # 统一直径（所有圆直径均为d）
    circles = [(0.0, 0.0)]  # 第1层：中心圆（序号1）
    
    # -------------------------- 第2层：6个圆（序号2-7，R2=a） --------------------------
    R2 = a  # 第2层半径（与中心圆相切）
    angles2 = [math.radians(30 + 60*i) for i in range(6)]  # 30°,90°,...,330°
    for angle in angles2:
        x = R2 * math.cos(angle)
        y = R2 * math.sin(angle)
        circles.append((x, y))
    
    # -------------------------- 第3层：6个圆（序号8-13，R3=2a·cos30°） --------------------------
    R3 = 2 * a * math.cos(math.pi/6)  # 您确认的公式：≈1.732a（d=33时≈57.16mm）
    angles3 = [math.radians(60*i) for i in range(6)]  # 0°,60°,...,300°
    for angle in angles3:
        x = R3 * math.cos(angle)
        y = R3 * math.sin(angle)
        circles.append((x, y))
    
    # -------------------------- 3a子层：6个圆（序号14-19，R3a=2a，严格推导公式） --------------------------
    R3a = 2 * a  # 手动推导公式：R3a=2a（d=33时=66mm，比第3层大8.84mm，刚好相切）
    angles3a = [math.radians(30 + 60*i) for i in range(6)]  # 30°,90°,...,330°（与第2层角度对齐）
    for angle in angles3a:
        x = R3a * math.cos(angle)
        y = R3a * math.sin(angle)
        circles.append((x, y))
    
    # -------------------------- 模块尺寸与Kicad生成 --------------------------
    max_xy = max(math.hypot(x, y) for x, y in circles) + a/2  # 最外层=3a子层：66 + 16.5=82.5mm
    module_size = 2 * max_xy * 1.02  # 含2%边距
    center = module_size / 2
    circles_abs = [(x + center, y + center) for x, y in circles]
    
    kicad_mod = new_kicad_mod(name=f'hex_3layer_d{d}', w=module_size, h=module_size)
    for idx, (x, y) in enumerate(circles_abs, 1):
        circle(kicad_mod, x, y, a, layers=glayers_silk)
        color = [1,0,0] if idx <=13 else [0,0,1]  # 3a子层蓝色区分
        text(kicad_mod, str(idx), at=[x, y], size=[a/6, a/6], layers=glayers_FB_Cu, color=color)
    
    # 标注推导过程（确保公式正确性）
    text(kicad_mod, f'3a公式推导：R3a=2a（d={d}mm时={2*a}mm，与第2/3层相切）', 
         at=[center, module_size + 5], size=[a/5, a/5], layers=glayers_FB_Cu)
    text(kicad_mod, f'Layers=3+3a, Total=19, R3={R3:.1f}mm', 
         at=[center, module_size + 15], size=[a/5, a/5], layers=glayers_FB_Cu)
    return write_kicad_mod(kicad_mod, zip=zip)


def add_footprint_to_pcb(fp_path=r"C:\Program Files\KiCad\9.0\share\kicad\footprints\Symbol.pretty\Symbol_Danger_18x16mm_Copper.kicad_mod"):
    import os,pcbnew
    IU_PER_MM = 1000000  # KiCad内部单位（纳米）到毫米的转换因子
    board = pcbnew.GetBoard()  # 获取当前PCB板
    
    # 提取封装库目录和封装名称
    lib_path = os.path.dirname(fp_path)
    footprint_name = os.path.splitext(os.path.basename(fp_path))[0]
    
    # 加载封装
    footprint = pcbnew.FootprintLoad(lib_path, footprint_name)
    if footprint is None:  # 检查是否成功加载
        raise RuntimeError(f"无法加载封装: {fp_path}")
    
    # 计算PCB中心位置
    board_bbox = board.GetBoardEdgesBoundingBox()
    center_x = board_bbox.GetX() + board_bbox.GetWidth() / 2
    center_y = board_bbox.GetY() + board_bbox.GetHeight() / 2
    position = pcbnew.VECTOR2I(int(center_x), int(center_y))
    footprint.SetPosition(position)  # 设置封装位置
    
    footprint.SetReference("DNG")  # 设置参考标识符
    board.Add(footprint)  # 将封装添加到PCB板
    
    # 转换为毫米单位
    mm_x = center_x / IU_PER_MM
    mm_y = center_y / IU_PER_MM
    
    return f"成功添加封装 '{footprint.GetReference()}' 到位置 ({mm_x:.2f}mm, {mm_y:.2f}mm)"  # 返回成功消息

def packed_circles_in_circle(D=100, d=10, zip=0):
    import math
    import random

    def pack_circles(D, d):
        """
        Packs small circles of diameter d into a large circle of diameter D.
        This version tries to place circles until a certain number of consecutive failures.
        """
        R = D / 2
        r = d / 2
        packed_circles = []
        
        if r > R:
            return []

        max_failures = 1000
        failures = 0

        while failures < max_failures:
            angle = random.uniform(0, 2 * math.pi)
            distance_from_center = math.sqrt(random.uniform(0, 1)) * (R - r)
            x = distance_from_center * math.cos(angle)
            y = distance_from_center * math.sin(angle)

            # Check for overlaps with other circles
            overlap = False
            for cx, cy in packed_circles:
                if math.sqrt((x - cx)**2 + (y - cy)**2) < d:
                    overlap = True
                    break
            
            if not overlap:
                packed_circles.append((x, y))
                failures = 0  # Reset failures on success
            else:
                failures += 1
                
        return packed_circles

    kicad_mod = new_kicad_mod(name=f'packed_circles_D{D}_d{d}', w=D, h=D)
    
    center_x = D / 2
    center_y = D / 2

    # Draw the large circle
    circle(kicad_mod, center_x, center_y, radius=D/2, layers=glayers_silk)

    # Pack and draw the small circles
    small_circles = pack_circles(D, d)
    for x, y in small_circles:
        non_plated_hole(kicad_mod, center_x + x, center_y + y, d)

    # Add text with the number of packed circles
    info_text = f'D={D}, d={d}, Count={len(small_circles)}'
    text(kicad_mod, info_text, at=[D/2, -5], size=[1,1], layers=glayers_FB_Cu + glayers_Cmts)

    return write_kicad_mod(kicad_mod, zip=zip)


def super_capacitor_500F_6(W=100, H=100, D=35.5, pin_distance=15, zip=0):
    kicad_mod = new_kicad_mod(w=W, h=H)  # 创建模块
    # 过孔参数 - 只包含铜层确保被绿油覆盖
    via_params = dict(type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, size=[0.6,0.6], drill=0.3, layers=['*.Cu'])
    
    def super_capacitor_500F(kicad_mod, x, y):
        # 电容轮廓
        circle(kicad_mod, x, y, radius=D/2, layers=glayers_silk,width=0.1)  # 外圆
        circle(kicad_mod, x, y, radius=D/2-5, layers=glayers_silk,width=0.12)  # 内圆
        circle(kicad_mod, x, y, radius=6.5, layers=glayers_silk,width=0.1)  # 中心圆(d=13)
        # 焊盘参数
        pka = dict(type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT, size=[12,3], drill=[9.4,1.4], layers=Pad.LAYERS_THT)
        kicad_mod.append(Pad(number='1', at=[x-11, y], rotation=90, **pka))  # 垂直焊盘
        kicad_mod.append(Pad(number='2', at=[x+6, y+5], rotation=0, **pka))  # 水平焊盘
        # 在焊盘1周围打过孔 (只连接铜层)
        pad1_x, pad1_y = x-11, y
        for dx in range(-5, 6, 2):  # X方向±5mm间隔2mm
            for dy in range(-5, 6, 2):  # Y方向±5mm间隔2mm
                kicad_mod.append(Pad(number=0, at=[pad1_x+dx, pad1_y+dy], **via_params))  # 密集过孔
        # 在焊盘2周围打过孔 (只连接铜层)
        pad2_x, pad2_y = x+6, y+5
        for dx in range(-5, 6, 2):  # X方向±5mm间隔2mm
            for dy in range(-5, 6, 2):  # Y方向±5mm间隔2mm
                kicad_mod.append(Pad(number=0, at=[pad2_x+dx, pad2_y+dy], **via_params))  # 密集过孔
    
    # 电容布局
    y = 50 - D  # 垂直位置基准
    super_capacitor_500F(kicad_mod, 32, y)  # 左上
    super_capacitor_500F(kicad_mod, 32, y + D)  # 左中
    super_capacitor_500F(kicad_mod, 32, y + D*2)  # 左下
    super_capacitor_500F(kicad_mod, W-32, y)  # 右上
    super_capacitor_500F(kicad_mod, W-32, y + D)  # 右中
    super_capacitor_500F(kicad_mod, W-32, y + D*2)  # 右下
    
    plated_hole(kicad_mod,32-11-8,y+D,4.9,size=12,shape=Pad.SHAPE_RECT)  # 额外安装孔
    plated_hole(kicad_mod,32-11-10,y+D*2,4.9,size=12,shape=Pad.SHAPE_RECT)  # 额外安装孔
    
    y=0
    for i in range(1,10):  # 测试孔阵列
        y=y+i*2
        plated_hole(kicad_mod,100-8,y,i,size=i*1.5,shape=Pad.SHAPE_RECT)
    
    if zip:  # 密集测试过孔
        for dx in range(2,100,3):  # X方向
            for dy in range(2,100,3):  # Y方向
                kicad_mod.append(Pad(number=3, at=[dx,dy], **via_params))  # 过孔
    
    return write_kicad_mod(kicad_mod, zip=zip)  # 生成输出

def b3265_8x7_full_parking(D=33.2, zip=True):
    layers = glayers_silk + glayers_FB_Cu
    import math
    # --- 1. 定义布局参数 ---
    grid_rows = 8
    grid_cols_max = 7
    R = D / 2.0
    step_x = D
    step_y = D * math.sqrt(3) / 2
    # --- 2. 动态计算边界框 W 和 H ---
    W = (grid_cols_max - 1) * step_x + D
    H = (grid_rows - 1) * step_y + D
    # --- 3. 初始化封装 ---
    kicad_mod = new_kicad_mod(name=f'Circle_8x7_D{D}_Interstitial_v2', w=W, h=H, edge_layers=glayers_edge_fsilk)
    
    circle_count_large = 0
    circle_count_small = 0
    # --- 4. 循环创建所有大圆 ---
    large_circle_centers = []
    for r in range(grid_rows):
        y_current = R + r * step_y
        x_start = R
        cols_in_this_row = grid_cols_max
        if r % 2 != 0:
            x_start += R
            cols_in_this_row = grid_cols_max - 1
        for c in range(cols_in_this_row):
            cx = x_start + c * step_x
            cy = y_current
            circle(kicad_mod, cx, cy, radius=R, layers=layers)
            text(kicad_mod,circle_count_large+1,at=[cx,cy], size=[3,3], layers=layers)
            large_circle_centers.append((cx, cy))
            circle_count_large += 1
            
    # --- 5. 在空隙中添加小圆 (全新、正确的搜索逻辑) ---
    d_small = 3.9 # D * 0.1547
    r_small = d_small / 2.0
    centers_set = { (round(cx, 5), round(cy, 5)) for cx, cy in large_circle_centers } # 使用圆整后的坐标以避免浮点数精度问题
    small_circles_to_add = py.set()
    
    for (cx, cy) in large_circle_centers:
        # **关键修正**: 对于每个圆，检查它周围所有6个可能的邻居位置
        # 邻居1: 右侧
        p_right = (round(cx + step_x, 5), round(cy, 5))
        # 邻居2: 右上
        p_upper_right = (round(cx + R, 5), round(cy + step_y, 5))
        # 邻居3: 左上
        p_upper_left = (round(cx - R, 5), round(cy + step_y, 5))
        # 邻居4: 左下
        p_lower_left = (round(cx - R, 5), round(cy - step_y, 5))
        # 邻居5: 右下
        p_lower_right = (round(cx + R, 5), round(cy - step_y, 5))

        # 检查 "顶点朝上" (▲) 的组合
        if p_right in centers_set and p_upper_right in centers_set:
            small_cx = round((cx + p_right[0] + p_upper_right[0]) / 3, 5)
            small_cy = round((cy + p_right[1] + p_upper_right[1]) / 3, 5)
            small_circles_to_add.add((small_cx, small_cy))
        
        # 检查 "顶点朝下" (▼) 的组合
        if p_right in centers_set and p_lower_right in centers_set:
            small_cx = round((cx + p_right[0] + p_lower_right[0]) / 3, 5)
            small_cy = round((cy + p_right[1] + p_lower_right[1]) / 3, 5)
            small_circles_to_add.add((small_cx, small_cy))

    for (scx, scy) in small_circles_to_add:
        circle(kicad_mod, scx, scy, radius=r_small, layers=layers)
        circle_count_small += 1
        
    # --- 6. 添加信息文本并生成文件 ---
    info_text = f'W:{W:.2f} H:{H:.2f} Large:{circle_count_large} Small:{circle_count_small}'
    text(kicad_mod, info_text, at=[W/2, -5], size=[1,1], layers=glayers_FB_Cu + glayers_Cmts)
    
    rectangle_outline(kicad_mod, 0,(H-225)/2, w=217, h=225, layers=layers) # 4. 在丝印层绘制整个区域的边框
    
    return write_kicad_mod(kicad_mod, zip=zip)

def b3265_52_full_parking(D=32.5, zip=0):
    import math
    # --- 1. 定义布局参数 ---
    grid_rows = 7
    grid_cols_max = 8
    R = D / 2.0
    step_x = D
    step_y = D * math.sqrt(3) / 2
    # --- 2. 动态计算能容纳所有圆的最小矩形 W 和 H ---
    W = (grid_cols_max - 1) * step_x + D
    H = (grid_rows - 1) * step_y + D
    # --- 3. 初始化封装 ---
    kicad_mod = new_kicad_mod(name=f'Circle_8x7_D{D}_Packing_49pcs_Corrected', w=W, h=H, edge_layers=glayers_edge_fsilk)
    layers = glayers_silk + glayers_FB_Cu
    circle_count = 0
    
    # --- 4. 逐行构建六边形紧密堆积阵列 (逻辑重构) ---
    for r in range(grid_rows): # 外层循环遍历行 (Y轴)
        y_current = R + r * step_y # 计算当前行的中心Y坐标
        x_start = R # 偶数行的起始X坐标
        cols_in_this_row = grid_cols_max
        if r % 2 != 0: # 如果是奇数行
            x_start += R # 则增加一个半径的水平偏移
            cols_in_this_row = grid_cols_max - 1
        for c in range(cols_in_this_row): # 内层循环遍历当前行的圆 (X轴)
            x_current = x_start + c * step_x # 计算当前圆的中心X坐标
            # 跳过指定的3个圆
            if c == 0 and r in [2, 4, 6]: # 定义要跳过的物理行号 (从下往上，从0开始):
                continue
            circle(kicad_mod, x_current,y_current, radius=R, layers=layers)
            text(kicad_mod,circle_count+1,at=[x_current,y_current], size=[3,3], layers=layers)
            circle_count += 1
    # --- 5. 添加信息文本并生成文件 ---
    info_text = f'W:{W:.2f} H:{H:.2f} Count:{circle_count}'
    text(kicad_mod, info_text, at=[W/2, -5], size=[1,1], layers=glayers_FB_Cu + glayers_Cmts)
    return write_kicad_mod(kicad_mod, zip=zip)

def b3265_8x6_full_parking(D=33, zip=0):
    import math
    # --- 1. 根据布局和D，动态计算出能容纳所有圆的最小矩形 W 和 H ---
    grid_rows = 8
    grid_cols = 6
    R = D / 2.0
    step_x = D
    step_y = D * math.sqrt(3) / 2
    # 宽度由包含6个圆的行决定
    W = (grid_cols - 1) * step_x + D
    # 高度由8行决定
    H = (grid_rows - 1) * step_y + D
    # --- 2. 初始化封装 ---
    kicad_mod = new_kicad_mod(name=f'Circle_8x6_D{D}_Packing', w=W, h=H, edge_layers=glayers_edge_fsilk)
    layers = glayers_silk + glayers_FB_Cu
    y_current = R # 从底部半径处开始第一行
    circle_count = 0
    for r in range(grid_rows): # --- 3. 循环创建8行 ---
        x_current = R # 偶数行的起始X坐标
        cols_in_this_row = grid_cols
        if r % 2 != 0: # 如果是奇数行
            x_current += R # 则增加一个半径的水平偏移
            cols_in_this_row -= 1 # 奇数行会少一个圆以保持紧凑
        for c in range(cols_in_this_row): # 循环创建当前行的所有圆
            circle(kicad_mod, x_current, y_current, radius=R, layers=layers)
            circle_count += 1
            x_current += step_x
        y_current += step_y
    # --- 4. 添加信息文本并生成文件 ---
    info_text = f'W:{W:.2f} H:{H:.2f} Count:{circle_count}'
    text(kicad_mod, info_text, at=[W/2, -5], size=[1,1], layers=glayers_FB_Cu + glayers_Cmts)
    return write_kicad_mod(kicad_mod, zip=zip)

def full_parking_circle(W=272, H=250, D=33, zip=0):
    import math
    kicad_mod = new_kicad_mod(name=f'full_parking_circle_{W}x{H}_D{D}', w=W, h=H, edge_layers=glayers_edge_fsilk)
    layers = glayers_silk + glayers_FB_Cu
    R = D / 2.0
    step_x = D
    step_y = D * math.sqrt(3) / 2
    y_current = R
    row_index = 0
    circle_count = 0
    max_x_used, max_y_used = 0, 0
    while y_current <= H - R:
        x_current = R
        if row_index % 2 != 0:
            x_current += R
        while x_current <= W - R:
            circle(kicad_mod, x_current, y_current, radius=R, layers=layers)
            circle_count += 1
            if x_current + R > max_x_used: max_x_used = x_current + R
            x_current += step_x
        if y_current + R > max_y_used: max_y_used = y_current + R
        y_current += step_y
        row_index += 1
    info_text = f'Actual W: {max_x_used:.2f}, H: {max_y_used:.2f}, Count: {circle_count}'
    text(kicad_mod, info_text, at=[W/2, -5], size=[1,1], layers=glayers_FB_Cu + glayers_Cmts)
    return write_kicad_mod(kicad_mod, zip=zip)

def b3265_3x3_aluminum(W=100, H=100,zip=0):
    kicad_mod = new_kicad_mod(w=W, h=H, text_at=[W/2, -5], edge_layers=glayers_edge_fsilk) 
    d=W/3
    for yi in range(3):
        for xi in range(3):
            x=(xi+0.5)*d
            y=(yi+0.5)*d
            non_plated_hole(kicad_mod,x,y,d=3.85)
    non_plated_hole(kicad_mod,0.5*d,0.5*d,d=4.85)
    non_plated_hole(kicad_mod,1.5*d,0.5*d,d=5.85)
    non_plated_hole(kicad_mod,2.5*d,0.5*d,d=7.85)
    return write_kicad_mod(kicad_mod,zip=zip)    
    
def link_bar(W=347, H=180, bar_width=7.0,cut_width=1.2, zip=0):
    if zip:test_layer=[]
    else  :test_layer=['B.Cu','B.Mask']
    kicad_mod = new_kicad_mod(name=f'Link_Bar_{W}x{H}={U.stime()[12:17]}', w=W, h=H, text_at=[W/2, -5], edge_layers=glayers_edge_fsilk) 
    rectline_center(kicad_mod,W/2,H/2,w=W,h=66,width=0.01,crosshair=1,layers=glayers_silk+test_layer,) # test 
    dry=33+23/2
    rectline_center(kicad_mod,W/2,H/2+dry,w=W,h=23,width=0.01,crosshair=1,layers=glayers_silk+test_layer,) # test 
    rectline_center(kicad_mod,W/2,H/2-dry,w=W,h=23,width=0.01,crosshair=1,layers=glayers_silk+test_layer,) # test 
    
    end_margin = 5.0 # 上下不切断的保留间距
    num_bars = int((W + cut_width) / (bar_width + cut_width)) # 计算可以容纳的连接条数量
    total_content_width = (num_bars * bar_width) + ((num_bars - 1) * cut_width) # 计算所有内容的总宽度
    start_x_offset = (W - total_content_width) / 2 # 计算起始偏移量以实现居中
    bar_height = H - 2 * end_margin # 计算每个条和槽的实际高度
    for i in range(num_bars): # --- 单一循环处理所有“条”和“槽” ---
        bar_start_x = start_x_offset + i * (bar_width + cut_width) # 计算当前条的起始X坐标
        bar_center_x = bar_start_x + bar_width / 2 # 计算当前条的中心X坐标
        rectangle_full(kicad_mod, bar_center_x,H/2,w=bar_width,h=bar_height, layers=glayers_F_Cu) 
        rectangle_full(kicad_mod, bar_center_x, H/2+33+12, w=bar_width, h=24, layers=glayers_F_Mask) 
        rectangle_full(kicad_mod, bar_center_x, H/2-33-12, w=bar_width, h=24, layers=glayers_F_Mask)
        
        rectline_center(kicad_mod,bar_center_x,H/2,w=bar_width,h=bar_height,width=0.01,crosshair=1,layers=['F.SilkS']+test_layer,) # 勾勒条的外形
        # rectangle_outline(kicad_mod, bar_start_x, end_margin, w=bar_width, h=bar_height, layers=glayers_silk)
        non_plated_hole(kicad_mod,bar_center_x,H/2,d=2.9)
        rectangle_full(kicad_mod, bar_center_x,H/2,w=bar_width,h=8, layers=glayers_F_Mask)
        dhy=70
        yna=H/2+dhy + ((i+1)//8)*0.05
        non_plated_hole(kicad_mod,bar_center_x,yna,d=2.9)
        rectangle_full(kicad_mod, bar_center_x,yna,w=bar_width,h=8, layers=glayers_F_Mask)
        ynb=yna=H/2-dhy - ((i+1)//8)*0.05
        non_plated_hole(kicad_mod,bar_center_x,ynb,d=2.9)
        rectangle_full(kicad_mod, bar_center_x,ynb,w=bar_width,h=8, layers=glayers_F_Mask)
        
        
        text(kicad_mod,bar_center_x,H/2-33+3,t=(i%24)+1,size=3,layers=['F.SilkS',]+test_layer,)
        # text(kicad_mod,bar_center_x,H/2-21+i+3,t=(i%24)+1,size=3,layers=['F.SilkS',]+test_layer,)
        
        if i < num_bars - 1: # 如果不是最后一个条，则在它的右侧绘制切槽
            cutout_center_x = bar_start_x + bar_width + cut_width / 2 # 计算切槽的中心X坐标
            rectangle_full(kicad_mod, cutout_center_x, H / 2, w=cut_width, h=bar_height, layers=glayers_edge_pure) # 绘制切槽
            
            rectangle_full(kicad_mod, bar_start_x,5-cut_width/2, w=2, h=cut_width, layers=glayers_edge_pure) # 绘制切槽
            rectangle_full(kicad_mod, bar_start_x+bar_width,5-cut_width/2, w=2, h=cut_width, layers=glayers_edge_pure) 
            
            yc=H-(5-cut_width/2)
            rectangle_full(kicad_mod, bar_start_x,          yc, w=2, h=cut_width, layers=glayers_edge_pure) # 绘制切槽
            rectangle_full(kicad_mod, bar_start_x+bar_width,yc, w=2, h=cut_width, layers=glayers_edge_pure) 
            
            
    return write_kicad_mod(kicad_mod, zip=zip)
    


def b3265_8x6(W=272, H=246+4, zip=0):
    kicad_mod = new_kicad_mod(name=f'b3265_8x6={W}x{H}={U.stime()[12:17]}', w=W, h=H, text_at=[W/2, -4], edge_layers=glayers_edge_fsilk) # 1. 初始化封装
    d32 = 32.5 # 定义圆的固定直径
    gap = W/8-d32 # 定义圆之间的固定间隙
    step_x = d32 + gap # 2. 根据固定间隙计算步进距离
    step_y = d32 + gap
    step_x=step_y=34
    
    start_x=(W-34*8)/2+34/2
    start_y=(H-34*6)/2+34/2
    
    U.set('x,y mid',[W/2,start_y+34*2.5])
    for c in range(8): # 4. 循环遍历所有列
        for r in range(6): # 循环遍历所有行
            center_x = start_x + c * step_x # 计算当前圆的中心X坐标
            center_y = start_y + r * step_y # 计算当前圆的中心Y坐标
            circle(kicad_mod, center_x, center_y, radius=d32/2,width=0.1,layers=glayers_silk) # 绘制圆
            strong_plated_hole(kicad_mod, center_x, center_y, d=3.9, size=10, cu_size=11.8,number=f'{c+1}-{r+1}') # 使用增强型过孔
            # plated_hole(kicad_mod, center_x, center_y, d=3.9, size=10,number=f'{c+1}-{r+1}') # 使用增强型过孔
    rectline_center(kicad_mod,*U.get('x,y mid'),w=34*8,h=34*6,width=0.01,crosshair=1,layers=glayers_silk+[],) # test 
            
    # --- 5. 在顶部边缘均匀分布24个gb30元件 ---
    num_gb30 =24 # 定义要放置的元件数量
    for i in range(num_gb30): # 循环放置24个元件
        x = (i + 0.5) * (W / num_gb30) # **精简公式**: 直接计算第i个元件的中心X坐标
        gb30(kicad_mod, x,11.5,number=25-i,mask='F.Mask') # 假设已定义
        gb30(kicad_mod, x,H-11.5,number=i+1,mask='B.Mask') # 假设已定义
        
    xm=W/2
    ym=H/2
    dx=103
    non_plated_hole(kicad_mod,x=xm,y=ym,d=9.9) #左上
    # non_plated_hole(kicad_mod,x=xm+dx,y=ym,d=5.9) #左上
    # non_plated_hole(kicad_mod,x=xm-dx,y=ym,d=5.9) #左上
    hole_rect_center(kicad_mod,xm,ym,side_len_x=98,angle=45,d=5.9)
    
        
    return write_kicad_mod(kicad_mod, zip=zip) # 6. 生成最终文件
    
def gb30(kicad_mod,x,y,d=3.9,number=0,mask='B.Mask',**ka):
    ''' 铝型材 国标 30 弹片 m4'''
    rectline_center(kicad_mod,x,y,w=9,h=23,width=0.05,crosshair=1,layers=glayers_silk+[],) 
    multi_dot_line(kicad_mod,[(x,y-8.8),(x,y+8.6)],width=7,layers=glayers_FB_Cu+[mask])
    
    ka['d']=3.9
    ka['size']=8
    ka['number']=number
    if mask=='F.Mask':
        plated_hole(kicad_mod,x,y+5.5,**ka) # 原始孔 距离边缘6mm 。
        plated_hole(kicad_mod,x,y-5.5,**ka)
        plated_hole(kicad_mod,x,y-6,**ka)
    if mask=='B.Mask':
        plated_hole(kicad_mod,x,y-5.5,**ka) # 原始孔 距离边缘6mm 。
        plated_hole(kicad_mod,x,y+5.5,**ka)
        plated_hole(kicad_mod,x,y+6,**ka)
    
def b3265_7x7(W=244, H=274.5, zip=0):
    kicad_mod = new_kicad_mod(name=f'b3265_7x7_{W}x{H}', w=W, h=H, text_at=[W + 2, H / 2], edge_layers=glayers_edge_fsilk) # 1. 初始化封装
    d32 = 32.5 # 定义圆的固定直径
    grid_size = 7 # 定义网格尺寸为7x7
    gap = 2.0 # 定义圆之间的固定间隙
    step_x = d32 + gap # 2. 根据固定间隙计算步进距离
    step_y = d32 + gap
    total_grid_width = (grid_size - 1) * step_x + d32 # 3. 计算起始坐标
    total_grid_height = (grid_size - 1) * step_y + d32 # 计算整个阵列的总高度
    start_x = d32/2 + gap + 0.25 # 采用您提供的、经过优化的起始X坐标
    # start_y = (H - total_grid_height) / 2 + d32 / 2 # **计算能使阵列在垂直方向上居中的起始Y坐标**
    start_y =start_x+8
    
    for c in range(grid_size): # 4. 循环遍历所有列
        for r in range(grid_size): # 循环遍历所有行
            center_x = start_x + c * step_x # 计算当前圆的中心X坐标
            center_y = start_y + r * step_y # 计算当前圆的中心Y坐标
            if c==r==3:U.set('x,y mid',[center_x,center_y])
            circle(kicad_mod, center_x, center_y, radius=d32/2,width=1,layers=glayers_silk) # 绘制圆
            strong_plated_hole(kicad_mod, center_x, center_y, d=3.9, size=10, cu_size=12,number=f'{c+1}-{r+1}') # 使用增强型过孔
    rectline_center(kicad_mod,*U.get('x,y mid'),w=239.5,width=0.1,crosshair=1,layers=glayers_FB_Cu) # test 
            
    # --- 5. 在顶部边缘均匀分布24个gb30元件 ---
    num_gb30 =24 # 定义要放置的元件数量
    for i in range(num_gb30): # 循环放置24个元件
        x = (i + 0.5) * (W / num_gb30) # **精简公式**: 直接计算第i个元件的中心X坐标
        gb30(kicad_mod, x,H-11.5,number=i+1) # 假设gb30已定义
    return write_kicad_mod(kicad_mod, zip=zip) # 6. 生成最终文件

def b3265_5x5(W=258, zip=0):
    ''' 244x275  价格 0.88
    244x274.5  免费
'''   
    
    H=W
    kicad_mod = new_kicad_mod(name=f'Circle_Grid_5x5_D32.5_{W}x{H}', w=W, h=H, text_at=[W + 2, H / 2]) # 1. 初
    d32 = 32.5 # 定义固定直径
    grid_size = 5 # 定义网格尺寸为5x5
    step_x = W / grid_size # 2. 计算网格的水平步进距离
    step_y = H / grid_size # 计算网格的垂直步进距离
    
    step_x=step_y=d32+2
    start_x = step_x / 2 # 计算第一个圆心的起始X坐标，使其在单元格内居中
    start_y = step_y / 2 # 计算第一个圆心的起始Y坐标
    for c in range(grid_size): # 3. 循环遍历所有列
        for r in range(grid_size): # 循环遍历所有行
            center_x = start_x + c * step_x # 计算当前圆的中心X坐标
            center_y = start_y + r * step_y # 计算当前圆的中心Y坐标
            circle(kicad_mod, center_x, center_y, radius=d32/2, layers=glayers_silk) # 绘制圆
    rectangle_outline(kicad_mod, 0, 0, w=W, h=H, layers=glayers_silk) # 4. 在丝印层绘制整个区域的边框
    return write_kicad_mod(kicad_mod, zip=zip) # 5. 生成最终文件

def circle32_4(d=32,W=100,j=1,zip=1):
    # for i in 
    kicad_mod = new_kicad_mod(name=f'circle32_4d{d}W{W}', w=W, h=W) # 1. 初始化封装
    x=y=W/2
    e=d/2+j
    non_plated_hole(kicad_mod,x=x-e,y=y-e,d=32.5+0.0) #左上
    non_plated_hole(kicad_mod,x=x+e,y=y-e,d=32.5+0.1)# 右上
    non_plated_hole(kicad_mod,x=x-e,y=y+e,d=32.5+0.2)
    non_plated_hole(kicad_mod,x=x+e,y=y+e,d=32.5+0.3)#
    
    
    dsh=3.9# diameter of screw hole
    non_plated_hole(kicad_mod,x=x,y=y,d=5.9)#
    s=d-3
    non_plated_hole(kicad_mod,x=x+s,y=y,d=dsh)#
    non_plated_hole(kicad_mod,x=x-s,y=y,d=dsh)#
    non_plated_hole(kicad_mod,x=x,y=y+s,d=dsh)#
    non_plated_hole(kicad_mod,x=x,y=y-s,d=dsh)#
    
    hole_rect_center(kicad_mod,x,y,side_len_x=W-7,d=dsh)
    
    return write_kicad_mod(kicad_mod, zip=zip) # 3. 生成最终文件```


def circle32_td(d=32, n=12, zip=0):
    ''' td 可变 直径测试 '''
    import math # 导入数学库
    kicad_mod = new_kicad_mod(name=f'Hole_Line_Variable_d{d}_n{n}', w=0, h=0) # 1. 初始化封装
    x_center_current = 0 # 初始化第一个孔的中心为原点
    max_diameter = 0 # 用于追踪最大的孔径，以确定外框高度
    
    # 第一次循环: 放置孔洞并计算最终的 x_end
    for i in range(n):
        td = d + 0.04 *(i-3) # 计算当前孔的可变直径
        if td > max_diameter: max_diameter = td # 更新最大直径
        if i == 0: # 处理第一个孔
            x_start = -td / 2 # 计算整条孔链的起始边缘
            x_center_current = 0
            x_end_previous = td / 2
        else: # 处理后续的孔
            x_center_current = x_end_previous + td / 2 # 新孔的中心 = 上一个孔的右边缘 + 新孔的半径
            x_end_previous = x_center_current + td / 2 # 更新“上一个孔的右边缘”

        non_plated_hole(kicad_mod, x=x_center_current, y=0, d=td) # 放置当前孔
        
    x_end = x_end_previous # 循环结束后，最后一个孔的右边缘就是x_end
    # 2. 根据计算出的 x_start 和 x_end 来绘制外框
    total_width = x_end - x_start # 计算总宽度
    rect_center_x = (x_start + x_end) / 2 # 计算矩形轮廓的中心X坐标
    
    rectline_center(kicad_mod, rect_center_x, 0, w=total_width, h=max_diameter, layers=glayers_silk) # 绘制精确的外框
    
    return write_kicad_mod(kicad_mod, zip=zip) # 3. 生成最终文件```

def circle32(d=32,n=12,zip=0):
    import math # 导入数学库
    kicad_mod = new_kicad_mod(name=f'Hole_Line_d{d}_n{n}', w=0, h=0, text_at=[d/2 + 2, 0]) # 1. 初始化封装
    
    start_x = 0
    for i in range(n): # 3. 循环放置12个孔
        td=d #-0.04+0.02*n
        non_plated_hole(kicad_mod, x=start_x, y=0, d=td) # 在计算出的位置放置非金属化孔
        start_x = start_x + td # 计算当前孔的中心X坐标
        
    rectline_center(kicad_mod,d*(n/2)-d/2,0, w=d*n, h=d, layers=glayers_silk) # 4. 在丝印层绘制外形轮廓以供参考
    return write_kicad_mod(kicad_mod, zip=zip) # 5. 生成最终文件```

def jp_led_27(xm=248,wm=270, led_interval_y=10, led_interval_x=10, wire_width=0.8, zip=True): # 最终版 - 3-LED串联, X/Y间距分离
    kicad_mod = new_kicad_mod(name=f'jp_led_panel_3-series_{xm}x{wm}_ix{led_interval_x}_iy{led_interval_y}', w=xm, h=wm, text_at=[wm/2, -5],edge_layers=glayers_edge_fsilk) # 1. 初始化封装
    margin_x = max(xm/110, led_interval_x / 2) # 定义X方向边距
    # margin_y = led_interval_y / 2 # 定义Y方向边距
    pad_w, pad_h, pad_y_dist = 1.2, 1.6, 1.8 # 定义1206焊盘尺寸
    layers_cu_mask, layer_cu, layer_silk = ['F.Cu','F.Mask'], ['F.Cu'], ['F.SilkS'] # 定义图层
    grid_area_w = xm - 2 * (margin_x + led_interval_x) # 2. 动态计算尺寸
    grid_area_h = wm
    num_cols = int(grid_area_w / led_interval_x)-1
    num_rows = int(grid_area_h / led_interval_y)
    if num_rows % 3 != 0: num_rows = (num_rows // 3) * 3 # 确保总行数是3的倍数
    main_bus_width = min(wire_width + num_cols * 0.4, margin_x * 1.9) # 根据并联列数动态计算主总线宽度
    start_x = (xm - (num_cols - 1)*led_interval_x) / 2+ led_interval_x/10 # X轴起始点
    start_y = (wm - (num_rows - 1) * led_interval_y) / 2 # Y轴起始点
    v_plus_rail_x = xm - main_bus_width / 2 # 3. 创建电源总线
    rectangle_full(kicad_mod, v_plus_rail_x, wm / 2, w=main_bus_width, h=wm, layers=['F.Cu','B.Cu']) # 右侧V+总线
    gnd_rail_x = main_bus_width / 2
    rectangle_full(kicad_mod, gnd_rail_x, wm / 2, w=main_bus_width, h=wm, layers=['F.Cu','B.Cu']) # 左侧GND总线
    input_pad_h = 6.0 # 定义输入焊盘高度
    for input_y in [input_pad_h/2,wm-input_pad_h/2]: # 将输入焊盘定位在顶部
        dpx=2
        rectangle_full(kicad_mod, v_plus_rail_x, input_y, w=main_bus_width, h=input_pad_h, layers=['F.Cu','F.Mask','B.Mask','B.Cu']) # 右侧(+)输入焊盘
        km_text(kicad_mod, '+', at=[v_plus_rail_x - main_bus_width, input_y], size=[3, 3])
        plated_hole(kicad_mod,xm-dpx,input_y,1.4,size=3)
        
        rectangle_full(kicad_mod, gnd_rail_x, input_y, w=main_bus_width, h=input_pad_h, layers=['F.Cu','F.Mask','B.Mask','B.Cu']) # 左侧(-)输入焊盘
        km_text(kicad_mod, '-', at=[gnd_rail_x + main_bus_width, input_y], size=[2, 2])
        plated_hole(kicad_mod,dpx,input_y,1.4,size=3)
    for c in range(num_cols): # 4. 均匀网格布局与布线
        for r in range(0, num_rows, 3): # 循环步长为3
            if r + 2 >= num_rows: continue # 确保有足够的空间放置3个LED
            cx = start_x + c * led_interval_x # X坐标使用led_interval_x
            cy_centers = [start_y + (r + i) * led_interval_y for i in range(3)] # Y坐标使用led_interval_y
            dfix = 2 # 关键几何修正因子
            pads_y = [] # 存储6个焊盘的Y坐标
            for cy_center in cy_centers:
                pads_y.append(cy_center + pad_y_dist/2 - dfix) # Anode
                pads_y.append(cy_center - pad_y_dist/2 + dfix) # Cathode
            p1_y, p2_y, p3_y, p4_y, p5_y, p6_y = pads_y # 解包6个焊盘坐标
            for i, p_y in enumerate(pads_y): # a. 循环创建6个焊盘
                kicad_mod.append(Pad(number=f'P{c}_{r+i//2}_{i%2+1}', type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, at=[cx, p_y], size=[pad_w, pad_h], layers=layers_cu_mask))
            rect_w = pad_w + 0.6 # b. 循环创建3个LED的丝印
            rect_h = pad_y_dist + pad_h
            for i in range(3):
                rectangle_outline(kicad_mod,cx-rect_w/2, cy_centers[i] - rect_h/2, w=rect_w, h=rect_h, layers=layer_silk)
                circle(kicad_mod, cx - rect_w/2 - 0.5, pads_y[i*2+1], radius=0.2, layers=layer_silk)
            hw = led_interval_y/2 - (6/led_interval_y) # c. 精确布线, 水平线宽度取决于Y间距
            dhw = hw * 0.3
            d防短路= 1.5
            multi_dot_line(kicad_mod, [(v_plus_rail_x - main_bus_width / 2, p1_y-dhw), (cx+d防短路, p1_y-dhw)], width=hw, layers=layer_cu) # V+ Bus -> P1
            multi_dot_line(kicad_mod, [(cx, p2_y), (cx, p3_y)], width=wire_width, layers=layer_cu) # P2 -> P3
            multi_dot_line(kicad_mod, [(cx, p4_y), (cx, p5_y)], width=wire_width, layers=layer_cu) # P4 -> P5
            multi_dot_line(kicad_mod, [(cx-d防短路, p6_y+dhw), (gnd_rail_x + main_bus_width / 2, p6_y+dhw)], width=hw, layers=layer_cu) # P6 -> GND Bus
            # if cx > start_x: # 在列之间添加固定/散热孔
                # non_plated_hole(kicad_mod, cx - led_interval_x * 0.5, cy_centers[1], 0.9)
                
    dy18650_box=53.2 #53.72
    two_hole(kicad_mod,xm/2,dy18650_box,20,2.9,angle=0,holes=[0,1,],func=non_plated_hole)#,func=0 force reload   
    two_hole(kicad_mod,xm/2,wm-dy18650_box,20,2.9,angle=0,holes=[0,1,],func=non_plated_hole)#,func=0 force reload   
                
    multi_dot_line(kicad_mod, [(xm,-6), (xm,wm+6)], width=12, layers=glayers_silk) # v+
    
    for yi in range(10):
        non_plated_hole(kicad_mod,5.7,2.5+ yi*led_interval_y*3,1.5)
    
    return write_kicad_mod(kicad_mod, zip=zip) # 5. 生成最终文件  


def plug3_220v(W=26.5,H=18,pin_length=5,zip=True):
    kicad_mod = new_kicad_mod(name=f'Socket_IEC_C14_{W}x{H}', w=W, h=H, text_at=[0, 15]) # 1. 初始化封装
    # shell_ # 核心尺寸：外壳宽度
    # shell_h = 18.0 # 核心尺寸：外壳高度
    top_edge_length = 16.0 # 核心尺寸：切角后顶部边长
    pin_thickness = 0.9 # 核心尺寸：引脚厚度
    # pin_length = 12.3 # 核心尺寸：引脚长度
    pin_spacing_horiz = 14.0 # 核心尺寸：下方两引脚间距
    pin_spacing_vert = 5.0 # 核心尺寸：上下引脚垂直距离
    cx, cy = W/2, H/2 # 将电气中心（引脚组的中心）设为坐标原点(0,0)
    drill_slot_size = [pin_thickness, pin_length] # 2. 定义焊盘和槽孔尺寸
    pad_size = [drill_slot_size[0] + 1.6, drill_slot_size[1] + 1.6] # 焊盘尺寸在槽孔基础上增加铜环
    p_gnd_y = cy + pin_spacing_vert / 2 # 3. 计算引脚的精确位置
    p_ln_y = cy - pin_spacing_vert / 2
    p_l_x = cx - pin_spacing_horiz / 2
    p_n_x = cx + pin_spacing_horiz / 2
    kicad_mod.append(Pad(number='L', type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, at=[p_l_x, p_ln_y], size=pad_size, drill=drill_slot_size, layers=Pad.LAYERS_THT)) # 创建L引脚焊盘
    kicad_mod.append(Pad(number='N', type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, at=[p_n_x, p_ln_y], size=pad_size, drill=drill_slot_size, layers=Pad.LAYERS_THT)) # 创建N引脚焊盘
    kicad_mod.append(Pad(number='G', type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, at=[cx, p_gnd_y], size=pad_size, drill=drill_slot_size, layers=Pad.LAYERS_THT)) # 创建G引脚焊盘
    # cutout_offset_y =0#  - pin_spacing_vert / 2 - shell_h / 2 - 1.5 #+cy# 4. **修正**：将开槽的Y轴中心定位在L/N引脚的下方
    half_w, half_h = W / 2, H / 2
    cutout_corner_cut_x = (W - top_edge_length) / 2 # **修正**：根据顶部边长精确计算切角偏移
    cutout_nodes = [ # **修正**：重新定义顶点，使切角在顶部，并翻转Y轴
        # (cx - half_w, cy - half_h),
        (cx + half_w, cy - half_h),
        (cx + half_w, cy + half_h - cutout_corner_cut_x), # Y轴切角高度通常与X偏移相同
        (cx + half_w - cutout_corner_cut_x, cy + half_h),
        (cx - half_w + cutout_corner_cut_x, cy + half_h),
        (cx - half_w, cy + half_h - cutout_corner_cut_x),
        (cx - half_w, cy - half_h) # 闭合路径
    ]
    multi_dot_line(kicad_mod, cutout_nodes, layers=glayers_edge_pure, width=1) # 在Edge.Cuts层绘制开槽
    multi_dot_line(kicad_mod, [(cx - half_w, cy - half_h),(cx + half_w, cy - half_h),], layers=glayers_edge_pure, width=1,segments=1,segments_d=2) # 断续 开槽
    return write_kicad_mod(kicad_mod, zip=zip)

def parallel_18650(wm=100,hm=100,spring=3.1,spring_D=0.7,zip=True): # parallel connection 并联
    kicad_mod = new_kicad_mod(w=wm, h=hm,text_at=[9,-2], )
    def one(x,y,spring=spring,D=0.8,L=65.3):
        LA=L+10
        rectline_center(kicad_mod,x,y,w=LA,h=18.3,layers=glayers_edge_pure)
        
        rectangle_full(kicad_mod,x-44,y,layers=('F.Cu','B.Cu',),w=11,h=20)
        rectangle_full(kicad_mod,x+44,y,layers=('F.Cu','B.Cu',),w=11,h=20)
        
        for xi in range(3):# 
            dx=LA/2+1.8+xi*spring
            dy=3.5-spring_D/2
            
            size=spring-0.1
            plated_hole(kicad_mod,x-dx-1,y+dy,D,size=size )
            plated_hole(kicad_mod,x-dx+1,y-dy,D,size=size ) # 左上
            
            
            plated_hole(kicad_mod,x+dx-1,y+dy,D,size=size )
            plated_hole(kicad_mod,x+dx+1,y-dy,D,size=size )
        # dx=35.1+4+0.9+2*spring    
        dx=LA/2+1.8+3*spring    
        plated_hole(kicad_mod,x-dx+1,y-dy,D,size=size )
        plated_hole(kicad_mod,x+dx-1,y+dy,D,size=size )
                
    x=wm/2
    m=4
    mi=hm/m
    for yi in range(m):
        y=mi/2+mi*yi
        if yi==3:
            # one(x+10,y,spring=spring-yi*0.1,D=0.85+yi*0.05,L=56)
            continue
        one(x,y,spring=spring-yi*0.1,D=0.85+yi*0.05)
    
    for y in [25,75]:
        multi_dot_line(kicad_mod,[(5,y-5),(5,y-1),(50-7,y-1)],width=1,layers=('F.Cu','B.Cu',))  
        multi_dot_line(kicad_mod,[(95,y-5),(95,y-1),(50+7,y-1)],width=1,layers=('F.Cu','B.Cu',))  
        plated_hole(kicad_mod,50+7,y,1.35,size=2 )
        plated_hole(kicad_mod,50-7,y,1.35,size=2,shape=Pad.SHAPE_RECT )
        
        plated_hole(kicad_mod,50+3.75,y,1.35,size=2 )
        plated_hole(kicad_mod,50-3.75,y,1.35,size=2,shape=Pad.SHAPE_RECT  )
    
    return write_kicad_mod(kicad_mod,zip=zip)
    
def rv097ns_up(wm=9.5,hm=11.4,z=0,edge=None):
    kicad_mod = new_kicad_mod(w=wm, h=hm+5,text_at=[9,-2], )
    x=wm/2
    y=hm/2
    hq=0.2
    rectline_center(kicad_mod,x,y      ,w=wm,h=hm,layers=glayers_edge_pure)
    rectline_center(kicad_mod,x,hm+hq/2,w=2,h=hq,layers=glayers_edge_pure)
    
    for i in range(-1,2):
        xi=x+i*2.5
        kicad_mod.append(Pad(number=i+2,type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
				at=[xi,hm+2.6], size=0.9, drill=0, layers=['*.Cu','*.Mask',]))
        for yi in range(10):#ref:  # 尾4p
            plated_hole(kicad_mod,xi,hm+yi*0.3,0.9,size=0.9 )
        
    return write_kicad_mod(kicad_mod,zip=z)

def rv097ns_cut_pcb(wm=9.6,hm=7.1,z=0,edge=None):
    #stm32f103_board
    if edge:edge=glayers_edge_pure # 对于kicad 3d预览，没用，还是无法看出全貌
    else   :edge=('F.SilkS',)
    
    kicad_mod = new_kicad_mod(w=wm+1, h=hm+15,text_at=[9,-2],edge_layers=edge)
    
    x=wm/2
    y=hm/2
    
    for i in range(-1,2):
        xi=x+i*2.5
        rectangle_full(kicad_mod,xi,-2,layers=('B.Cu',),w=1.2,h=4)
        rectangle_full(kicad_mod,xi,-1.5,layers=('B.Mask',),w=1,h=3)
        kicad_mod.append(Pad(number=i+2,type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
				at=[xi,-1.5], size=1, drill=0, layers=['B.Cu','B.Mask',]))
    
    hq=0.7
    rectline_center(kicad_mod,x,hm+hq/2,w=2,h=hq,layers=glayers_edge_pure)

    rectline_center(kicad_mod,x,y      ,w=wm,h=hm,layers=glayers_edge_pure)
    
    return write_kicad_mod(kicad_mod,zip=z)

def socket_916(wm=56.5,hm=48.5,z=0):
    ''' 三面七孔插座 型号916  10A 250V '''
    kicad_mod = new_kicad_mod(w=wm, h=hm,text_at=[9,-2])
    x=wm/2
    y=hm/2
    
    
    hole_rect_center(kicad_mod,x,y,40,side_len_y=30,d=3.1,holes=[0,2,],angle=0)   
    two_hole(kicad_mod,x,y-7,40,hole=2.9)
    
    return write_kicad_mod(kicad_mod,zip=z)
    
    
def miniature_circuit_breaker_C1(wm=73.5,hm=17.88,z=0):
    kicad_mod = new_kicad_mod(w=wm, h=hm,text_at=[9,-2])
    x=wm/2
    y=hm/2
    # dx=
    dc=7
    rectangle_full(kicad_mod,0-dc/2,y,layers=glayers_FB_Cu,w=dc,h=3)
    rectangle_full(kicad_mod,0-dc/2,y,layers=glayers_FB_Mask,w=dc,h=1)
    
    ec=glayers_edge_pure+glayers_silk
    du=20.6
    # du=20.65
    
    rectline_center(kicad_mod,du/2,y,w=du,h=hm,layers=glayers_Cmts) # up on
 
    
    u2=1
    rectline(kicad_mod,start=[0,0],end=[du-u2,hm],layers=ec) # up on
    u2h=4.1
    rectline_center(kicad_mod,du-u2/2,u2h/2,w=u2,h=u2h,layers=ec) # up on
    rectline_center(kicad_mod,du-u2/2,hm-u2h/2,w=u2,h=u2h,layers=ec) # up on
    
    
    hx=24.2
    dhy=2.5
    non_plated_hole(kicad_mod,hx,dhy,2.5)
    non_plated_hole(kicad_mod,hx,hm-dhy,2.5)
    
    d=17
    rectline_center(kicad_mod,wm-d/2,y,w=d,h=hm,layers=ec) # down off
    d11=0.3
    rectline_center(kicad_mod,wm-d-d11/2,y,w=d11,h=11.3,layers=ec) # down off
   
    # rectline_center(kicad_mod,wm-8,y,w=26,h=11.3,layers=glayers_edge_pure) # down off
    non_plated_hole(kicad_mod,wm+7.3-1.4-2,y,3.9)
    
    
    return write_kicad_mod(kicad_mod,zip=z)
    
    
def motor_220v_4mm(kicad_mod,x,y,angle=0,hole=17.4,):
    ''' 外径最小 42.2  ，42.1  放不进'''
    if hole>17:
        # hole=17.4
        m4=3.9
        m5=5
        cs=[0.1,4,12,17.5,42.2]
    else:
        #hole=3.99
        m4=1
        m5=1
        cs=[42.2]
    non_plated_hole(kicad_mod,x,y,hole)
    circle(kicad_mod,x,y,cs)
    xd=29/2
    
    non_plated_hole(kicad_mod,*rotate_point(x-xd,y,angle,x,y),m4)
    non_plated_hole(kicad_mod,*rotate_point(x+xd,y,angle,x,y),m4)
    
    # non_plated_hole(kicad_mod,*rotate_point(x,y-12.8,angle,x,y),m5) # 上
    non_plated_hole(kicad_mod,*rotate_point(x,y-12.6,angle,x,y),m5) # 上
    
    
    if 0:
        hole_rect_center(kicad_mod,x,y,18.5,side_len_y=16.5,d=1,holes=[0,1,2,3],angle=angle)   
        c4=31/1.4142
        for i in range(3):
            hole_rect_center(kicad_mod,x,y,c4,side_len_y=c4,d=1,holes=[0,1,2,3],angle=angle-7-i)  
        
def hgr20_flange_block(kicad_mod,x,y,angle=0,hole=5.9,holes=(0,1,2,3),zip=0):
    '''  hgr20_flange_block 法兰款'''
    write_kicad=False
    if not kicad_mod:
        kicad_mod = new_kicad_mod(w=100, h=100)
        write_kicad = True
    rectline_center(kicad_mod,x,y,76,43,crosshair=1,layers=glayers_F_Cu+glayers_silk,angle=angle)    
    rectline_center(kicad_mod,x,y,50.9,63,crosshair=1,layers=glayers_F_Cu,angle=angle)    
    # rectline_center(kicad_mod,x,y,76,63,crosshair=1,layers=glayers_silk,angle=angle)    
    # hole_rect_center(kicad_mod,0,0,side_len_x=80,side_len_y=70,d=1)
    hole_rect(kicad_mod,x,y,side_len_x=40,side_len_y=53,d=hole,angle=angle,holes=holes)
    if write_kicad:return write_kicad_mod(kicad_mod,zip=zip)
HGW20CC=hgr20_flange_block    
    
def hgr20_block(kicad_mod,x,y,angle=0,hole=4.9,holes=(0,1,2,3),write_kicad=False, mid_hole=False):
    '''  hgr20_block 普通 无法兰'''
    if not kicad_mod:
        kicad_mod = new_kicad_mod(w=100, h=100)
        write_kicad = False
    rectline_center(kicad_mod,x,y,75,44,crosshair=1,layers=glayers_F_Cu,angle=angle)    
    rectline_center(kicad_mod,x,y,78,44,crosshair=1,layers=glayers_silk,angle=angle)    
    # hole_rect_center(kicad_mod,40,30,side_len_x=80,side_len_y=60,d=1)
    hole_rect(kicad_mod,x,y,side_len_x=36,side_len_y=32,d=hole,angle=angle,holes=holes)
    
    if mid_hole:
        if not py.isnum(mid_hole):mid_hole=2
        non_plated_hole(kicad_mod, *rotate_point(x,y,angle, x, y), mid_hole)
    
    if write_kicad:kicad_mod.write(f"HGR20_{h}mm.kicad_mod")
    
    
def hgr20_rail(kicad_mod,x,y,angle=0,h=300, hole=5.9, mid_hole=None, write_kicad=False, z=0):
    ''' 生成HGR20直线导轨封装  not hgr20_block '''
    if not kicad_mod:
        kicad_mod = new_kicad_mod(w=wm, h=hm)
        write_kicad = False
    
    # 绘制20mm宽导轨外形轮廓
    rectline_center(kicad_mod, x, y, w=h, h=20, width=0.012, angle=angle, layers=glayers_silk)
    
    # 计算安装孔数量（mm间距）
    n = h // 60
    if n % 2 == 1:  # 保证偶数对称分布
        n += 1
    
    # 生成对称安装孔
    for i in range(n//2):
        offset = i * 60  # 安装孔间距
        
        # 中间特殊孔处理
        if i == 0 and mid_hole:
            non_plated_hole(kicad_mod, *rotate_point(x,y,angle, x, y), mid_hole)
            continue
            
        # 正负方向打孔
        non_plated_hole(kicad_mod, *rotate_point(x+offset,y, angle, x, y), hole)
        non_plated_hole(kicad_mod, *rotate_point(x-offset,y, angle, x, y), hole)
    
    # 添加中心标记（含导轨宽度指示）
    if hole:circle(kicad_mod, x, y, diameter=[0.1, 1, 2, 20], crosshair=1, layers=glayers_Cmts)

    # 自动输出封装文件
    if write_kicad:kicad_mod.write(f"HGR20_{h}mm.kicad_mod")
    
def chainwheel_04c(kicad_mod,x,y,hole=10,n=17):
    '''dnD={
11:[25.5],    
14:[31.5],    
15:[33.5],    
16:[35.5],    
17:[37.5],    
    }
    
dnW={
17:40
}    
    
    '''
    non_plated_hole(kicad_mod,x,y,hole)   
    D=3.5+2*n
    W=3.5+2*n+2
    bw=W/2
    
    circle(kicad_mod,x,y, diameter=[hole+0.2,25,D,W], crosshair=0, layers=glayers_silk)  
    for yw in [y+bw,y-bw]:
        multi_dot_line(kicad_mod,[(-11,yw),(x,yw)],width=0.01,layers='F.SilkS')  
    
def two_hole(kicad_mod,x,y,distance,hole=5.9,angle=0,hole_func=py.No('hole_func=non_plated_hole'),holes=None,line=False,**ka):
    ''' zcz  '''
    if not hole_func:hole_func=non_plated_hole
    distance=U.get_duplicated_kargs(ka,'distance','d','D',default=distance)#不可能同时取到不同值
    r=distance/2
    if U.len(hole)!=2:
        hole=[hole,hole]
    x0,y0=rotate_point(x-r,y,angle,x,y)
    if holes and 0 not in holes:pass
    else:    
        hole_func(kicad_mod,x0,y0,hole[0])

    x1,y1=rotate_point(x+r,y,angle,x,y)
    if holes and 1 not in holes:pass
    else:
        hole_func(kicad_mod,x1,y1,hole[1])
    
    if line:
        multi_dot_line(kicad_mod,[(x0,y0),(x1,y1)],width=0.1,layers=glayers_silk)
        multi_dot_line(kicad_mod,[(x,y+distance/10),(x,y-distance/10)],width=0.1,layers=glayers_silk)
    
    return (x0,y0),(x1,y1)
    
def gear_1m_70_10(motor_hole=17.4,long_hole=False,z=0):
    ''' chain wheel '''
    kicad_mod = new_kicad_mod(name=f'gear_1m_70_10={motor_hole}',w=100, h=100, text_at=(10,1),edge_layers=glayers_edge_fsilk)
    
    dg=1*(70+10)/2
    
    
    
    y=36+12+4.5  #zcz10_45 max 8,motor max 11
    x=33#37.4
    circle(kicad_mod,x,y, diameter=[0.1,10,15,67.5,72], crosshair=0, layers=glayers_silk)
    chainwheel_04c(kicad_mod,x,y,n=15)
    motor_220v_4mm(kicad_mod,*rotate_point(x+dg,y,-0,x,y),hole=motor_hole,angle=-90)
    # a=15.8
    # motor_220v_4mm(kicad_mod,*rotate_point(x+dg,y,a,x,y),hole=1,angle=a+180)
    # motor_220v_4mm(kicad_mod,*rotate_point(x+dg,y,-a,x,y),hole=1,angle=-a)
    
    zcz10=46
    zcz_15=53
    
    # two_hole(kicad_mod,x,y,distance=zcz10,hole=4.9,angle=-45,hole_func=circle)
    #def two_hole(kicad_mod,x,y,distance=zcz10,angle=-33)
    # two_hole(kicad_mod,x,y,distance=zcz10,angle=-40,hole=1,hole_func=circle)
    if motor_hole>40:
        p0,p1=two_hole(kicad_mod,x,y,distance=zcz10,angle=-77.3,hole=5,hole_func=non_plated_hole)
    else:    
        two_hole(kicad_mod,x,y,distance=zcz10,angle=-45,hole=5,hole_func=non_plated_hole)
        p1=(38.05646270011526, 30.0627054892453)
    # U.set(1,p1)
    
    
    # hgr20_rail(kicad_mod,20,10,angle=0)
    yr=90#y+42 #
    hgr20_rail(kicad_mod,20,yr,angle=0)
    rectline_center(kicad_mod,x+2,yr,78,44,crosshair=1,layers=glayers_Cmts+glayers_silk)
    # rectline_center(kicad_mod,x+2,10,78,44,crosshair=1,layers=glayers_Cmts)
    
    # hole_rect_center(kicad_mod,50,50,side_len_x=80,side_len_y=60,d=1)
    
    
    if long_hole:
        nh=2
        for i in range(-nh,nh+1):
            non_plated_hole(kicad_mod,20+i*2,90,5.9)
            non_plated_hole(kicad_mod,80+i*2,90,5.9)
            
    xb=p1[0]-16#28.5
    yb=p1[1]+18
    hgr20_rail(kicad_mod,xb,yb,hole=0,angle=90)
    
    if motor_hole>40:
        hgr20_block(kicad_mod,xb,yb,angle=90,hole=4.9,holes=[0,1,2])
        hgr20_block(kicad_mod,xb,yb,angle=90,hole=4.2,holes=[3])
    # hgr20_block(kicad_mod,28,48,angle=90,hole=4.9)
    # non_plated_hole(kicad_mod,xb,6,1)
    non_plated_hole(kicad_mod,6,6,5.9)#xb-15
    non_plated_hole(kicad_mod,6+(xb-6)*2,6,3.9)#xb-15
    non_plated_hole(kicad_mod,80,10,5.9) # 左上
    non_plated_hole(kicad_mod,20,10,5) # 左上
    
    # non_plated_hole(kicad_mod,20,30,1) # 竖轨
    
    
    return write_kicad_mod(kicad_mod,zip=z)



    
def jp65_heatbed(W=650, H=118, w=0.4, interval=0.2, margin=3,margin_w=7, z=0):
    ''' hotbed heatbed  297 '''
    kicad_mod = new_kicad_mod(w=W, h=H, text_at=(10,1),edge_layers=glayers_edge_fsilk)
    for x in [5,6,7,8,9,10]:    
        multi_dot_line(kicad_mod,[(x,0),(x,H)],width=0.01,layers='F.SilkS')  
        
    s = w + interval
    
    # 配置参数
    sensor_width = 22
    eff_H = H - 2*margin
    loop_count = int(eff_H // (2*s))
    actual_eff_H = loop_count * 2*s
    total_height = actual_eff_H + 2*margin
    
    # 开口范围控制
    mid = loop_count // 2
    open_range = range(mid - 3, mid + 3)  # 控制开口覆盖层数
    
    # Z形路径模板
    left_start = margin_w + 3  # 初始左侧偏移
    right = W - margin_w
    current_y = margin+(w+interval)/2 #qgb为了两边对称
    points = []
    
    sa,sb=H/2-4.5,H/2+4.5
    is_once=1
    for i in range(loop_count):
        left = left_start
        # 在开口范围内偏移左侧起点
        if sa<current_y<sb:
            left += sensor_width
        
        # 构建Z形路径
        zrow = [
            (left, current_y),            # 起点
            (right, current_y),            # 右点
            (right, current_y + s),        # 右上点
            (left, current_y + s)          # 左回点
        ]
        # if i==open_range.stop:zrow[0]=(left_start+sensor_width,current_y) # qgb 加的，不然多出一条
        
        if current_y>sb and is_once:
            is_once=0
            zrow[0]=(left_start+sensor_width,current_y) # qgb 加的，不然多出一条
        # 正向走线
        points.append((zrow[0], zrow[1]))
        # 右侧垂直
        points.append((zrow[1], zrow[2]))
        # 反向走线
        points.append((zrow[2], zrow[3]))
        # 左侧垂直（非末层）
        if i < loop_count - 1:
            points.append((zrow[3], (zrow[3][0], current_y + 2*s)))
        
        # 特殊处理开口起始层
        if i == open_range.start:
            # 补充开口左侧走线
            points.append(((left_start, current_y), (left, current_y)))
        
        current_y += 2*s
    
    
    # 生成走线
        
    # multi_dot_line(kicad_mod,points,width=w,layers=mlayers)    
    for start, end in points:
        for ilayer in ['F.Cu']:
            kicad_mod.append(Line(start=start, end=end, layer=ilayer, width=w))
            
    # dw=10  
    # wf=W-7-dw
    # hf=H-margin*2
    # serpentine_line(kicad_mod,x=dw+wf/2,y=margin-0.51+hf/2,w=hf,h=wf,angle=-90,wire_width=w,interval=interval)
    # return write_kicad_mod(kicad_mod,zip=0)
        
    dsy=H/2+1    
    rectline_center(kicad_mod,sensor_width-2,dsy,w=sensor_width,h=7.5,width=0.01,layers=glayers_edge_pure) # 开槽
    
    mlayers=['F.Cu',]
    # 焊盘配置
    pad_offset = 0 #值越小，越往中间靠拢
    fka=py.dict(layers=mlayers,w=6,h=w+0.1)
    rectangle_full(kicad_mod,left_start + pad_offset, margin - pad_offset,**fka)
    rectangle_full(kicad_mod,left_start + pad_offset, total_height - margin + pad_offset,**fka)
    
    pad_offset=-interval
    fka=py.dict(layers=mlayers,w=6,h=w)
    rectangle_full(kicad_mod,left_start + pad_offset, margin - pad_offset,**fka)
    rectangle_full(kicad_mod,left_start + pad_offset, total_height - margin + pad_offset,**fka)
    
    a=2.8
    lx2=left_start-2
    fka=py.dict(layers=mlayers,w=2.5,h=5)
    rectangle_full(kicad_mod,lx2,margin+a,**fka)
    rectangle_full(kicad_mod,lx2,total_height - margin-a,**fka)
    
    fka=py.dict(layers=['F.Cu','F.Mask'],w=1.3,h=4)
    rectangle_full(kicad_mod,lx2,total_height - margin-a,**fka)
    if dsy<66:
        rectangle_full(kicad_mod,lx2,margin+a,**fka)
    else:    
        rectangle_full(kicad_mod,lx2,dsy-60,**fka)
        multi_dot_line(kicad_mod,[(lx2,margin+a),(lx2,dsy-60)],width=1.3,layers='F.Cu'   )
        # rectangle_full(kicad_mod,lx2,dsy+60,**fka)
        # multi_dot_line(kicad_mod,[(lx2,total_height-(margin+a)),(lx2,dsy+60)],width=1.3,layers='F.Cu'   )
    
    hn=H//25
    hn_mid=hn//2
    ydh=(H-hn*25)/2
    if 100<H<125 and hn==4:hn=5# 顺序不能乱
    if not ydh:ydh=25/2
    if hn>5 and hn%2==0:his=[hn_mid-1,hn_mid]
    else:his=[hn_mid]
    # U.set(3,[hn,hn_mid,ydh,his,dsy])
    for i in range(hn):
        m3=2.85
        non_plated_hole(kicad_mod,W-margin_w/2,ydh+25*i,m3)
        
        if i in his:m3=1.3#mid
        non_plated_hole(kicad_mod,margin_w/2,ydh+25*i,m3)
    
    dh=margin/2
    dx=margin_w/2+1
    dx=25
    for i in range(W//25):
        if W-i*25<=dx:continue
        non_plated_hole(kicad_mod,dx+25*i,dh,1)
        non_plated_hole(kicad_mod,dx+25*i,H-dh,1)
          
        
    if W==650:
        for i in [-1,25]:
            circle(kicad_mod,dx+i*25,dh,[1,3])
        for i in range(hn):
            # circle(kicad_mod,10.5,ydh+25*i,[1,3])
            circle(kicad_mod,dx+25*25+1,ydh+25*i,[1,3])
            
            
    mb=margin+1.5
    current_x = 32  # X轴当前坐标
    loop_count = int((W-current_x-margin_w) // (2*s))
    points=[]
    for i in range(loop_count):
        # 垂直Z形路径（上下往复）
        zrow = [
            (current_x, margin),            # 上点
            (current_x, H - mb),        # 下点 
            (current_x + s, H - mb),    # 右下点
            (current_x + s, margin)         # 右上点
        ]
        
        # 向下走线
        points.append((zrow[0], zrow[1]))
        # 向右过渡
        points.append((zrow[1], zrow[2]))
        # 向上走线
        points.append((zrow[2], zrow[3]))
        # 向右过渡（非末层）
        points.append((zrow[3], (current_x + 2*s, margin)))
        current_x += 2*s  # X轴步进
        if i==loop_count - 1:
            yb=H-margin-0.7
            points.append([(current_x,margin),(current_x,yb)])
            points.append([(current_x,yb),(32-s,yb)])
            
    bl2=['B.Cu']
    for start, end in points:
        for ilayer in bl2:
            kicad_mod.append(Line(start=start, end=end, layer=ilayer, width=w))
                    
    dw=margin_w+2.9
    wf=23.5
    hf=52.5
    serpentine_line(kicad_mod,x=dw+wf/2,y=3+hf/2,w=wf,h=hf,angle=0,wire_width=w,interval=interval,layers=bl2,pop_indexes=[-1,-1])
    rectangle_full(kicad_mod,8.15,6.4,layers=bl2,w=4,h=7)# 底 上
    
    # dw=
    dw-=0.6
    hf-=2.8
    serpentine_line(kicad_mod,x=(dw+wf/2),y=(H-0.72)-(3+hf/2),w=wf,h=hf,angle=0,wire_width=w,interval=interval,layers=bl2,pop_indexes=[0,-1])
    rectangle_full(kicad_mod,8.15,(H-0.72)-6.4,layers=bl2,w=4,h=7)
    return write_kicad_mod(kicad_mod,zip=0)            
            
    
    return write_kicad_mod(kicad_mod, zip=z)
    

def stepper_mgn12(W=100,H=100,dy=0,z=0):
    kicad_mod = new_kicad_mod(w=W,h=H,text_at=(4,-3))
    x=W/2
    for i in range(3):
        yi=80+i*5
        if yi==95:continue
        non_plated_hole(kicad_mod,x,yi,1)
    multi_dot_line(kicad_mod,[(x,0),(x,101)],width=0.01,layers=glayers_silk+glayers_Cmts)    
    
    
    step_motor_42(kicad_mod,x,42/2,d=4.99,hole_func=circle)
    step_motor_42(kicad_mod,x,42/1.414,d=4.99,angle=45)
    step_motor_57(kicad_mod,x,56.6/2,d=6.35,hole_func=circle)
    step_motor_57(kicad_mod,x,56.6/1.414,d=6.35,angle=45)
    
    gt17_d=9.7
    gt20_d=12+1.4#皮带厚度, 皮带齿高0.7
    d9gt=(gt20_d-9)/2-1.4
    xm=x+(gt20_d/2+9/2+10) #+1.4#皮带厚度
    y=50-12.5-7.78
    
    mgn12c_rail(kicad_mod,xm,y,h=200)
    rectline_center(kicad_mod,xm,50,20,200,crosshair=1,layers=glayers_Cmts+glayers_silk)
    
    xm=x-(gt20_d/2+9/2+10)
    mgn12c_rail(kicad_mod,xm,y,h=200,hole=4.9,mid_hole=2.9)
    
    y=95
    non_plated_hole(kicad_mod,x-d9gt,y,2.9)
    circle(kicad_mod,x-d9gt,y,d=[3,9],layers=glayers_F_Cu)
    
    return write_kicad_mod(kicad_mod,zip=z)

    # non_plated_hole(kicad_mod,x,y,2.9)
    # circle(kicad_mod,x,y,d=[3,12,gt20_d],layers=glayers_silk+glayers_Cmts)
    
    
    xa=xm-10
    # circle(kicad_mod,xa,y,d=[3,9],layers=glayers_silk)
    multi_dot_line(kicad_mod,[(0,y),(100,y)],width=0.01,layers=glayers_silk)
    non_plated_hole(kicad_mod,xa,     y-4,2.9)
    non_plated_hole(kicad_mod,xa-1.47,y,2.9)
    
    
    y=y-10
    non_plated_hole(kicad_mod,x,y,2.9)
    circle(kicad_mod,x,y,d=[3,12,gt20_d],layers=glayers_Cmts)
    
    
    mgn12c_block(kicad_mod,17.35,100-13.5)
    mgn12c_rail (kicad_mod,17.35,100-27-12.5)
    
    
    return write_kicad_mod(kicad_mod,zip=z)

def jp30x20_mgn12_heatbed(W=297,H=200,wd=277,z=0):
    kicad_mod = new_kicad_mod(w=W,h=H,text_at=(4,-3))
    def non_plated_hole(kicad_mod,x,y,d=0,width=0.001):
        kicad_mod.append(KicadModTree.Circle(center=[x,y],radius=d/2, layer='Edge.Cuts',width=width))
        qgb.kicad.non_plated_hole(kicad_mod,x,y,d=d)
    
    
    bd=(W-wd)/2
    d3=3.4    
    
    for i in range(8):
        # for xi in [bd,W-bd]:
        yi=12.5+i*25
        non_plated_hole(kicad_mod,bd,yi,2.9)
        non_plated_hole(kicad_mod,W-bd,yi,2.9)
        
        tbd=bd-2
        rectangle_full(kicad_mod,W-tbd/2,yi,tbd,d3)
        
        if i==0:yi+=1
        if i==7:yi-=1
        rectangle_full(kicad_mod,tbd/2,yi,tbd,d3)
        
        
    w=0.9
    interval=0.2
    max=200
    dy_start=9
    silk_line=True
    d=w+interval
    M=py.int(max/(2*d))-1
    # d=w
    # x0=d*2
    # x0=w
    x0=bd+2.5
    x0=y0=(max-((M+1)*2*d-interval))/2+ w/2
    # x0=y0=0
    # y_mid=50
    
    zrow=(    [x0,y0],[W-x0,y0],    # 0   1
                    [W-x0,y0+d],# 3   2
            [x0,y0+d],            # 4
            [x0,y0+d+d],)        # 
        
    for i in range(M+1,):
        # kicad_mod.append(KicadModTree.Text(type='value', text=f'{i}', at=[-3,M*2*d],size=[1,1],layer='F.SilkS'))
        
        z0=None
        for n,z in py.enumerate(zrow):
            z=U.deepcopy(z)
            z[1]+=i*d*2
            
            if abs(z[1]%25-12.5)<d3 and n in (1,2): # 螺丝右
                z[0]-=(bd+2)
            if abs(z[1]%25-12.5)<d3 and n in (3,4,0): # 螺丝左
                z[0]+=(bd+2)
            
            if (abs(z[1])<dy_start or abs(H-z[1])<dy_start ) and n in (3,4,0,): # start input 左
                z[0]+=(dy_start*1.33)
            
            # if i in (M//2,) and n in (3,4): # 螺丝 21 M=43 
                # z[0]+=d*2
            
            
            if i==M and n==4:break
            
            
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
                        zs[0]=W
                        if i==0:zs0[0]=0
                    if n==3:
                        zs0[0]-=dxs
                        zs[0]=0
                        if i==M:zs0[0]=W
                    
                    kicad_mod.append(KicadModTree.Line(start=zs0, end=zs, layer='F.SilkS',width=sw_interval))
            z0=z
        
    dp=1.35
    # x,y=dy_start/2,(dy_start/2)*0.9
    # circle(kicad_mod,x,y,5,width=1,layers=['F.Cu', 'F.Mask'])
    # rectangle_full(kicad_mod,dy_start*0.66,dp-0.18,1.5,0.8)    
    # rectangle_full(kicad_mod,dy_start*1.06,dp,dy_start*0.8,1.15)
    
    x=y=(dy_start/2)*1.4
    y-=0.2
    # for y in [y-0.2,W-y+0.2]:
    circle(kicad_mod,x,y,dy_start,width=1,layers=['F.Cu', 'F.Mask'])
    rectangle_full(kicad_mod,dy_start*0.66,dp-0.18,2,0.8)    
    rectangle_full(kicad_mod,dy_start,dp,dy_start,1.15)    
    non_plated_hole(kicad_mod,x,y,5)
    
    y=H-(dy_start/2)*1.4+0.2
    circle(kicad_mod,x,y,dy_start,width=1,layers=['F.Cu', 'F.Mask'])
    rectangle_full(kicad_mod,dy_start*0.66,H-dp+0.18,2,0.8)    
    rectangle_full(kicad_mod,dy_start,H-dp,dy_start,1.15)    
    non_plated_hole(kicad_mod,x,y,5)
    
    
    
    # rectangle_full(kicad_mod,3,2.2,4,3,layers=['F.Cu', 'F.Mask'])    
    # rectangle_full(kicad_mod,5,dp,4,1.15)    
    # rectangle_full(kicad_mod,3,H-2.2,4,3,layers=['F.Cu', 'F.Mask'])    
    # rectangle_full(kicad_mod,5,H-dp,4,1.15)    
    
    return write_kicad_mod(kicad_mod,zip=z)
    
def tc_2020_wheel(W=100,H=100,z=0):
    ''' 36.7-23.2 == 13.5  # 6.75 '''
    kicad_mod = new_kicad_mod(w=W,h=H)
    
    # multi_dot_line(kicad_mod,[(0,0),(99,99)],width=0.01,layers=glayers_silk,segments=6,segments_d=1)    
    crosshair(kicad_mod,50,10,w=100,h=21)
    # for i in range(5):
        # ntc_2020(kicad_mod,11.2+i*20,30,hole=2.9,dh=i,angle=i*20)
    ka2020=dict(hole=2.9,layers=glayers_silk)
    last_ka=dict(hole2=3.9,dh2=-2.3)
    dx=11.2
    dy=10.1
    
    a=-90
    y=dy
    ntc_2020(kicad_mod,dx,y   ,dh=2.9,angle=a,**ka2020)
    ntc_2020(kicad_mod,40-dx,y,dh=3,angle=a,**ka2020)
    
    ntc_2020(kicad_mod,100-(40-dx),y,dh=3.1,angle=a,**ka2020)
    ntc_2020(kicad_mod,100-dx,y,     dh=3.2,angle=a,**ka2020)
        
    multi_dot_line(kicad_mod,[(41.5,0),(41.5,13),],width=3,layers=glayers_edge_pure)    
    multi_dot_line(kicad_mod,[(58.5,0),(58.5,13),],width=3,layers=glayers_edge_pure)    
    multi_dot_line(kicad_mod,[(43,2.2),(57.8,2.2),],width=4.4,layers=glayers_edge_pure)        
    
    multi_dot_line(kicad_mod,[(0,21),(100,21),],width=1.6,layers=glayers_edge_pure,segments=10)    
    
    ##############
    a=90
    y=100-dy
    ntc_2020(kicad_mod,dx,y         ,dh=3.25,angle=a,**ka2020)
    ntc_2020(kicad_mod,40-dx,y      ,dh=3.3,angle=a,**ka2020)
    
    ntc_2020(kicad_mod,100-(40-dx),y,dh=3.4,angle=a,**ka2020)
    ntc_2020(kicad_mod,100-dx,y     ,dh=3.5,angle=a,**ka2020,**last_ka)    
        
    multi_dot_line(kicad_mod,[(41.5,100),(41.5,87),],width=3,layers=glayers_edge_pure)    
    multi_dot_line(kicad_mod,[(58.5,100),(58.5,87),],width=3,layers=glayers_edge_pure)    
    multi_dot_line(kicad_mod,[(43,97.8),(57.8,97.8),],width=4.4,layers=glayers_edge_pure)        
    
    multi_dot_line(kicad_mod,[(0,79),(100,79),],width=1.6,layers=glayers_edge_pure,segments=10)    
    
    #####
    crosshair(kicad_mod,50,50,w=100,h=57)
    wm=34.7
    hm=27
    # x,y=wm/2,hm/2
    #14.6-1.6=13
    x=hm/2+13
    x=50
    y=50
    rectline_center(kicad_mod,x-(hm+13)/2,y,w=13,h=44,width=0.1,layers=glayers_silk) 
    rectline_center(kicad_mod,x+(hm+13)/2,y,w=13,h=44,width=0.1,layers=glayers_silk) 
    mgn12c_block(kicad_mod,x,y,angle=90)
    
    bw=wm/2+1
    for i in range(1,10):
        non_plated_hole(kicad_mod,i*10,y+bw,1)#2.45
        non_plated_hole(kicad_mod,i*10,y-bw,1)
    
    hdz=10
    
    x=50+hm/2+hdz
    multi_dot_line(kicad_mod,[(x,21),(x,79)],width=0.01,layers=glayers_silk,)    
    mgn12c_block(kicad_mod,x+hm/2,y,angle=90)
    
    x=50-hm/2-hdz
    multi_dot_line(kicad_mod,[(x,21),(x,79)],width=0.01,layers=glayers_silk,)    
    mgn12c_block(kicad_mod,x-hm/2,y,angle=90)
    
    return write_kicad_mod(kicad_mod,zip=z)


def g3030_j45(W=100,k16=1.6,m4=3.9,m5=4.9,m6=5.9,z=0):
    kicad_mod = new_kicad_mod(w=W,h=W)
    
    multi_dot_line(kicad_mod,[(0,0),(99,99)],width=0.01,layers=glayers_silk,segments=6,segments_d=1)    
        
    return write_kicad_mod(kicad_mod,zip=z)


def a2020_j45(W=100,k16=1.6,m4=3.9,m5=4.9,m6=5.9,z=0):
    kicad_mod = new_kicad_mod(w=W,h=W)
    x=y=W/2
    
    multi_dot_line(kicad_mod,[(0,0),(100,100)],width=0.01,layers=glayers_silk)    
    multi_dot_line(kicad_mod,[(100,0),(0,100)],width=0.01,layers=glayers_silk)    
    
    lmh=42.36
    non_plated_hole(kicad_mod,lmh,W-lmh,m5)
    non_plated_hole(kicad_mod,W-lmh,lmh,m5)
    
    a=100    
    xr=48.2841+(10*2**0.5)+((k16/2)*2**0.5)
    sx=25.274
    lx=87.3951
    krh=dict(w_holes={10:m5,sx:m5,50:m5,W-sx:m5,90:m5},w_holes_d=4.9,w=a,h=20,layers=glayers_silk,width=0.01,angle=0,)
    kr=dict(w_holes=[22.5,lx],w_holes_d=m5,crosshair=1,h=20,layers=glayers_silk,width=0.01,w=a,)
    rectline_center(kicad_mod,a/2,10,**krh)
    rectline_center(kicad_mod,xr,48.2841,angle=45,**kr)
    # rectline_center(kicad_mod,48.2841-5.85,48.2841,w=100,h=20,layers=glayers_Cmts,angle=45,crosshair=1)
    
    rectline_center(kicad_mod,a/2,W-10,**krh)
    rectline_center(kicad_mod,W-(xr),W-48.2841,angle=180+45,**kr)
        
    
    d=2.5
    q=20*2**0.5
    multi_dot_line(kicad_mod,[(d,20),(20,20),(W-20,W-20),(W-d,W-20)],width=1.6,layers=glayers_edge_pure,segments=17.6,segments_d=0.1)    
        
    for yi in krh['w_holes']:
        # for n,(x,y) in enumerate(edge_distance_turn(W,W,[d,d])): #
        if yi==W-sx:
            continue
        npd=m5
        non_plated_hole(kicad_mod,10,yi,npd)
        non_plated_hole(kicad_mod,W-10,W-yi,npd)
        
    multi_dot_line(kicad_mod,[(10,0),(10,100)],width=0.01,layers=glayers_silk)        
    multi_dot_line(kicad_mod,[(20,0),(20,100)],width=0.01,layers=glayers_silk)        
        
    return write_kicad_mod(kicad_mod,zip=z)

def ntc_2020(kicad_mod,x,y,angle=0,hole=4.9,dh=0,w2=2.2,h6=4.3+0.3,layers=py.No('glayers_Cmts'),hole2=None,dh2=None):
    '''  ￥0.7 两个'''
    if not layers:layers=glayers_Cmts
    
    e=glayers_edge_pure
    circle(kicad_mod,*rotate_point(x+10,y,angle,x,y),2,layers=layers)
    
    rectline_center(kicad_mod,*rotate_point(x+(10-2.55),y,angle,x,y), w=w2, h=h6, width=0.01, layers=e,angle=angle)  #
    non_plated_hole(kicad_mod,*rotate_point(x+dh,y,angle,x,y), hole)
    rectline_center(kicad_mod,*rotate_point(x-(17.55-10),y,angle,x,y), w=w2, h=h6, width=0.01, layers=e,angle=angle)  #

    rectline_center(kicad_mod,x,y,w=20.2,h=17,layers=layers,angle=angle)
    
    # if angle%180==90:
    rounded_rectangle(kicad_mod,x,y, w=8.6, h=6, width=0.01, layers=layers,angle=angle)
    if hole2:
        if not dh2:dh2=0
        non_plated_hole(kicad_mod,*rotate_point(x+dh2,y,angle,x,y), hole2)
    
    
    
def tc_2028(kicad_mod,x,y,angle=0,hole=4.9,w2=2.2):
    ''' 天成五金 2028 连接件  angle 负逆时针。正顺'''
    #1.9
    h6 = 5.9
    # da = 13.2
    # db = 34.5
    # m5 = 4.9  # 孔直径
    
    e=glayers_edge_pure
    # e=glayers_silk+glayers_edge_pure
    # e=
    
    #11.8  ,9.5
    circle(kicad_mod,*rotate_point(x+14,y,angle,x,y),2,layers=glayers_Cmts)
    
    rectline_center(kicad_mod,*rotate_point(x+(14-3.37),y,angle,x,y), w=w2, h=h6, width=0.01, layers=e,angle=angle)  # 2028
    non_plated_hole(kicad_mod,*rotate_point(x-2,y,angle,x,y), hole)
    non_plated_hole(kicad_mod,*rotate_point(x+2,y,angle,x,y), 1)
    rectline_center(kicad_mod,*rotate_point(x-(24.77-14),y,angle,x,y), w=w2, h=h6, width=0.01, layers=e,angle=angle)  # 2028

    rectline_center(kicad_mod,x,y,w=28,h=20,layers=glayers_Cmts,angle=angle)
    # rectline_center(kicad_mod,x,y,w=28-4.4,h=10,layers=glayers_Cmts,angle=angle)

def aluminum_profile_2020_wheel(mw=59,m5=4.9,m6=5.9,z=0):#36+12.9*2
    ''' 普通欧标2020 1.8 ，不是推荐的V型槽

白色（5*21.5*7mm）
黑色（5*21.5*7mm）    
625zz 5*16*5
    '''
    kicad_mod = new_kicad_mod(w=100,h=mw)
    x=50
    y=mw/2
    non_plated_hole(kicad_mod,x,y,2.9)
    rectline_center(kicad_mod,x,y,20,20,layers=glayers_silk)
    
    
    tc_2028(kicad_mod,x-10-14,y,angle=0,  hole=1.2,w2=2)
    tc_2028(kicad_mod,x+10+14,y,angle=180,hole=1.2,w2=2)
    # tc_2028(kicad_mod,x,y+10+14,angle=-90)
    
    ya=-20.2#-32.3#-mw/2#
    rectline_center(kicad_mod,x,y+ya,w=19.9,h=19.9,width=0.01,layers=glayers_edge_pure) # 2020
    multi_dot_line(kicad_mod,[(10,y+ya),(90,y+ya)],width=0.5,layers=glayers_Cmts)
    
    
    tc_2028(kicad_mod,x,y+ya-10-14,angle=90)
    tc_2028(kicad_mod,x,y+ya+10+14,angle=-90,hole=m5)
    
    ntc_2020(kicad_mod,x-10-10,y+ya,angle=0,hole=m5)
    ntc_2020(kicad_mod,x+10+10,y+ya,angle=180,hole=m5)
    
    xi=38.8
    bd=36.7/2
    circle(kicad_mod,x-xi,y+bd,r=11)
    non_plated_hole(kicad_mod,x-xi,y+bd,m5)#左 下
    non_plated_hole(kicad_mod,x-xi,y-bd,m5)
    
    non_plated_hole(kicad_mod,x+xi,y+bd,m5)
    non_plated_hole(kicad_mod,x+xi,y-bd,m5)
    
    # 侧轮
    ntc_2020(kicad_mod,x-xi,y-bd,angle=90,layers=glayers_silk,)
    rectline_center(kicad_mod,x-xi,y,w=16,h=7.5,width=0.01,layers=glayers_edge_pure) # wheel
    ntc_2020(kicad_mod,x-xi,y+bd,angle=-90,layers=glayers_silk,)
    
    ntc_2020(kicad_mod,x+xi,y-bd,angle=90)
    rectline_center(kicad_mod,x+xi,y,w=16,h=7.5,width=0.01,layers=glayers_edge_pure) # wheel
    ntc_2020(kicad_mod,x+xi,y+bd,angle=-90)
    
    step_motor_42(kicad_mod,x,y+ya-10-21,d=1)
    step_motor_57(kicad_mod,x,y+ya-10-56.6/2,d=1)
    
    
    return write_kicad_mod(kicad_mod,zip=z)

def brushless_wheel(W=240,k16=1.2,z=0):
    kicad_mod = new_kicad_mod(w=W,h=W)
    x=y=W/2
    non_plated_hole(kicad_mod,x,y,16.7)
    non_plated_hole_circle(kicad_mod,x,y,r=113/2,d=3.8,n=6,angle=0)
    non_plated_hole_circle(kicad_mod,x,y,r=113/2,d=1,n=6,angle=30)
    circle(kicad_mod,x,y,130)
    circle(kicad_mod,x,y,160)
    circle(kicad_mod,x,y,W,crosshair=1,layers=glayers_Cmts)
    rd=W/2+0.6
    ac=23 # 四边连
    for i in range(4):
        radian = math.radians(i * 90+ac/2)   # 将角度转换为弧度
        xi=x+ rd * math.cos(radian)
        yi=y+ rd * math.sin(radian)
        arc(kicad_mod,center=[x,y], start=[xi,yi],angle=90-ac, layers=glayers_edge_pure,width=k16)
        
    for i in range(10):                
        non_plated_hole_circle(kicad_mod,x,y,r=W/2-i*4-4,d=4.9,n=1,angle=28+i*36)
        
    #### 42
    
    
    
    d2028=20.4
    d=30
    w=60
    # rka=dict()
    whs=[20+10,50]
    
    for n,(x,y) in enumerate(edge_distance_turn(W,W,[d,10])): #
        rectline_center(kicad_mod,x,y,w,20,angle=n*90+180,w_holes=whs)
        
    for n,(x,y) in enumerate(edge_distance_turn(W,W,[10,d])): # 
        rectline_center(kicad_mod,x,y,w,20,angle=n*90-90,w_holes=whs)
        
    for n,(x,y) in enumerate(edge_distance_turn(W,W,[10,10])): # 
        non_plated_hole(kicad_mod,x,y,d=4.9)
        
    return write_kicad_mod(kicad_mod,zip=z)

def vacuum(z=0):
    '''吸尘器 空气滤芯 口径 57.2  
六味地黄丸 蜜丸瓶子 外径 58    
    '''
    kicad_mod = new_kicad_mod(w=100,h=100)
    x=y=50
    non_plated_hole(kicad_mod,x,y,57.2)
    return write_kicad_mod(kicad_mod,zip=z)
    
def xn_j_48v(wm=100,hm=22,drill_screw=0.95,z=0):
    x,y=wm/2,hm/2
    kicad_mod = new_kicad_mod(w=wm,h=hm,text_at=[x,y])
    
    rectline_center(kicad_mod,x,y,w=174,h=hm,width=0.01,layers=glayers_silk) #usb typec
    
    d=37.5
    non_plated_hole(kicad_mod,x-d,y,3)
    non_plated_hole(kicad_mod,x+d,y,3)
    non_plated_hole(kicad_mod,x,y,10)
    
    
    return write_kicad_mod(kicad_mod,zip=z)    
def esp32c3_mini(wm=18,hm=23,drill_screw=0.95,z=0):
    ''' 上typec 下天线 进入下载模式：按住ESP32C3的BOOT按键，然后按下RESET按键，松开RESET按键，再松开BOOT按键，此时ESP32C3会进入下载模式。（每次连接都需要重新进入下载模式，有时按一遍，端口不稳定会断开，可以通过端口识别声音来判断）
新模块插入typec一直有端口识别声，无法使用，烧录micropython后串口可以直接使用。    
# stm32(    
    '''
    x,y=wm/2,hm/2
    kicad_mod = new_kicad_mod(w=wm,h=hm,text_at=[x,y])
    s2=[
['5V',' GND','3V3','4SCK','3','2','1','0',],
['5MIS' ,'6MOS'  ,'7SS' ,'8SDA','9SCL','10','20RX','21TX'],
]    
    
    
    for i in range(len(s2[0])):# 20
        for xi,si in {1:0,-1:1}.items():
            x,y=wm/2+7.54*xi,2+2.54*i
            text(kicad_mod,s2[si][i],at=[x+3*xi,y],)
            # plated_hole(kicad_mod,x,y,drill_screw,size=psize,number=s2[si][i])
            size=[drill_screw,drill_screw]
            kicad_mod.append(Pad(number=s2[si][i],type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
                at=[x,y], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
            kicad_mod.append(Pad(number=s2[si][i],type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x,y], size=[2,0.8], drill=drill_screw, layers=Pad.LAYERS_THT))
        # plated_hole(kicad_mod,wm/2-7.5,hm/2-25.4+1.27+2.54*i,drill_screw,size=psize,number=s2[1][i])
        
    # x,y=wm/2,hm/2    
    rectline_center(kicad_mod,wm/2,3,w=9,h=7.4,width=0.01,layers=glayers_silk) #usb typec
    
    rectline_center(kicad_mod,wm/2,-7,w=10,h=8,width=0.01,layers=glayers_edge_pure) #usb typec 插线避空
    
    return write_kicad_mod(kicad_mod,zip=z)    
    

def xl7015(wm=16.1,hm=44,z=0):
    ''' 80v > 5v '''
    kicad_mod = new_kicad_mod(w=wm,h=hm)
    x,y=wm/2,hm/2
    hole_square(kicad_mod,x,y,w=12.5,h=40,d=1.9,angle=0,holes=[0,1,2,3],func=plated_hole)
    return write_kicad_mod(kicad_mod,zip=z)    
    
def XH_A232(wm=53.2,hm=45.4,z=0):
    ''' 30w x2 '''
    kicad_mod = new_kicad_mod(w=wm,h=hm)
    x,y=wm/2,hm/2
    hole_square(kicad_mod,x,y,w=46,h=38,d=3,angle=0,holes=[0,1,2,3],func=non_plated_hole)
    
    non_plated_hole(kicad_mod,17.3,24.4,3.5)
    non_plated_hole(kicad_mod,35.9,24.4,3.5)
    
    wr=4.4
    rectline_center(kicad_mod,13,2,w=wr,h=4,width=0.01,layers=glayers_silk+glayers_edge_pure)
    rectline_center(kicad_mod,20,2,w=wr,h=4,width=0.01,layers=glayers_silk+glayers_edge_pure)
    rectline_center(kicad_mod,33,2,w=wr,h=4,width=0.01,layers=glayers_silk+glayers_edge_pure)
    rectline_center(kicad_mod,40.2,2,w=wr,h=4,width=0.01,layers=glayers_silk+glayers_edge_pure)
    
    rectline_center(kicad_mod,13,hm-2,w=wr,h=4,width=0.01,layers=glayers_silk+glayers_edge_pure)
    rectline_center(kicad_mod,20,hm-2,w=wr,h=4,width=0.01,layers=glayers_silk+glayers_edge_pure)
    
    rectline_center(kicad_mod,36,hm-1.9,w=7.1,h=3.8,width=0.01,layers=glayers_silk+glayers_edge_pure)
    
    return write_kicad_mod(kicad_mod,zip=z)    
    
    d=2
    non_plated_hole(kicad_mod,13  ,2,d,number='L+')
    non_plated_hole(kicad_mod,20  ,2,d,number='L-') 
    non_plated_hole(kicad_mod,33  ,2,d,number='R+')
    non_plated_hole(kicad_mod,40.2,2,d,number='R-') 
    
    for i in range(7):
        non_plated_hole(kicad_mod,13  ,hm-i*0.5,d,number='VCC')
        non_plated_hole(kicad_mod,20,hm-i*0.5,d,number='GND')
        
        non_plated_hole(kicad_mod,33.5,hm-i*0.5,d,number='L')
        non_plated_hole(kicad_mod,36,hm-i*0.5,d,number='G')
        non_plated_hole(kicad_mod,38.6,hm-i*0.5,d,number='R')
    
    
    return write_kicad_mod(kicad_mod,zip=z)    
    
def speaker_48x48(M=48,d=44,z=0):
    '''  '''
    
    kicad_mod = new_kicad_mod(w=M,h=M)
    x=y=M/2
    
    # draw_octagon(kicad_mod,x,y,M,angle=45/2,layers=glayers_edge_pure)
    hole_square(kicad_mod,x,y,39,d=3,angle=0,holes=[0,1,2,3],func=non_plated_hole)
    circle(kicad_mod,x,y,33.4)
    
    
    circle(kicad_mod,x,y,d)
    radius = d / 2  # 圆的半径
    initial_hole_spacing = 5  # 初始孔的间距（假设孔的初始间距为 5）
    num_rings = int(d/6)  # 圆环的数量

    for ring in range(1, num_rings + 1):  # 计算每个孔的坐标
        current_radius = radius * (ring / num_rings)  # 当前圆环的半径
        circumference = 2 * math.pi * current_radius  # 计算当前圆环的周长
        hole_spacing = initial_hole_spacing * (1 + (ring - 1) * 0.1)  # 计算当前圆环上的孔间距
        n = int(circumference / hole_spacing)  # 计算当前圆环上的孔数量
        for i in range(n):  # 计算角度
            angle = 2 * math.pi * i / n
            xi = x + current_radius * math.cos(angle)  # 计算孔的坐标
            yi = y + current_radius * math.sin(angle)  # 计算孔的坐标
            non_plated_hole(kicad_mod, xi, yi, 1)  # 调用 non_plated_hole 函数
    
    
    return write_kicad_mod(kicad_mod,zip=z)    
    
def mgn12c_rail(kicad_mod,x,y,angle=0,h=150,hole=2.95,mid_hole=None,write_kicad=False,z=0):    
    '''  '''
    if not kicad_mod:
        kicad_mod = new_kicad_mod(w=wm,h=hm)
        write_kicad=False
    # rectangle_outline(kicad_mod,x,y,w=12,h=100-hm,width=0.12,layers=glayers_silk) # 
    rectline_center(kicad_mod,x,y,w=12,h=h,width=0.012,angle=angle,layers=glayers_silk) # 
    n=h//25
    if n%2==1:n+=1
    for i in range(n//2):
        if i==0 and mid_hole:
            non_plated_hole(kicad_mod,*rotate_point(x,y+i*25,angle,x,y),mid_hole)
            continue
    
        non_plated_hole(kicad_mod,*rotate_point(x,y+i*25,angle,x,y),hole)
        non_plated_hole(kicad_mod,*rotate_point(x,y-i*25,angle,x,y),hole)
    
    circle(kicad_mod,x,y,diameter=[0.1,1,2,12],crosshair=1,layers=glayers_Cmts)
    # hole_square(kicad_mod,x,y,w=15,h=20,d=2.95,angle=angle,holes=[0,1,2,3],func=non_plated_hole)
    
    
    if write_kicad:
        return write_kicad_mod(kicad_mod,zip=z)        
        
def mgn12c_block(kicad_mod,x,y,angle=0,wm=34.7,hm=27,write_kicad=False,up_rail=False,z=0):    
    ''' ,wm=12,hm=200'''
    if not kicad_mod:
        kicad_mod = new_kicad_mod(w=wm,h=hm)
        write_kicad=False
    circle(kicad_mod,x,y,1,layer=glayers_Cmts)
    hole_square(kicad_mod,x,y,w=15,h=20,d=2.95,angle=angle,holes=[0,1,2,3],func=non_plated_hole)
    rectline_center(kicad_mod,x,y,w=wm,h=hm,width=0.012,angle=angle,layers=glayers_silk) # 
    multi_dot_line(kicad_mod, [(x-50,y), (x+50,y)],layers=glayers_Cmts)  # 导轨线
    
    if py.isnum(up_rail):
        rotate_point
        if py.isfloat(up_rail):#22
            # rectline_center(kicad_mod,x,y,w=32.5,h=hm,width=0.01,angle=angle,layers=glayers_FB_Cu) # 
            # rectline_center(kicad_mod,x,y,w=32.5,h=hm-3,width=0.01,angle=angle,layers=glayers_Cmts) # 
            if angle==180:
                rectline_center(kicad_mod,x+up_rail,y,w=7.9,h=11.9,width=0.01,angle=angle,layers=glayers_edge_pure) # 
                non_plated_hole(kicad_mod,x+up_rail-4-5,y,2.9)
            else:    # -11+4  = -7
                rectline_center(kicad_mod,x-up_rail,y,w=7.9,h=11.9,width=0.01,angle=angle,layers=glayers_edge_pure) # 
                # non_plated_hole(kicad_mod,x-up_rail,y,1) # 向内
                non_plated_hole(kicad_mod,x-up_rail+4+5,y,2.9) # 向内
            
            
        # 这个不正确，有空慢慢推理 rectline_center(kicad_mod,*rotate_point(x,y,angle,x-11+4,y),w=8,h=11.9,width=0.01,angle=angle,layers=glayers_edge_pure) 
    if write_kicad:
        return write_kicad_mod(kicad_mod,zip=z)    
    
    
    
    
    
def mgn12c_rail_triangle(kicad_mod=None, x0=0, y0=0,dh=12.5, wm=34.7, hm=27, z=0):
    ''' MGN12C导轨安装三角形支架 '''
    write_kicad = not kicad_mod
    if not kicad_mod: kicad_mod = new_kicad_mod(w=wm, h=hm)
    cx, cy = x0 + wm/2, y0 + hm/2  # 中心点坐标(x,y)
    
    # 中心方孔安装孔
    hole_square(kicad_mod, cx, cy, w=15, h=20, d=2.95, angle=0, holes=[0,1,2,3], func=non_plated_hole)
    
    # 水平线（向右延伸）
    multi_dot_line(kicad_mod, [(x0-50, cy), (x0+50, cy)])  # 向左延伸50mm，向右延伸50mm
    
    # 矩形轮廓（向下延伸）
    rectangle_outline(kicad_mod, cx-6, y0+hm, w=12, h=100-hm, width=0.1, layers=glayers_Cmts)
    
    # 导轨安装孔（向下分布）
    yr = hm + dh  # dh 孔距滑块下边缘     25mm（25/2=12.5）
    for i in [-2,-1]: circle(kicad_mod, cx, y0+yr+i*25, 3)  # 向下每隔25mm一个孔
    for i in [0,1,2,3]: non_plated_hole(kicad_mod, cx, y0+yr+i*25, 3.2)  # 向下每隔25mm一个孔
    
    # 闭合外框轮廓（顺时针方向）
    multi_dot_line(kicad_mod, [
        (x0, y0),            # 左上角起点 (0,0)
        (x0, y0+hm),         # 向下移动到左下角 (0,hm)
        (cx-6, y0+hm),         # 滑块边缘导轨 
        (cx-6, y0+100),      # 向右下移动到三角形左顶点 (cx-6,100)
        (cx+6, y0+100),      # 向右移动到三角形右顶点 (cx+6,100)
        (cx+6, y0+hm),        # 滑块边缘导轨 
        (x0+wm, y0+hm),      # 向右下移动到右下角 (wm,hm)
        (x0+wm, y0),         # 向上移动到右上角 (wm,0)
        (x0, y0)             # 向左移动回起点 (0,0) - 闭合
    ], width=0.01,layers=glayers_edge_pure,segments=100)
    
    # 保存模块
    return write_kicad_mod(kicad_mod, zip=z) if write_kicad else kicad_mod    
    
    
    
    
def boost3470(wm=36,hm=70,z=0):
    ''' 适配 250w铝基板升压模块'''
    kicad_mod = new_kicad_mod(w=wm,h=hm)
    for i in range(30):
        if i in [12,25]:continue
        non_plated_hole(kicad_mod,0-0.4,i*0.9,0.8)
    
    x,y=wm/2,hm/2
    
    plated_hole(kicad_mod,x+10,-0,2.5) # out+
    plated_hole(kicad_mod,x-10,-0,2.5) # out-
    # plated_hole(kicad_mod,x+10,-1.5,2.5) # out+
    # plated_hole(kicad_mod,x-10,-1.5,2.5) # out-
    
    non_plated_hole(kicad_mod,x-15,4,3.1)
    non_plated_hole(kicad_mod,x+15,4,3.1)
    
    
    # 21.2 -20.4= 0.8 
    drx=10.2/2 +0.4
    non_plated_hole(kicad_mod,x-drx,10,10.2)
    non_plated_hole(kicad_mod,x+drx,10,10.2)
    
    
    #20.6,h=4.7
    rectline_center(kicad_mod,22,19,w=21,h=5,width=0.01,layers=glayers_silk+glayers_edge_pure) # V-ADJ OC-ADJ
    # non_plated_hole(kicad_mod,13,17,5.2)
    
    h=21.4+2
    multi_dot_line(kicad_mod,[(0,h),(wm,h)],width=0.01,layers=glayers_silk+glayers_edge_pure)
    
    multi_dot_line(kicad_mod,[(0,28),(wm,28)],width=0.01)
    
    #竖
    multi_dot_line(kicad_mod,[(6,0),(6,hm)],width=0.01)
    
    return write_kicad_mod(kicad_mod,zip=z)    

def SSR(wm=45.5,hm=58.5,drill_screw=4.1,z=0):
    kicad_mod = new_kicad_mod(w=wm,h=hm) #name=f'SSR-{wm},{hm}',
    x,y=wm/2,hm/2
    non_plated_hole(kicad_mod,x,4.5,drill_screw)
    non_plated_hole(kicad_mod,x-0.5,8,drill_screw)
    # for i in range(7):
        # non_plated_hole(kicad_mod,x,i,drill_screw)
    
    non_plated_hole(kicad_mod,x,52.2,drill_screw)
    non_plated_hole(kicad_mod,x-0.5,54.5,drill_screw)
    
    rectangle_outline(kicad_mod,wm,0,w=-wm,h=-hm-2,width=0.1,layers=glayers_Cmts) # 
    
    return write_kicad_mod(kicad_mod,zip=z)    
    

def trapezoid_socket(drill_screw=2.5,z=0,wm=57,hm=93.5):
    ''' 1+2+2 插线板 '''
    kicad_mod = new_kicad_mod(w=wm,h=hm)
    x,y=wm/2,hm/2
    ss=51.5
    trapezoid(kicad_mod,x,y,ss,wm,hm)
    x0=x-ss/2
    y0=y-hm/2
    non_plated_hole(kicad_mod,x0+11.5   ,y0+8.9,drill_screw)
    non_plated_hole(kicad_mod,x0+ss-11.5,y0+8.9,drill_screw)
    
    non_plated_hole(kicad_mod,x-wm/2+0.6+5.8, y0+73,drill_screw)
    non_plated_hole(kicad_mod,x+wm/2-0.6-5.8, y0+73,drill_screw)
    
    non_plated_hole(kicad_mod,x,y0+8.7,3.9) # 居中挂钩
    non_plated_hole(kicad_mod,x,y0+14.7,7.85) # 居中挂钩
    
    yzw=hm+3.5
    # for i in range(3):
        # i-=1
        # d=4
        # non_plated_hole(kicad_mod,x+i*d,yzw,d) # 居中尾挂孔
    non_plated_hole(kicad_mod,x,yzw,4) # 居中尾挂孔    
    #####################
    non_plated_hole(kicad_mod,x0+11.5+0.3,3.3,4) # 上左挂孔
    drill_screw=2.9
    
    bx=31/2
    non_plated_hole(kicad_mod,x-bx, yzw-18,drill_screw)
    non_plated_hole(kicad_mod,x+bx, yzw-18,drill_screw)
    
    bx=35.5/2
    non_plated_hole(kicad_mod,x-bx, yzw-18-61.3,drill_screw)
    non_plated_hole(kicad_mod,x+bx, yzw-18-61.3,drill_screw)
    
    
    return write_kicad_mod(kicad_mod,zip=z)    
    

def stm32f103_board_typec(drill_screw=0.95,djz=0,psize=1.2,pad_size=[1.5,0.8],z=0):
    ''' usb micro 口 在左，丝印从左至右'''
    wm,hm=23,53.3
    kicad_mod = new_kicad_mod(w=wm,h=hm,d=drill_screw,p=pad_size,text_at=[11,-9])
    s2=[
['GND','GND','3N','RST','B11','B10','B1','B0','A7','A6','A5','A4','A3','A2','A1','A0','C15','C14','C13','3B'],
['B12','B13','B14','B15','A8','A9','A10','A11','A12','A15','B3','B4','B5','B6','B7','B8','B9','5V','GND','3V'],
]    
    
    
    for i in range(len(s2[0])):# 20
        for xi,si in {1:0,-1:1}.items():
            x=wm/2+xi*7.6
            y=hm/2-25.4+1.27+2.54*i-0.1
            y=hm/2-24.23+2.54*i
            y=2.5+2.54*i
            text(kicad_mod,s2[si][i],x+2.1*xi,y+0.2,)
            # plated_hole(kicad_mod,x,y,drill_screw,size=psize,number=s2[si][i])
            size=[drill_screw,drill_screw]
            kicad_mod.append(Pad(number=s2[si][i],type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
                at=[x,y], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
            kicad_mod.append(Pad(number=s2[si][i],type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x-(xi*pad_size[0]*0.2),y],size=pad_size, drill=0, layers=Pad.LAYERS_THT))
        # plated_hole(kicad_mod,wm/2-7.5,hm/2-25.4+1.27+2.54*i,drill_screw,size=psize,number=s2[1][i])
        
    rectline_center(kicad_mod,wm/2,4.3,w=9,h=8.6,width=0.01,layers=glayers_silk+glayers_edge_pure) #usb c         

    # rectline_center(kicad_mod,wm/2,10+2.4,w=11.4,h=6,width=0.01,layers=glayers_silk+glayers_edge_pure) # 复位按键
    # rectline_center(kicad_mod,8,10+2.54,w=3.9,h=6,width=0.01,layers=glayers_silk+glayers_edge_pure) # 复位按键
    # for x,y in U.range2d(2,3):
        # x=wm-8-2.54+x*2.54
        # y=10+y*2.54
        # plated_hole(kicad_mod,x,y,1.2,size=psize,number=f'yellow{x},{y}')
    rectline_center(kicad_mod,wm/2,14,w=11,h=8,width=0.01,layers=glayers_silk+glayers_edge_pure,crosshair=1) # 全包框
    
    rectline_center(kicad_mod,wm/2,26.5,w=8.5,h=8.5,width=0.01,layers=glayers_edge_pure,angle=45) # stm32
        
    rounded_rectangle(kicad_mod, wm / 2,35.6, w=10.2+djz, h=4+djz, radius=2, width=0.01, layers=glayers_edge_pure) # 晶振
    rectline_center(kicad_mod, wm / 2,41, w=8.3, h=3.4, width=0.01, layers=glayers_silk + glayers_edge_pure) # 整流桥
    
    for i in range(8): # LED
        xe=(i-1)*0.2
        dw=7.8
        dxled=-0.2
        y=45
        non_plated_hole(kicad_mod,dw+xe+dxled,y,1.4) # 2025年11月15日
        non_plated_hole(kicad_mod,wm-dw-xe+dxled,y,1.4)
    
    rectline_center(kicad_mod, wm / 2,48.5, w=10.2, h=4, width=0.01, layers=glayers_silk + glayers_edge_pure) # 尾4p
    
    for yi in range(18):
        for i in range(4):# 4p
            plated_hole(kicad_mod,wm/2-3.8+2.54*i,50.5+yi*0.3,0.9,size=1.1,number=f'4p{i}')
    
        
    rectline_center(kicad_mod,wm/2,hm/2,w=wm,h=hm,width=0.1,layers=glayers_silk) # 
    
    multi_dot_line(kicad_mod,[(0,0),(wm,hm)],width=0.01)
    multi_dot_line(kicad_mod,[(wm,0),(0,hm)],width=0.01)
    multi_dot_line(kicad_mod,[(0,hm/2),(wm,hm/2)],width=0.01)
    multi_dot_line(kicad_mod,[(wm/2,0),(wm/2,hm)],width=0.01)
    
    multi_dot_line(kicad_mod,[(0,hm/2+1.27),(wm,hm/2+1.27)],width=0.01)
    multi_dot_line(kicad_mod,[(0,hm/2-1.27),(wm,hm/2-1.27)],width=0.01)
    
    return write_kicad_mod(kicad_mod,zip=z)    
        

def stm32f103_board_extend(d=[3,3.5],xd=3,dxi=7.48, z=0):  # d改为列表形式，默认两级扩展[3.5, 5.0]
    if py.isnum(d):d=[d]
    assert d
    if py.isnum(xd):
        xd_temp=[]
        for i,di in enumerate(d):
            xd_temp.append(xd+i*0.1)
        xd=xd_temp    
    wm, hm = 22.7, 53.3
    kicad_mod = new_kicad_mod(text_at=[11,-9], w=wm, h=hm,d=d)
    s2 = [
        ['GND','GND','3N','RST','B11','B10','B1','B0','A7','A6','A5','A4','A3','A2','A1','A0','C15','C14','C13','3B'],
        ['B12','B13','B14','B15','A8','A9','A10','A11','A12','A15','B3','B4','B5','B6','B7','B8','B9','5V','GND','3V'],
    ]
    
    # 计算引脚阵列中心Y坐标
    center_y = hm/2 - 25.4 + 1.27 + 2.54 * 9.5  # 20个引脚，中间在第9.5个位置
    
    for i in range(len(s2[0])):  # 20个引脚
        for xi, si in {1: 0, -1: 1}.items():  # 左右两侧
            # 原始引脚位置 (2.54mm间距)
            x_orig = wm/2 + xi * dxi
            y_orig = hm/2 - 25.4 + 1.27 + 2.54 * i - 0.1
            
            # 当前级坐标（初始为原始引脚位置）
            prev_x = x_orig
            prev_y = y_orig
            
            # 创建原始引脚
            sn = s2[si][i]
            ka = dict(number=sn, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_THT)
            kicad_mod.append(Pad(at=[prev_x, prev_y], size=[0.4,0.4], drill=0.4, **ka))
            
            # 处理多级扩展
            for level, spacing in enumerate(d):
                # 计算当前级扩展引脚位置
                # 水平偏移：每级增加3mm
                x_ext = x_orig + xi * (4.0 + xd[level] * level)  
                
                # 垂直位置：相对于中心对称扩展
                # 计算当前引脚相对于中心的偏移量
                offset_from_center = (i - 9.5) * spacing
                y_ext = center_y + offset_from_center
                
                # 创建扩展引脚（尺寸和钻孔随级别增加）
                drill_size = 1.0 + 0.1 * level
                
                drill_size=min(1.4,drill_size)
                pad_size = min( 1.2+0.4* level,1.8)
                kicad_mod.append(Pad(at=[x_ext, y_ext], drill=drill_size, size=[pad_size, pad_size], **ka))
                
                # 绘制走线连接前一级到当前级
                multi_dot_line(
                    kicad_mod, 
                    [(prev_x, prev_y), (x_ext, y_ext)], 
                    layers=glayers_F_Cu, 
                    width=0.3 + 0.1 * level  # 线宽随级别增加
                )
                
                # 更新前一级坐标为当前级
                prev_x = x_ext
                prev_y = y_ext
                
                # 在最后一级添加文本标注
                if level == len(d) - 1:
                    text(kicad_mod, sn, x_ext-xi*1, y_ext - 1.4)
                # elif level==0:    
                    # text(kicad_mod, sn[-1], x_ext+0.3, y_ext -(0.2*level))
                else:    
                    text(kicad_mod, sn[-1], x_ext+xi*1, y_ext)
    
    return write_kicad_mod(kicad_mod, zip=z)    
    
    
def stm32f103_board(drill_screw=0.95,djz=0,psize=1.2,pad_size=[1.5,0.8],z=0):
    ''' usb micro 口 在左，丝印从左至右'''
    wm,hm=22.7,53.3
    kicad_mod = new_kicad_mod(w=wm,h=hm,d=drill_screw,p=pad_size)
    s2=[
['GND','GND','3N','RST','B11','B10','B1','B0','A7','A6','A5','A4','A3','A2','A1','A0','C15','C14','C13','3B'],
['B12','B13','B14','B15','A8','A9','A10','A11','A12','A15','B3','B4','B5','B6','B7','B8','B9','5V','GND','3V'],
]    
    
    
    for i in range(len(s2[0])):# 20
        for xi,si in {1:0,-1:1}.items():
            x=wm/2+xi*7.48
            y=hm/2-25.4+1.27+2.54*i-0.1
            text(kicad_mod,s2[si][i],x+2.3*xi,y+0.2,)
            # plated_hole(kicad_mod,x,y,drill_screw,size=psize,number=s2[si][i])
            size=[drill_screw,drill_screw]
            kicad_mod.append(Pad(number=s2[si][i],type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
                at=[x,y], size=size, drill=drill_screw, layers=Pad.LAYERS_THT))
            kicad_mod.append(Pad(number=s2[si][i],type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x-(xi*pad_size[0]*0.2),y],size=pad_size, drill=0, layers=Pad.LAYERS_THT))
        # plated_hole(kicad_mod,wm/2-7.5,hm/2-25.4+1.27+2.54*i,drill_screw,size=psize,number=s2[1][i])
        
    rectline_center(kicad_mod,wm/2,3,w=8.5,h=6.3,width=0.01,layers=glayers_silk+glayers_edge_pure) #usb micro         

    rectline_center(kicad_mod,wm/2,10+2.4,w=11.4,h=6,width=0.01,layers=glayers_silk+glayers_edge_pure) # 复位按键
    # rectline_center(kicad_mod,8,10+2.54,w=3.9,h=6,width=0.01,layers=glayers_silk+glayers_edge_pure) # 复位按键
    for x,y in U.range2d(2,3):
        x=wm-8-2.54+x*2.54
        y=10+y*2.54
        # plated_hole(kicad_mod,x,y,1.2,size=psize,number=f'yellow{x},{y}')
    rectline_center(kicad_mod,wm/2,10+2.54,w=11,h=7.7,width=0.01,layers=glayers_silk+glayers_edge_pure) # 全包框
    
    rectline_center(kicad_mod,wm/2,26.8,w=8.1,h=8.1,width=0.01,layers=glayers_edge_pure,angle=45) # stm32
        
    rounded_rectangle(kicad_mod, wm / 2, hm-17.8, w=10.2+djz, h=4+djz, radius=2, width=0.01, layers=glayers_edge_pure) # 晶振
    rectline_center(kicad_mod, wm / 2, hm-17.8+5.2, w=8.3, h=3.3, width=0.01, layers=glayers_silk + glayers_edge_pure) # 整流桥
    rectline_center(kicad_mod, wm / 2, hm-17.8+5.2, w=8.3, h=3.4, width=0.01, layers=glayers_silk + glayers_edge_pure) # 整流桥
    
    for i in range(8): # LED
        xe=(i-1)*0.2
        dw=7.8
        dxled=-0.2
        non_plated_hole(kicad_mod,dw+xe+dxled,hm-8.8,1.4) # 2025年11月15日
        non_plated_hole(kicad_mod,wm-dw-xe+dxled,hm-8.8,1.4)
    
    rectline_center(kicad_mod, wm / 2, hm-4.1, w=10.2, h=4, width=0.01, layers=glayers_silk + glayers_edge_pure) # 尾4p
    
    for i in range(4):# 4p
        non_plated_hole(kicad_mod,wm/2-3.8+2.54*i,hm-2-4,0.9,size=1.1,number=f'4p{i}')
        non_plated_hole(kicad_mod,wm/2-3.8+2.54*i,hm-2-4.2,0.9,size=1.1,number=f'4p{i}')
        non_plated_hole(kicad_mod,wm/2-3.8+2.54*i,hm-2-4.4,0.9,size=1.1,number=f'4p{i}')
    
    for yi in range(21):
        for i in range(4):# 4p
            plated_hole(kicad_mod,wm/2-3.8+2.54*i,hm-2+yi*0.3,0.9,size=1.1,number=f'4p{i}')
    
        
    rectline_center(kicad_mod,wm/2,hm/2,w=wm,h=hm,width=0.1,layers=glayers_silk) # 
    
    multi_dot_line(kicad_mod,[(0,0),(wm,hm)],width=0.01)
    multi_dot_line(kicad_mod,[(wm,0),(0,hm)],width=0.01)
    multi_dot_line(kicad_mod,[(0,hm/2),(wm,hm/2)],width=0.01)
    multi_dot_line(kicad_mod,[(wm/2,0),(wm/2,hm)],width=0.01)
    
    multi_dot_line(kicad_mod,[(0,hm/2+1.27),(wm,hm/2+1.27)],width=0.01)
    multi_dot_line(kicad_mod,[(0,hm/2-1.27),(wm,hm/2-1.27)],width=0.01)
    
    return write_kicad_mod(kicad_mod,zip=z)    
    

def stm32_7segment_display(z=0):
    kicad_mod=new_kicad_mod()
    x,y=24.1,15
    w4=30.25
    h4=14.25
    wm=41.7
    hm=23.5
    rectline_center(kicad_mod,x,y,w=wm,h=hm,width=0.1,layers=glayers_silk) # 
    # hole_rect_center(kicad_mod,x,y,36.5,side_len_y=19.7,d=3,holes=[0,1,2,3])    # w 41.7  , h 23.5
    dw,dh=36.5,19.7
    
    x1=x-dw/2-0.4
    x2=x+dw/2
    non_plated_hole(kicad_mod, x1,y-dh/2, 2.95)
    non_plated_hole(kicad_mod, x2,y-dh/2, 2.95)
    non_plated_hole(kicad_mod, x1,y+dh/2, 2.95)
    non_plated_hole(kicad_mod, x2,y+dh/2, 2.95)
    
    rectline_center(kicad_mod,x+(6.3-(wm-w4)/2),y+0.1,w=w4,h=h4,width=0.1,layers=glayers_edge_pure+glayers_silk) # 
    
    multi_dot_line(kicad_mod,[(0,0),(100,100)],layers=glayers_silk)
    
    return write_kicad_mod(kicad_mod,zip=z)    
    
def as5600(x=50,y=50,w=22.8+0.2,h=23.4+0.2,zip=0,drill_screw=3.5,kicad_mod=None):
    '''磁铁直径 4  '''
    is_write=False
    if not kicad_mod:
        kicad_mod=new_kicad_mod()  # w=w,h=h 会分离成两个  还是默认 100
        is_write=True
        
    rectline_center(kicad_mod,x,y,w,h)
    
    hole_square(kicad_mod,x,y,15.8,drill_screw,angle=0,holes=[0,1,2,3],func=non_plated_hole)#,func=0 force reload
    hole_square(kicad_mod,x,y,15.8,drill_screw,angle=45,holes=[0,1,2,3],func=circle)#,func=0 force reload
    
    if is_write:
        return write_kicad_mod(kicad_mod,zip=zip)    
    
def esp32c3(drill_screw=0.95):
    kicad_mod = new_kicad_mod(w=21,h=52)
    s2=[
['GND', '5V', 'BOOT', 'IO08', 'IO04', 'IO05', '3.3V', 'GND', 'PB_11', 'IO07', 'IO06', 'IO10', 'IO03', 'IO02', '3.3V', 'GND'],
['5V', 'PWB', 'GND', '3.3V', 'RESET', 'NC', 'IO13', 'U0_TX', 'U0_RX', 'GND', 'IO19', 'IO18', 'IO12', 'IO01', 'IO00', 'GND']
]    
 
    for i in range(len(s2[0])): # 16
        plated_hole(kicad_mod,1.5,6.5+2.54*i,drill_screw,number=s2[0][i])
        plated_hole(kicad_mod,1.5+18,6.5+2.54*i,drill_screw,number=s2[1][i])
    
    return write_kicad_mod(kicad_mod,zip=1)    
    

def SOP8(body_width=3.9,zip=0):
    kicad_mod = new_kicad_mod(name=f'sop8_w{body_width}',w=6, h=0)
    pad_width = 0.6
    pad_height = 2
    pitch = 1.27
    # body_width = 3.9
    h = 6

    x0 = pitch
    x0 = 0
    y0 = 0
    for i in range(8):
        x = i % 4 * pitch
        y = (i // 4 - 0.5) * h
        if i % 4 in [0, 3]:
            t = 0.95
        else:
            t = 1
        
        
        # shape=Pad.SHAPE_RECT
        kicad_mod.append(Pad(number=str(i+1), type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x0 + x, y0 + y], size=[pad_width, pad_height * t], layers=Pad.LAYERS_SMT))
        
        mka = py.dict(kicad_mod=kicad_mod, width=0.2, layer=['F.Cu',]) #'B.Cu'
        x2, y2 = x0 + (i % 4 * 2.54)  -2.54+0.2, y0 + y * 2

        multi_dot_line(dots=([x0 + x, y0 + y ], [x2, y2]), **mka)
        kicad_mod.append(Pad(number=str(i+1), type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x2, y2 * 1.08], size=[1, 2], layers=Pad.LAYERS_SMT))
        if i==0:
            kicad_mod.append(Pad(number=str(i+1), type=Pad.TYPE_SMT, shape=Pad.SHAPE_CIRCLE,
                at=[x2, y2 * 1.08], size=[1.5, 1.5], layers=Pad.LAYERS_SMT))
            
        
    x,y=1.5*pitch,0
    circle(kicad_mod,x,y,diameter=[1,12],crosshair=1)


    D = 1
    non_plated_hole(kicad_mod, x-body_width/2 - D, y0, D)
    non_plated_hole(kicad_mod, x+body_width/2 + D, y0, D)

    return write_kicad_mod(kicad_mod,zip=zip)    
    
    
def TSSOP20():
    kicad_mod=new_kicad_mod(w=7,h=0)
    pad_width = 0.5
    pad_height = 1.2
    pitch = 0.65
    body_width = 6.5
    h = 4.4
    h=2.8*2

    x0=pitch
    x0=0
    y0=0
    for i in range(20):
        x = i%10 * pitch
        y = (i//10-0.5)*h
        # pad = Pad(number=i, type="smd", shape="rect", at=(x, y), size=(pad_width, pad_height))
        # kicad_mod.add_pad(pad) 
        if i%10 in [0,9]:
            t=0.95
        else:
            t=1
        
        kicad_mod.append(Pad(number=str(i),type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x0+x,y0+y], size=[0.2,2.8*t], layers=Pad.LAYERS_SMT))
        
        mka=py.dict(kicad_mod=kicad_mod,width=0.2,layer=['F.Cu','B.SilkS'])
        x2,y2=x0+(2.54/pitch)*x-(3.5*2.54-0.4)  ,y0+y*3
        
        multi_dot_line(dots=([x0+x,y0+y*1.5*(t**3)]        ,[x2,y2],),**mka)        
        kicad_mod.append(Pad(number=str(i),type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                at=[x2,y2*1.08], size=[1,2], layers=Pad.LAYERS_SMT))
                
    D=1            
    non_plated_hole(kicad_mod,x0-D-0.7,y0,D)
    non_plated_hole(kicad_mod,x0+6.5+D,y0,D)    
        
    return write_kicad_mod(kicad_mod)
    

def szj25_pillow_block(w100=100,de=2.5,drill_screw=3.9,m6=5.85,z=0):
    '''  '''
    kicad_mod=new_kicad_mod(name='pillow-mid')
    crosshair(kicad_mod,50,50)
    # circle         (kicad_mod,50,50,crosshair=1,diameter=U.tuple_multiply([10,30,41,70],2))    
    
    
    # zd=24.85
    # zd=5.86
    # ayz=39.5 # -5.9
    ayz=27.7 # 24.5+(100-81.8-15)
    x,y=get_szj25_57(kicad_mod,drill_screw=drill_screw,m6=m6,zd=24.88,h=81.8,dls2x=-0.2,ayz=ayz,axz=0,m57=False,f_dz57x=lambda:47/2+w_szj/2+drill_screw/2,f_dz57y=lambda:0)  # dz57y=-0.35 # 两个szj 横竖 边重合
    # step_motor_57(kicad_mod,x,y,drill_screw=drill_screw,)# 右下角开始逆时针 0，1，2，3
    step_motor_57(kicad_mod,x,y,drill_screw=3,)
    hole_square(kicad_mod,x,y,47,3,angle=0,holes=[0,1,2,3],func=circle)#,func=0 force reload
    
    non_plated_hole(kicad_mod,x,y,9.88)
    non_plated_hole(kicad_mod,x-dz57x,y,1)
    
    step_motor_57(kicad_mod,x,y,drill_screw=1,angle=45)

    z=[0 ,0   ], [0 , 4.2], [3.45, 7.4], [3.45, 10.2], [0 , 13.3], [0 , 17.5],
    symmetric_x(kicad_mod,z,xm=19.7,xmid=x,y0=0,angle=0,width=0.01,layers=glayers_silk+glayers_Cmts) #glayers_edge_pure+
    multi_dot_line(kicad_mod,[(x-22,30),(x+22,30)],layers=glayers_silk)
    
    zcz=47
    
    azcz=45
    cz_holes=(1,3)
    if m6<5:cz_holes=(0,1,2,3)
    # hole_rect_center(kicad_mod,x,y,zcz/1.4142,d=m6,angle=azcz,holes=(0,2),) # 45°  右下变正右，逆时针转45
    hole_rect_center(kicad_mod,x,y,zcz/1.4142,d=m6,angle=azcz,holes=cz_holes,) # 
    hole_rect_center(kicad_mod,x,y,zcz/1.4142,d=[0.1,1,3,5.85,6.5],angle=azcz,func=circle,) # 45°  右下变正右，逆时针转45
    hole_rect_center(kicad_mod,x,y,zcz/1.4142,d=[0.1,1,3,5.85,6.5],angle=45,func=circle,) # 45°  右下变正右，逆时针转45

    hole_rect_center(kicad_mod,x,y,64/1.4142,d=1,angle=10,holes=cz_holes,) # 45°  右下变正右，逆时针转45


    xz3=x-dz57y
    yz3=y+dz57x
    non_plated_hole(kicad_mod,x=xz3,y=yz3,d=m6)
    rectline_center(kicad_mod,xz3+dyz_szj,yz3,w=h_szj,h=w_szj)
    crosshair(kicad_mod,xz3+dyz_szj,yz3,w=h_szj,h=w_szj)

    
    circle(kicad_mod,x=xz3+dyz_ls2,y=yz3-8,d=m6)# 
    circle(kicad_mod,x=xz3+dyz_ls2,y=yz3+8,d=m6)
    
    
    return write_kicad_mod(kicad_mod,zip=z)

    a2=180+50.5  # 右下
    polar_coordinate(kicad_mod, xz,yz,a2,45,func=lambda x,y:circle(kicad_mod,x=x,y=y,crosshair=1,diameter=[6,25,]))
    x2,y2=polar_coordinate(kicad_mod, xz,yz,a2,45,func=lambda x,y:non_plated_hole(kicad_mod,x=x,y=y,d=5.85))
    
    a3=180  # 左下
    polar_coordinate(kicad_mod, x2,y2,a3,45,func=lambda x,y:circle(kicad_mod,x=x,y=y,crosshair=1,diameter=[6,25,]))
    x3,y3=polar_coordinate(kicad_mod, x2,y2,a3,45,func=lambda x,y:non_plated_hole(kicad_mod,x=x,y=y,d=5.85))
    
    a31=180+17
    x31,y31=polar_coordinate(kicad_mod, x2,y2,a31,45,func=lambda x,y:non_plated_hole(kicad_mod,x=x,y=y,d=5.85))
    polar_coordinate(kicad_mod, x2,y2,a31,45,func=lambda x,y:circle(kicad_mod,x=x,y=y,crosshair=1,diameter=[6,25,]))  # 正右→ 开始 逆时针
    
    a3_4=90 # 左上
    x3_4,y3_4=polar_coordinate(kicad_mod, x3,y3,a3_4,45,func=lambda x,y:non_plated_hole(kicad_mod,x=x,y=y,d=5.85))
    polar_coordinate(kicad_mod, x3,y3,a3_4,45,func=lambda x,y:circle(kicad_mod,x=x,y=y,crosshair=1,diameter=[6,25,]))  # 正右→ 开始 逆时针
    
    a31_4=90
    # x31_4,y31_4=polar_coordinate(kicad_mod, x31,y31,a31_4,45,func=lambda x,y:non_plated_hole(kicad_mod,x=x,y=y,d=5.85))
    polar_coordinate(kicad_mod, x31,y31,a31_4,45,func=lambda x,y:circle(kicad_mod,x=x,y=y,crosshair=1,diameter=[6,25,]))  # 正右→ 开始 逆时针
    
    a3_4_5=0
    # x3_4_5,y3_4_5=polar_coordinate(kicad_mod, x3_4,y3_4,a3_4_5,45,func=lambda x,y:non_plated_hole(kicad_mod,x=x,y=y,d=1))
    x3_4_5,y3_4_5=polar_coordinate(kicad_mod, x3_4,y3_4,a3_4_5,45,func=lambda x,y:circle(kicad_mod,x=x,y=y,crosshair=1,diameter=[6,25,]))  # 正右→ 开始 逆时针
    
    
    a3_4_5_6=-90  # 检验 2 与6 转一圈后是否重合
    x3_4_5_6,y3_4_5_6=polar_coordinate(kicad_mod, x3_4_5,y3_4_5,a3_4_5_6,45,func=lambda x,y:non_plated_hole(kicad_mod,x=x,y=y,d=5.85))
    polar_coordinate(kicad_mod, x3_4_5,y3_4_5,a3_4_5_6,45,func=lambda x,y:circle(kicad_mod,x=x,y=y,crosshair=1,diameter=[6,25,]))  # 正右→ 开始 逆时针
    
    
    
    
    return write_kicad_mod(kicad_mod,zip=z)
    
def hua4_铜螺母42h(w100=100,de=2.5,drill_screw=3.9,z=1):
    kicad_mod=new_kicad_mod()
    
    x=42/2
    y=100-x
    
    circle(kicad_mod,x,y,diameter=[1,3,4,5,6,6.35,8,10,12,],crosshair=1,layers=glayers_silk) # ,25,28,40
    non_plated_hole(kicad_mod,x,y,4.9)

            
    hole_square(kicad_mod,x,y,31,2.95,angle=0,)
    rectline_center(kicad_mod,x,y,w=42,angle=0,width=0.1,layers=glayers_F_Cu+glayers_silk) # 
    
    multi_dot_line(kicad_mod,[(x,y),(x,101)],layers=glayers_edge_pure,width=4.8)
    
    # t=2.5
    # for i in range(int(42//t)+2):
        # non_plated_hole(kicad_mod, x=43-i*t,y=100-42-0.5, d=1)
        # non_plated_hole(kicad_mod, x=42+0.5,y=100-41+i*t, d=1)
    
    return write_kicad_mod(kicad_mod,zip=z)

def yygj28_szj25(w100=100,de=2.5,drill_screw=3.9,z=0):
    ''' x 45  斜 28液压管夹 45 '''
    kicad_mod=new_kicad_mod()
    
    x,y=50,50
    a=11
    
    hole_square(kicad_mod,x,y,60,24.85,angle=a,holes=[1,2])
    rectline_center(kicad_mod,x,y,w=60,h=60,angle=a,width=0.1,layers=glayers_F_Cu+glayers_silk) # 
    
    
    return write_kicad_mod(kicad_mod,zip=z)

def pro_test(z=1):
    kicad_mod=new_kicad_mod()
    
    non_plated_hole(kicad_mod,50,50,11)
    multi_dot_line(kicad_mod,[(0,50),(77,50)],layers='F.SilkS',width=0.01)
    multi_dot_line(kicad_mod,[(50,0),(50,50)],layers='B.SilkS',width=0.01)
    
    
    return write_kicad_mod(kicad_mod,zip=z)


def get_szj25(kicad_mod,xz,yz,zd=24.85,h=81.8):
    w_szj=32.1
    h_szj=h
    xz=x+27+1.3+3
    yz=y-dz57
    y_szj=h_szj/2
    rectline_center(kicad_mod,xz,y_szj,w=w_szj,h=h_szj)
    crosshair(kicad_mod,xz,y_szj,w=w_szj,h=h_szj)


def get_szj25_57(kicad_mod,h=81.8,zd=24.85,ayz=24.5,axz=None,dyz2=24.5,dls2x=0,drill_screw=3.9,m6=5.85,m57=True,f_dz57x=None,f_y_szj=None,f_dz57y=None):
    global w57,dz57x,dz57y,d57x2,w_szj,h_szj,y_szj,dyz_szj,dyz_ls2,xz,yz,yz2,dls
    angle=0
    w57=56.6
    
    yz=ayz
    
    
    if py.callable(f_dz57y):
        dz57y=f_dz57y()
    else:    
        dz57y=3.8 #y-yz  # yz高度 25 ==3.3
    y=yz+dz57y  #w57/2
    
    if py.callable(f_dz57x):
        dz57x=f_dz57x()
    else:    
        dz57x=w57/2 + 3
    
    w_szj=32.2
    h_szj=h
    
    if axz:
        xz=axz
    else:
        xz=100-w_szj/2#x+dz57x
    x=xz-dz57x
    
    circle         (kicad_mod,x=xz,y=yz,crosshair=1,diameter=[25,28,40])
    
    if m57:
        step_motor_57(kicad_mod,x,y,drill_screw=2.9,circle_diameter=[10,12,14,22,26,28,30,32])
        step_motor_57(kicad_mod,x,y,drill_screw=drill_screw,holes=[2,3])# 右下角开始逆时针 0，1，2，3
    
    d57x2=x-w57/2
    if d57x2>20:
        step_motor_57(kicad_mod,w57/2,y,drill_screw=drill_screw)
        step_motor_57(kicad_mod,w57/2,w57/2,drill_screw=drill_screw)
    
    
    
    # yz=y-dz57y
    dyz_szj=16.4
    if py.callable(f_y_szj):
        y_szj=f_y_szj()
    else:    
        y_szj=yz+dyz_szj #(y- w57/2)+ h_szj/2
        
    rectline_center(kicad_mod,xz,y_szj,w=w_szj,h=h_szj)
    crosshair(kicad_mod,xz,y_szj,w=w_szj,h=100)
    
    non_plated_hole(kicad_mod,x=xz,y=yz,d=zd)
    
    # yz2=y_szj+4+12.5
    yz2=y_szj+(h_szj/2)-dyz2
    rectline_center(kicad_mod,xz+25,yz2,w=50,h=25,layers=glayers_F_Cu+glayers_silk)
    multi_dot_line(kicad_mod,[(xz-26,yz2),(xz+16,yz2)],layers=glayers_F_Cu+glayers_silk,width=0.01)# 
    
    yls2=76-0.2-(25-yz)
    dls=7
    dyz_ls2=50.35
    yls2=yz+dyz_ls2#h_szj-dls
    #dls2 .05
    
    non_plated_hole(kicad_mod,x=xz-8+dls2x,y=yls2,d=m6)
    non_plated_hole(kicad_mod,x=xz+8+dls2x,y=yls2,d=m6)
        
    non_plated_hole(kicad_mod,x=xz-8,y=yls2,d=m6)# 长条孔
    non_plated_hole(kicad_mod,x=xz+8,y=yls2,d=m6)
    
    
    y2=yz2-dz57y#h_szj-w57/2
    non_plated_hole(kicad_mod,100,y2,1)
    non_plated_hole(kicad_mod,81+0.5+2.8,y2,1)
    zc2=12.75
    multi_dot_line(kicad_mod,[(81,y2-zc2),(100,y2-zc2)],layers=glayers_F_Mask+glayers_silk,width=0.5)# 2轴承上
    multi_dot_line(kicad_mod,[(81,y2),(100,y2)],layers=glayers_F_Mask+glayers_silk,width=0.5)# mask width 0.01 造不出来 
    multi_dot_line(kicad_mod,[(81,y2+zc2),(100,y2+zc2)],layers=glayers_F_Mask+glayers_silk,width=0.5)# 2轴承下
    multi_dot_line(kicad_mod,[(81+1,y2-13),(81+1,y2+13)],layers=glayers_F_Mask+glayers_silk,width=1)# 2轴承里 
    multi_dot_line(kicad_mod,[(100,y2-13),(100,y2+13)],layers=glayers_F_Mask+glayers_silk,width=1)#2轴承外 

    return x,y
    
def szj25_mid(w100=100,de=2.5,drill_screw=3.9,z=0):
    kicad_mod=new_kicad_mod()
    x,y=get_szj25_57(kicad_mod,zd=5.9)
    
    x,y=xz-20,yz2-(dz57y) # z2 电机轴承中心
    rectline_center(kicad_mod,x,y,w=8,h=26,layers=glayers_F_Cu+glayers_silk)
    multi_dot_line(kicad_mod,[(x-6,y),(x+6,y)],layers=glayers_silk,width=0.01)#电机轴 
    
    x,y=15,75
    non_plated_hole(kicad_mod,x,y,25.9)
    circle         (kicad_mod,x,y,crosshair=1,diameter=[26,28,30,40])
    
    x,y=50,80
    non_plated_hole(kicad_mod,x,y,29.9)
    circle         (kicad_mod,x,y,crosshair=1,diameter=[26,28,30,40])
    
    return write_kicad_mod(kicad_mod,zip=z)
    
def szj25_818(w100=100,de=2.5,drill_screw=3.9,z=0):
    '''  '''
    kicad_mod=new_kicad_mod()
    crosshair(kicad_mod,50,50)

    zd=24.85
    zd=5.86
    x,y=get_szj25_57(kicad_mod,zd=zd,h=81.8)
    
    
    
    b57=w57/2+(100-x-w_szj) #28.3+15.1=43.4
    yb57=100-b57
    xb57=100-w_szj-0.8
    multi_dot_line(kicad_mod,[(-1,yb57),(xb57,yb57)],layers=glayers_edge_pure,width=0.01)
    multi_dot_line(kicad_mod,[(-1,yb57),(xb57,yb57)],layers=glayers_edge_pure,width=1.6)
    
    
    multi_dot_line(kicad_mod,[(xb57,yb57),(xb57,h_szj)],layers=glayers_edge_pure,width=1.6)#竖 
    t=4
    for i in range(int(20//t)+2):
        non_plated_hole(kicad_mod, x=xb57,y=yb57+t*i,d=1)
        
    t=1
    for i in range(int(9//t)):#横
        non_plated_hole(kicad_mod, x=100-w_szj+t*i,y=h_szj+0.5,d=1)
    t=1.4
    for i in range(int(12//t)+2):non_plated_hole(kicad_mod, x=100-w_szj+t*i,y=h_szj+0.5,d=1)
    multi_dot_line(kicad_mod,[(100-w_szj-1,h_szj+0.5),(100-w_szj+14,h_szj+0.5)],layers=glayers_F_Mask,width=2)    
    # non_plated_hole(kicad_mod,x=h_szj+0.5,y=h_szj+0.5,d=1)
        
    t=2.4
    for ix,iy in U.iter2d(9,9):
        non_plated_hole(kicad_mod,x=h_szj+0.5+t*ix,y=h_szj+0.5+t*iy,d=1)    
    square(kicad_mod,91,91,18.3,layers=glayers_F_Mask) #填充
    # N.rpc_set(base='http://192.168.1.3:1122/',ext_cmd='print(a)',a=[x,y])

        
    # add_new_hole(kicad_mod, x=xz, y=yz, d=zd, angle=180+40, distance=45)
    # crosshair(kicad_mod,62,50-8.6,layers=glayers_F_Cu+glayers_silk,w=33)
    
    # multi_dot_line(kicad_mod,[(xz,0),(xz,101)],layers=glayers_silk,width=0.01)
    
    
    
    # k25=dict(kicad_mod=kicad_mod,x=xz,y=yz)
    
    circle         (kicad_mod,x=xz,y=yz,crosshair=1,diameter=[25,28,40])
    
    x=w57/2
    # y=100-x
    # y0=100-x-w_szj/2
    # y=y0+x
    y=100-(dz57x-w_szj/2)
    step_motor_57(kicad_mod,x,y,drill_screw=3.9,holes=[],d=25.83) # 0,3 
    # hole_square(kicad_mod,x,y,31,2.95,angle=45,)
    # step_motor_57(kicad_mod,x,y+d57x2,drill_screw=3.9,holes=[],d=11) # 0,3 
    step_motor_57(kicad_mod,x,y-d57x2,drill_screw=3.9,holes=[0,3],d=2.95,rectline_layers=glayers_Cmts) # 0,3 
    
    
    circle       (kicad_mod,x=x,y=y,crosshair=1,diameter=[25,28,30])
    dzls=h_szj-xz-7
    # szj2=
    rectline_center(kicad_mod,h_szj/2,y,w=h_szj,h=w_szj)
    non_plated_hole(kicad_mod,h_szj-dls,y+8,3.9)
    non_plated_hole(kicad_mod,h_szj-dls,y-8,1)
    
    
    
    # circle       (kicad_mod,h_szj-yz,y,crosshair=1,diameter=[25,26,28,40])
    
    multi_dot_line(kicad_mod,[(h_szj-yz,y-8),(h_szj-yz,y+8)],layers=glayers_silk,width=5.85)
    multi_dot_line(kicad_mod,[(h_szj-yz,y-w_szj/2),(h_szj-yz,101)],layers=glayers_silk,width=0.01)
    non_plated_hole(kicad_mod,h_szj-yz,yb57+1,1)
    non_plated_hole(kicad_mod,h_szj-yz,100.2,1)
    
    multi_dot_line(kicad_mod,[(dls,y-w_szj/2),(dls,101)],layers=glayers_silk,width=0.01)
    multi_dot_line(kicad_mod,[(dls,y-7),(dls,y-8)],layers=glayers_silk,width=5.85) # 单独点，没有长度 在lceda不显示
    non_plated_hole(kicad_mod,dls,yb57+1,1)
    non_plated_hole(kicad_mod,dls,100.2,1)
    
    # multi_dot_line(kicad_mod,[(100-32.2,h_szj+0.8),(100,h_szj+0.8)],layers=glayers_edge_pure,width=0.01)
    # multi_dot_line(kicad_mod,[(100-32.2-0.8,w57+0.8),(100-32.2-0.8,h_szj+0.8)],layers=glayers_edge_pure,width=0.01)
    
    
    # N.rpc_set(base='http://192.168.1.3:1122/',ext_cmd='print(a)',a=[yz,yz2,h_szj-yz2])
    
    return write_kicad_mod(kicad_mod,zip=z)
    
def yygj25(w100=100,de=2.5,drill_screw=3.9,z=0):
    kicad_mod=new_kicad_mod()
    crosshair(kicad_mod,50,50)
    
    x=50
    y=100-24
    angle=0
    rc_ka=dict(kicad_mod=kicad_mod,x0=x,y0=y,angle=angle,width=0.1,layers=glayers_F_Cu+glayers_silk)
    rectline_center(**rc_ka,w=83,h=48)    
    multi_dot_line(kicad_mod,[(x-42,y),(x+42,y)],layers=glayers_silk,width=0.01)
    for i in [-1,1]:
        non_plated_hole(kicad_mod,x+(45/2)*i,y,24.9)
        circle         (kicad_mod,x+(45/2)*i,y,crosshair=1,diameter=[25,28,40])
    # non_plated_hole(kicad_mod,x-45/2,y,24.9)
    
    # y-=4.25
    y-=4.25+1.45
    rc_ka['y0']=y
    circle(kicad_mod,x,y,diameter=[1,3,4,5,6,6.35,8,10,12,100*1.414243],crosshair=1,layers=glayers_silk) # ,25,28,40
    non_plated_hole(kicad_mod,x,y,4.9)

            
    hole_square(kicad_mod,x,y,31,2.95,angle=45,)
    rectline_center(**U.dict_update_return_new(rc_ka,angle=45),w=42)

    hole_square(kicad_mod,x,y,47,3.9,angle=angle,)
    rectline_center(**rc_ka,w=56.5)
    
    # non_plated_hole(kicad_mod,x,24,39.9)
    # non_plated_hole(kicad_mod,20,20,39.9)
    # e=5
    # non_plated_hole(kicad_mod,e,e,2.95)
    e=5
    non_plated_hole(kicad_mod,100-e,e,2.95)
    e=5.05
    non_plated_hole(kicad_mod,e,100-e,2.95)
    e=4.9
    non_plated_hole(kicad_mod,100-e,100-e,2.95)
    
    dj=4.8
    j1=10.5-dj
    j2=16.5-dj
    for x,y in ([j1+3,j1+3],[50,j1+3],[97-j1,j1+3]):
        non_plated_hole(kicad_mod,x-3,y-3,drill_screw)
        non_plated_hole(kicad_mod,x+3,y+3,drill_screw)
    y0=(j1+3)*2    
    multi_dot_line(kicad_mod,[(0,y0),(101,y0)],layers=glayers_silk,width=0.01)    
    j1=10.5    
    yz=y0+j1+3
    for x,y in ([j1+3,yz],[50,yz],[97-j1,yz]):
        non_plated_hole(kicad_mod,x-3,y-3,drill_screw)
        non_plated_hole(kicad_mod,x+3,y+3,drill_screw)
        
    # non_plated_hole(kicad_mod,j1,53,drill_screw)    # 左右
    # non_plated_hole(kicad_mod,j2,47,drill_screw)    
    # non_plated_hole(kicad_mod,w100-j2,53,drill_screw)    
    # non_plated_hole(kicad_mod,w100-j1,47,drill_screw)    
    
    # non_plated_hole(kicad_mod,47,j1,drill_screw)  #上下
    # non_plated_hole(kicad_mod,53,j2,drill_screw)
    
    
    return write_kicad_mod(kicad_mod,zip=z)
    
    
def hua4fl(w100=100,de=2.5,drill_screw=3.9,z=0):
    kicad_mod=new_kicad_mod()
    x,y=50,50
    angle=0
    circle(kicad_mod,x,y,diameter=[1,3,4,5,6,25,28,40,100*1.414243],crosshair=1,layers=glayers_silk)
    rc_ka=dict(kicad_mod=kicad_mod,x0=x,y0=y,angle=angle,width=0.1,layers=glayers_F_Cu+glayers_silk)
            
    hole_square(kicad_mod,x,y,31,2.95,angle=angle,)
    rectline_center(**rc_ka,w=42)

    hole_square(kicad_mod,x,y,47,3.9,angle=angle,)
    rectline_center(**rc_ka,w=56.5)
    
    
    de=20
    for n,(x,y) in enumerate(edge_distance(w100,w100,[de,de])):
        # hole_square(kicad_mod,x,y,31,2.95,angle=0,)
        non_plated_hole(kicad_mod,x,y,5.95)
        circle(kicad_mod,x,y,crosshair=1,diameter=[6,12]) #,15,19,21,28,40
        hole_square(kicad_mod,x,y,14.143,2.95,angle=angle,)
        
            
    return write_kicad_mod(kicad_mod,zip=z)
    
def hua4ce(w100=100,de=2.5,drill_screw=3.9,z=0):
    kicad_mod=new_kicad_mod()
    crosshair(kicad_mod,50,50)
    
    dj=4.8
    j1=10.5-dj
    j2=16.5-dj
    for x,y in edge_distance(w100,w100,[j1+3,j1+3]):
        non_plated_hole(kicad_mod,x+3,y-3,drill_screw)
        non_plated_hole(kicad_mod,x-3,y+3,drill_screw)
        
    return write_kicad_mod(kicad_mod,zip=z)
    
def z25(w100=100,de=2.5,drill_screw=3.9,z=0):
    kicad_mod=new_kicad_mod()
    crosshair(kicad_mod,50,50)
    
    
    d47=(56.5-47)/2
    # plated_hole_square_vertice_start(kicad_mod,d47,d47,47,3.9)
    # plated_hole_square_vertice_start(kicad_mod,d47+47,d47+47,47,3.9,angle=45)
    
    w57=56.6
    x=y=w57/2
    for x,y in [(x,y),(100-x,100-y)]:
        if x==w57/2:
            non_plated_hole(kicad_mod,x,y,24.95)  #57
        else:    
            non_plated_hole(kicad_mod,x,y,2.95)  #57
            
        
        for angle in [0,45]:
            rc_ka=dict(kicad_mod=kicad_mod,x0=x,y0=y,angle=angle,width=0.1,layers=glayers_F_Cu+glayers_silk)
            
            hole_square(kicad_mod,x,y,31,2.95,angle=angle,)
            rectline_center(**rc_ka,w=42)
        
            hole_square(kicad_mod,x,y,47,3.9,angle=angle,)
            rectline_center(**rc_ka,w=w57)
            
    U.dict_multi_pop(rc_ka,'x0','y0','angle')    
    rc_ka['layers']=glayers_silk
    x,y=75+4,25-4        
    non_plated_hole(kicad_mod,x,y,6.8)
    hole_square(kicad_mod,x,y,31,2.95,angle=0,)
    rectline_center(**rc_ka,x0=x,y0=y,w=42)    
    
    x,y=25-4,75+4
    non_plated_hole(kicad_mod,x,y,8.4)
    hole_square(kicad_mod,x,y,31,2.95,angle=0,)
    rectline_center(**rc_ka,x0=x,y0=y,w=42)    
    
    
    return write_kicad_mod(kicad_mod,zip=z)
    
    

def hua4(w100=100,de=2.5,drill_screw=3.9,z=1):
    kicad_mod=new_kicad_mod()
    dx=50
    circle(kicad_mod,dx,50,diameter=[1,3,4,5,6,8,10,12,31*1.414],crosshair=1,layers=glayers_silk)
    non_plated_hole(kicad_mod,dx,50,8.85)
    hole_square    (kicad_mod,dx,50,31,2.95,angle=45)
    rectline_center(kicad_mod,dx,50,w=42,h=42,angle=45,width=0.1,layers=glayers_F_Cu+glayers_silk) # 
    
    
    de=20
    for n,(x,y) in enumerate(edge_distance(w100,w100,[de,de])):
        # hole_square(kicad_mod,x,y,31,2.95,angle=0,)
        non_plated_hole(kicad_mod,x,y,5.95)
        circle(kicad_mod,x,y,crosshair=1,diameter=[6,12,15,19,21,28,40])
        
    
    # j1=10.5
    # j2=16.5
    # for x,y in ([j1,j2],[j2,j1],):
        # non_plated_hole(kicad_mod,x,50-j1-3+y,drill_screw)
    # for x,y in ([j1,j1],[j2,j2]):    
        # non_plated_hole(kicad_mod,w100-x,50-j1-3+y,drill_screw)
        
        
    dj=4.8
    j1=10.5-dj
    j2=16.5-dj
    for x,y in edge_distance(w100,w100,[j1+3,j1+3]):
        non_plated_hole(kicad_mod,x+3,y-3,drill_screw)
        non_plated_hole(kicad_mod,x-3,y+3,drill_screw)
        
    non_plated_hole(kicad_mod,j1,53,drill_screw)    # 左右
    non_plated_hole(kicad_mod,j2,47,drill_screw)    
    non_plated_hole(kicad_mod,w100-j2,53,drill_screw)    
    non_plated_hole(kicad_mod,w100-j1,47,drill_screw)    
    
    non_plated_hole(kicad_mod,47,j1,drill_screw)  #上下
    non_plated_hole(kicad_mod,53,j2,drill_screw)
    non_plated_hole(kicad_mod,53,w100-j1,drill_screw)
    non_plated_hole(kicad_mod,47,w100-j2,drill_screw)    
    
    as5600(kicad_mod=kicad_mod)
    
    return write_kicad_mod(kicad_mod,zip=z)

def m3_main3(dy2b=30,dx=18.3-6,angle=45,w=33,write=True):
    kicad_mod=new_kicad_mod(f'm3main_{dy2b}',w=w,h=100,)
    
    if write:dx=w/2
    circle(kicad_mod,dx,50,diameter=[1,22,66.6],crosshair=1,layers=glayers_silk)
    
    non_plated_hole(kicad_mod,dx,50-dy2b,8.85)
    hole_square    (kicad_mod,dx,50-dy2b,31,2.95,angle=0,holes=(0,1,2,))
    
    non_plated_hole(kicad_mod,dx,50,8.85)
    hole_square    (kicad_mod,dx,50,31,2.95,angle=0)
    rectline_center(kicad_mod,dx,50,w=42,h=42,width=0.1,layers=glayers_F_Cu+glayers_silk) # 
    
    non_plated_hole(kicad_mod,dx,50+dy2b,8.85)
    hole_square    (kicad_mod,dx,50+dy2b,31,2.95,angle=0,holes=(0,2,3)) # 右下角 0 逆时针
    
    if write:
        km,fname=write_kicad_mod(kicad_mod)
        return km,fname
    return kicad_mod
    
def m3_hua_gai(w100=100,de=2.5):
    kicad_mod=new_kicad_mod(m3_hua.__name__,)
    dz=27
    non_plated_hole(kicad_mod,50,dz,8.9)
    rectline_center(kicad_mod,50,dz,w=42,h=42,width=0.1,layers=glayers_F_Cu+glayers_silk) # 
    circle(kicad_mod,50,dz,diameter=[1,3,5,9,(100-dz)*2*(1.116+0.0035*dz)],crosshair=1,layers=glayers_silk)
    
    
    for i in range(3):
        if i==1:continue
        x=33.333/2+33.333*i
        non_plated_hole(kicad_mod,x,dz,8.95)
    hole_square(kicad_mod,50,dz,31,2.95,angle=0,)
    
    
    y=dz+50+19
    w=59.8
    non_plated_hole(kicad_mod,50-w/2,y,5.9)
    non_plated_hole(kicad_mod,50+w/2,y,5.9)
    multi_dot_line(kicad_mod,[(50-35,y),(50+35,y)],layers=glayers_silk,width=2)

    # km,fname=m3(dx=0)
    # km.SetOrientation(90)
    kicad_mod.append(km)

    return write_kicad_mod(kicad_mod)
    
def m3_hua(w100=100,de=2.5):
    kicad_mod=new_kicad_mod(m3_hua.__name__,)
    dz=6
    non_plated_hole(kicad_mod,50,dz,4.4)
    circle(kicad_mod,50,dz,diameter=[1,3,5,9,(100-dz)*2*1.137],crosshair=1,layers=glayers_silk)
    for i in range(3):
        if i==1:continue
        x=33.333/2+33.333*i
        non_plated_hole(kicad_mod,x,dz,8.95)
    
    
    
    bj=[(0,dz+50-4.8-17),(22.3,dz+50-4.8-17),(22.3,dz+50-4.8),(0,dz+50-4.8),(0,dz+50-4.8-17)]
    multi_dot_line(kicad_mod,bj,layers=glayers_silk,width=0.01)
    symmetric_x(kicad_mod,bj,xm=100,xmid=50,x0=0, y0=0,angle=0,layer=['Edge.Cuts','F.SilkS','Edge.Cuts','B.SilkS'],width=0.01)
    
    
    
    
    y=dz+50
    multi_dot_line(kicad_mod,[(0,y),(100,y)],layers=glayers_silk,width=0.01)
    y=dz+50+9
    non_plated_hole(kicad_mod,50,y,1)
    circle(kicad_mod,50,y,diameter=[1,2,2.8,4,5,6,],crosshair=1,layers=glayers_silk)
    hole_square(kicad_mod,50,y-47/2,47,2.9,angle=0)
    hole_square        (kicad_mod,50,y-47/2,47,3.9,angle=0,func=circle)
    circle(kicad_mod,50,y-47/2,diameter=[1,3,6.35,156.6],crosshair=1,layers=glayers_silk)
    non_plated_hole(kicad_mod,50,y-47/2,d=1,)
    
    y=dz+50+19
    w=59.8
    non_plated_hole(kicad_mod,50-w/2,y,6)
    non_plated_hole(kicad_mod,50+w/2,y,6)
    multi_dot_line(kicad_mod,[(50-35,y),(50+35,y)],layers=glayers_silk,width=2)

    
    y=dz+50+19+20
    multi_dot_line(kicad_mod,[(50-6,y),(50+6,y)],layers=glayers_silk,width=0.5)
    
    for nx,x in enumerate(range(10,100,10)):
        for y in [60,70,80,90]:
            if y==60 and nx in [1,2,6,7]:continue
            if y==70 and nx in [2,3,4,5,6]:continue
            non_plated_hole(kicad_mod,x,y+5,1.95)

    return write_kicad_mod(kicad_mod)
    
def m345_42motor(w100=100,de=2.5):
    kicad_mod=new_kicad_mod(m345.__name__,)
    circle(kicad_mod,50,50,diameter=[1,100*1.414],crosshair=1,layers=glayers_silk)

    d=0.8
    
    dnd={0:2.95,1:4.95,2:8.9,3:22.1}
    for n,(x,y) in enumerate(edge_distance(w100,w100,[25-d,25-d])):
        hole_square(kicad_mod,x,y,31,2.95,angle=0,)
        non_plated_hole(kicad_mod,x,y,dnd[n])
        multi_dot_line(kicad_mod,[(x,0),(x,100)],layers=glayers_silk,width=0.01)
        multi_dot_line(kicad_mod,[(0,y),(100,y)],layers=glayers_silk,width=0.01)
        
    
    multi_dot_line(kicad_mod,[(0+de,50),(100-de,50)],layers=glayers_silk,width=0.1) #开槽
    multi_dot_line(kicad_mod,[(50,0+de),(50,100-de)],layers=glayers_silk,width=0.1)
    for i in range(50):
        non_plated_hole(kicad_mod,i*2,50,1)
        non_plated_hole(kicad_mod,50,i*2,1)

    
    
    
    d=0.2
    rectangle_outline(kicad_mod,0+d,0+d,w=100-d*2,h=100-d*2,width=0.1,layers=glayers_F_Cu) # 
    
    return write_kicad_mod(kicad_mod)
    
m345_hole=m345_42motor    
    
def m3(w100=100,dx=18.3-6,dy2b=30,drill_screw=3.3):
    ''' dy2b      两边的孔距离中心  '''
    kicad_mod=new_kicad_mod(f'm3_{drill_screw}')
    
    ha=17
    hr=11.5
    hl=ha-hr

    ja=22.3
    jbd=25.9-ja
    
    j1=10.5
    j2=16.5
    
    hy0=7.5
    
    # xy4=[j1,j1],[j1,j2],[j2,j1],[j2,j2]
    for x,y in edge_distance(w100,w100,[j1+3,j1+3]):
        non_plated_hole(kicad_mod,x+3,y-3,drill_screw)
        non_plated_hole(kicad_mod,x-3,y+3,drill_screw)
    
    for x,y in ([j1,j2],[j2,j1],):
        non_plated_hole(kicad_mod,x,50-j1-3+y,drill_screw)
    for x,y in ([j1,j1],[j2,j2]):    
        non_plated_hole(kicad_mod,w100-x,50-j1-3+y,drill_screw)
        
        # non_plated_hole(kicad_mod,50-j1-3+x,y,drill_screw)
        # non_plated_hole(kicad_mod,50-j1-3+x,100-y,drill_screw)
        
    non_plated_hole(kicad_mod,47,j1,drill_screw)
    non_plated_hole(kicad_mod,53,j2,drill_screw)    
    circle(kicad_mod,53,j1-6,drill_screw)    
    circle(kicad_mod,53,j1-6,drill_screw)    
    
    non_plated_hole(kicad_mod,53,w100-j1,drill_screw)
    non_plated_hole(kicad_mod,47,w100-j2,drill_screw)    
    circle(kicad_mod,53,j1-6,drill_screw)    
    circle(kicad_mod,w100-j2,j1-6,drill_screw)    
        
        # N.rpc_set(base='http://192.168.1.3:1122/',ext_cmd='print(a)',a=[i,y])
    f6=16.666
    for i in range(1,6):
        y=f6*i
        multi_dot_line(kicad_mod,[(0,y),(w100,y)],layers=glayers_silk)
        multi_dot_line(kicad_mod,[(y,0),(y,w100)],layers=glayers_silk)
    
    return write_kicad_mod(kicad_mod)
    
    circle(kicad_mod,50+dx,50,diameter=[1,22,66.6],crosshair=1,layers=glayers_silk)
    
    
    
    # hole_square(kicad_mod,50,f6*1,31,2.95,angle=0,func=circle)
    # hole_square(kicad_mod,50,f6*5,31,2.95,angle=0,func=circle)
    
    # for i in range(3):
        # y=f6+33.333*i
    # def func(*a):
        # N.rpc_set(base='http://192.168.1.3:1122/',ext_cmd='print(a)',a=a)
        # non_plated_hole(*a)
        
    non_plated_hole(kicad_mod,50+dx,50-dy2b,8.85)
    hole_square    (kicad_mod,50+dx,50-dy2b,31,2.95,angle=0,holes=(0,1,2,))
    
    non_plated_hole(kicad_mod,50+dx,50,8.85)
    hole_square    (kicad_mod,50+dx,50,31,2.95,angle=0)
    
    non_plated_hole(kicad_mod,50+dx,50+dy2b,8.85)
    hole_square    (kicad_mod,50+dx,50+dy2b,31,2.95,angle=0,holes=(0,1,3)) # 右下角 0 逆时针

    
def gear_15_10_jz():
    kicad_mod=new_kicad_mod(gear_15_10_jz.__name__)
    xh=42.4
    w57=56.5
    x0=100-(xh+w57)
    
    multi_dot_line(kicad_mod,[(x0,0),(x0,100)],layers=glayers_silk)
    mx=x0+xh
    multi_dot_line(kicad_mod,[(mx,0),(mx,100)],layers=glayers_silk)
    multi_dot_line(kicad_mod,[(x0,100-90),(mx,100-90)],layers=glayers_silk)
    mx=x0+xh/2
    multi_dot_line(kicad_mod,[(mx,0),(mx,100)],layers=glayers_silk)
    n=3+1
    ni=90/n
    for i in range(1,n):
        # non_plated_hole(kicad_mod,mx,100-(ni*i),3.9)
        circle(kicad_mod,mx,100-(ni*i),[0.2,2,3,4,5,6,8])
        # if i==(n/2):
        non_plated_hole(kicad_mod,mx,100-(ni*i),1.9)
        
    # non_plated_hole(kicad_mod,mx,75,3.9)
    
    hz57=100-(30+24.5)
    multi_dot_line(kicad_mod,[(0,hz57),(100,hz57)],layers=glayers_silk)
        
    x57=100-w57/2    
    non_plated_hole(kicad_mod,x57,hz57,6.35) #
    hole_rect_center(kicad_mod,x57,hz57,47,d=3.9,func=non_plated_hole,holes=[0,1,2,3])    
    rectline_center(kicad_mod,x57,hz57,w57,w57,layers=glayers_silk)     
    

    hole_rect_center(kicad_mod,mx+47/2,hz57,47,d=1.9,func=non_plated_hole,holes=[2,3])#右下0逆时针
    hole_rect_center(kicad_mod,mx+47/2,hz57,47,d=[0.2,2,3,4,5,6,8],func=circle,holes=[2,3])#右下0逆时针
    # hole_rect_center(kicad_mod,mx,hz57,47,d=3.9,angle=45,func=non_plated_hole,holes=[1,3])#右下0逆时针
    # non_plated_hole(kicad_mod,mx+47/2,hz57,6.35) #
    # hole_rect_center(kicad_mod,mx-47/2,hz57,47,d=3.9,func=non_plated_hole)
    # non_plated_hole(kicad_mod,mx-47/2,hz57,6.35) #
    # non_plated_hole(kicad_mod,mx,hz57+47/2,3.9)
    # non_plated_hole(kicad_mod,mx,hz57-47/2,3.9)
    non_plated_hole(kicad_mod,x0+2.9+1.6,10-2.9,5.85)
    non_plated_hole(kicad_mod,x0+xh-2.9-1.6,10-2.9,5.85)
    
    non_plated_hole(kicad_mod,mx,hz57,1.9)
    non_plated_hole(kicad_mod,mx,hz57+47,1.9)
    
    return write_kicad_mod(kicad_mod)
def gear_15_50():
    import math
    kicad_mod=new_kicad_mod(gear_15_50.__name__+'f',w=0,h=0)  # -{U.stime()}
    glayers_silk=glayers_silk#['F.SilkS']
    kicad_mod.append(KicadModTree.RectLine(start=[0,0],end=[100,100], layer='F.SilkS'))
    ek=30
    multi_dot_line(kicad_mod,[(0,50-ek),(0,50+ek)],layers=glayers_edge_pure)    
    multi_dot_line(kicad_mod,[(100,50-ek),(100,50+ek)],layers=glayers_edge_pure)    
    multi_dot_line(kicad_mod,[(50-ek,0),(50+ek,0)],layers=glayers_edge_pure)    
    multi_dot_line(kicad_mod,[(50-ek,100),(50+ek,100)],layers=glayers_edge_pure)    
    
    x0=y0=50
    # circle(kicad_mod,x0,y0,diameter=115,layers=glayers_edge_pure)
    rd=115/2
    for i in range(4):
        radian = math.radians(i * 90+ 29.5)   # 将角度转换为弧度
        x=x0+ rd * math.cos(radian)
        y=y0+ rd * math.sin(radian)
        
        arc(kicad_mod,center=[x0,y0], start=[x,y],angle=31, layers=['F.SilkS','Edge.Cuts'],width=0.01)
        # arc(kicad_mod,center=[x0,y0], start=[x0+rd,y0],angle=50, layers=['F.SilkS','Edge.Cuts','B.SilkS'],width=0.01)
    
    # multi_dot_line(kicad_mod,[(0,y0),(100,y0)],layers=glayers_silk)
    non_plated_hole(kicad_mod,x0,y0,7.8)
    circle(kicad_mod,x0,y0,diameter=[8.5,9.8,11,12,16,18,20,24,73,74,74.8,76,109,115],crosshair=1,layers=glayers_silk)
    # circle(kicad_mod,x0,y0,diameter=[9.9,11,12,13,14,15,16,75])
    r=11.9
    n=6
    a=360/n
    for i in range(n):
        if i%2==0:
            r=9+2
            
        else:
            r=12+2
        radian = math.radians(i * a+ a/4)   # 将角度转换为弧度
        x=x0+ r * math.cos(radian)
        y=y0+ r * math.sin(radian)
        
            
        radian = math.radians(i * a+ a/2)   # 将角度转换为弧度
        cx=x0+ r * math.cos(radian)
        cy=y0+ r * math.sin(radian)
#     4        
#3        5
# 2   0
#    1
        dk=1.95
        if i in [4,1]:dk=1.95
        if i in [2,5]:dk=3
        if i in [0,3]:dk=3.9
        non_plated_hole(kicad_mod,cx,cy,dk)
        circle(kicad_mod,cx,cy,diameter=[2.5,3.1,4],layers=glayers_silk)
    
    return write_kicad_mod(kicad_mod)