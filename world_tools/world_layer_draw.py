from PySide import QtGui, QtCore
from os.path import dirname, abspath
import xml.etree.cElementTree as ET
import random

world_layers = [r"W:\main\data\Worlds\London\Objects\User\01_CityOfLondon\00_COL_Subdivisions\00_COL_City_Blocks.xml",
                r"W:\main\data\Worlds\London\Objects\User\05_Hackney_Islington\00_HAC_Subdivisions\00_HAC_City_Blocks.xml",
                r"W:\main\data\Worlds\London\Objects\User\06_TowerHamlets_West\00_THW_Subdivisions\00_THW_City_Blocks.xml",
                r"W:\main\data\Worlds\London\Objects\User\07_TowerHamlets_East\00_THE_Subdivisions\00_THE_City_Blocks.xml",
                ]
                
             
def generate_random_color():
    # r = random.randint(0,255)
    # g = random.randint(0,255)
    # b = random.randint(0,255)
    
    
    
    return QtGui.QColor("#ffffff")

def get_shapes(offset, scale):
    shape_dict = {}
    for world_layer in world_layers:
        tree = ET.ElementTree(file=world_layer)
        for elem in tree.iter("Object"):
            name = elem.get("Name")
            pos = elem.get("Pos")
            pos = pos.split(",")
            pos_x = float(pos[0]) * -1 *scale
            pos_y = float(pos[1]) * scale
            pos_z = float(pos[2]) * scale
            for sub_elem in elem.iter("DebugAnnotationObject"):
                points = sub_elem.get("Points")
                points = points.split(" ")[1]
                points = points.split(";")
                qpoints = []
                for point in points:
                    if point == "":
                        continue
                    point = point.split(",")
                    x,y,z = float(point[0]),float(point[1]),float(point[2])
                    x = x * -1 * scale + offset + pos_x
                    y = y * scale + offset + pos_y
                    z = z * scale + offset + pos_z
                    qpoints.append(QtCore.QPoint(x,y))
                color = sub_elem.get("clrColor")
                color = color.split(",")
                r,g,b = float(color[0])*255,float(color[1])*255,float(color[2])*255
                qcolor = QtGui.QColor(r,g,b)
                shape_dict[name] = qpoints, qcolor
    return shape_dict
     
def draw_shape(painter, points, color, width, outline=True, fill=False):
    if outline:
        pen = QtGui.QPen()
        pen.setJoinStyle(QtCore.Qt.MiterJoin)
        pen.setWidth(width)
        pen.setColor(color)
        painter.setPen(pen)
    if fill:
        brush = QtGui.QBrush(color)
        painter.setBrush(brush)
    shape = QtGui.QPolygon(points)
    painter.drawPolygon(shape)
    
def main():
    world_size = 8192.0
    cur_path = dirname(abspath(__file__))   
    background = QtGui.QImage(cur_path + r"\background.png")
    offset = background.height()/2
    scale = background.height()/world_size
    shape_dict = get_shapes(offset,scale)     
    painter = QtGui.QPainter()
    painter.begin(background)
    step = 1#16777215 / len(shape_dict)
    counter = 1
    for name, pointscolor in shape_dict.iteritems():
        print "#{0:06x}".format(counter)
        draw_shape(painter, pointscolor[0], QtGui.QColor("#{0:06x}".format(counter)), 5, True, True)
        counter += step
        if counter >= 16777215:
            print name,": Colour exceeded max value, city block will show up black or white, problem!!!"
    painter.end()
    background.save(cur_path + r"\result.png")
    
main()