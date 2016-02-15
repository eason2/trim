# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui
import DraftGeomUtils,DraftVecUtils
import FreeCAD,FreeCADGui
import Draft
import Part
global mysel
mysel = []
try:
    _fromUtf8 = QtCore.QString.fromUtf8


except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)


except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class StandSelObserver: # sel
    def addSelection(self,doc,obj,sub,pnt):  # Selection
        global mysel
        if len(sub) > 0:
            sel = FreeCADGui.Selection.getSelection()
            if sel:
                subsel = FreeCADGui.Selection.getSelectionEx()[-1].SubObjects[-1]
                if type(subsel) == Part.Edge:
                    myobj = FreeCAD.ActiveDocument.getObject(obj)
                    mypos = FreeCAD.Vector(pnt[0],pnt[1],pnt[2])
                    mysel = [myobj,mypos,subsel]
                    FreeCAD.ActiveDocument.openTransaction("trim")
                    trim()
                    FreeCAD.ActiveDocument.commitTransaction() 
                    FreeCADGui.Selection.clearSelection()


                else:
                    prf('type(obj) is not Edge...do not run...')

class Ui_ee(object):
    def __init__(self):
        global eeui
        self.setupUi()
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.call = self.view.addEventCallback("SoEvent",self.action)


    def action(self,arg):
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.close()


    def close(self):
        global StaSel
        self.view.removeEventCallback("SoEvent",self.call)
        FreeCADGui.Control.closeDialog()
        FreeCADGui.Selection.removeObserver(StaSel)
        prf('close')


    def accept(self): #  OK
        self.close()


    def reject(self):# Cancel
        self.close()


    def setupUi(self):
        widget1 = QtGui.QWidget()
        widget1.setWindowTitle(QtGui.QApplication.translate("Form", " 2D trim", None,QtGui.QApplication.UnicodeUTF8))

        self.layout = QtGui.QGridLayout(widget1)
        self.layout.setSpacing(5)
        self.layout.setColumnMinimumWidth(0,10)

        self.form = [widget1]
        self.OK = QtGui.QPushButton(widget1)
        self.OK.setObjectName(_fromUtf8("OK"))
        self.layout.addWidget(self.OK,3,1)

        QtCore.QObject.connect(self.OK, QtCore.SIGNAL("clicked()"), self.close)
        self.OK.setText(QtGui.QApplication.translate("eeui", "close", None, QtGui.QApplication.UnicodeUTF8))

def trim():# main
    global mysel
    obj = mysel[0]
    pos = mysel[1]
    sub = mysel[2]
    myobj = obj
    obj = downgrade_start_obj(obj)# downgrade
    for i in obj: # delete what you click
        if DraftGeomUtils.isSameLine(i.Shape.Edge1,sub):
            myobj = i
            #FreeCAD.ActiveDocument.removeObject(i)
            break


    FreeCAD.ActiveDocument.recompute()
    allobjs=FreeCAD.ActiveDocument.Objects
    allobjs.remove(myobj)
    connet_edge_list = []
    connet_obj_list = []
    for i in allobjs:
        if str(type(i)) <> "<type 'App.DocumentObjectGroup'>" and FreeCADGui.ActiveDocument.getObject(i.Name).Visibility==True:
            for edge in i.Shape.Edges: # edges in obj
                if DraftGeomUtils.findIntersection(edge,sub): # if there is a interpoint in edge and sub_edge(click)...
                    connet_edge_list.append(edge)
                    connet_obj_list.append(i)
                    prf('Edge Inter ( click edge )',i.Name)


    prf('connet edge num',len(connet_edge_list))
    if len(connet_edge_list) == 0:
        prf('find no intersectionpoint,delete the obj!')
        FreeCAD.ActiveDocument.removeObject(myobj.Name)


    elif len(connet_edge_list) == 1:
        objs = downgrade_obj([myobj,mkobj(connet_edge_list[0])])
        myedge = getinteredge(objs,pos)
        FreeCAD.ActiveDocument.removeObject(myedge.Name)


    elif len(connet_edge_list) > 1:
        myedge = mkobj(getinteredge(connet_edge_list,pos,True))
        obj1 = downgrade_obj([myobj,myedge])
        myedge = getinteredge(obj1,pos)
        if len(obj1) == 1:
            FreeCAD.ActiveDocument.removeObject(obj1[0].Name)
            return()


        if obj1[0].Name == myedge.Name:
            another_edge = obj1[1]


        else: 
            another_edge = obj1[0]


        click_edge = myedge
        my_new_connet_edge = []
        for i in connet_edge_list:
            if DraftGeomUtils.findIntersection(i,click_edge.Shape.Edge1):
                if not DraftGeomUtils.findIntersection(i,another_edge.Shape.Edge1):
                    my_new_connet_edge.append(i)


        if my_new_connet_edge:
            myedge1 = mkobj(getinteredge(my_new_connet_edge,pos,True))
            myobj = downgrade_obj([myedge,myedge1])
            myedge = getinteredge(myobj,pos) # del obj
            FreeCAD.ActiveDocument.removeObject(myedge.Name)


        else:
            FreeCAD.ActiveDocument.removeObject(click_edge.Name)


    FreeCAD.ActiveDocument.recompute()


def getinteredge(alist,pnt,shape = False): # objlist and a Vertex
    if type(alist) <> list:
        return(alist)


    if shape:
        D = max
        obj=0
        pt = Part.Vertex(pnt)
        for i in alist:
            d = getd(i,pt)
            if d < D:
                D = d
                obj = i


        return(obj)


    else:
        D = max
        obj=0
        pt = Part.Vertex(pnt)
        for i in alist:
            d = getd(i.Shape.Edge1,pt)
            if d < D:
                D = d
                obj = i


        return(obj)


def getd(s1,s2): # distToShape
    return(s1.distToShape(s2)[0])


def prf(m,p=0): # print on report view
    if p==0: FreeCAD.Console.PrintMessage('\n'+str(m))
    else: FreeCAD.Console.PrintMessage('\n'+str(m)+':'+str(p))


def downgrade_start_obj(obj): # downgrade objs
    #prf('downgrade...start')
    if type(obj) <> list:
        obj = [obj]


    if len(obj) == 1 :
        if len(obj[0].Shape.Edges) > 1:
            obj = Draft.downgrade(obj[0],delete=True)[0]
            if len(obj) == 1:
                if len(obj[0].Shape.Edges) > 1:
                    obj = Draft.downgrade(obj[0],delete=True)[0]
                    if len(obj) == 1:
                        if len(obj[0].Shape.Edges) > 1:
                            obj = Draft.downgrade(obj[0],delete=True)[0]


    FreeCAD.ActiveDocument.recompute()
    return(obj)


def downgrade_obj(obj): # downgrade objs
    dobj = obj
    if type(obj) <> list:
        obj = [obj]


    if len(obj) == 1:
        for i in range(3):
            if len(obj[0].Shape.Edges) > 1:
                obj = Draft.downgrade(obj[0],delete=True)[0]


    elif len(obj) > 1: # cut
        obj = Draft.downgrade(obj,delete=True)[0]
        for i in range(3):
            if len(obj) == 1:
                if len(obj[0].Shape.Edges) > 1:
                    obj = Draft.downgrade(obj,delete=True)[0]


        for i in dobj:
            FreeCAD.ActiveDocument.removeObject(i.Name)


    FreeCAD.ActiveDocument.recompute()
    return(obj)


def errorDialog(msg): # message
    unicode_str =  unicode(msg,'utf-8')
    diag = QtGui.QMessageBox(QtGui.QMessageBox.Warning, 'Error MessageBox', unicode_str)
    diag.setWindowModality(QtCore.Qt.ApplicationModal)
    diag.exec_()


def findInterPoint(edge1,edge2): # give two edges and then return the inter_point
    pt1a = edge1.Vertex1.Point
    pt1b = edge1.Vertex2.Point
    pt2a = edge2.Vertex1.Point
    pt2b = edge2.Vertex2.Point
    nor1 = pt1a.sub(pt1b).normalize()
    nor2 = pt2a.sub(pt2b).normalize()
    line1 = Part.makeLine(pt1a+nor1*1000,pt1a+nor1*-1000)
    line2 = Part.makeLine(pt2a+nor2*1000,pt2a+nor2*-1000)
    p=DraftGeomUtils.findIntersection(line1,line2)
    if p: return(p[0])
    return(prf('cen not find the inter point!'))


def mkobj(shape):  # make obj
    obj = FreeCAD.ActiveDocument.addObject("Part::Feature",'Temp')
    obj.Shape = shape
    FreeCAD.ActiveDocument.recompute()
    return(obj)

def showup():
    global eeui,StaSel
    eeui = Ui_ee()
    FreeCADGui.Control.showDialog(eeui)
    StaSel = StandSelObserver()
    FreeCADGui.Selection.addObserver(StaSel)
    FreeCADGui.Selection.clearSelection()
    prf('trim start...')
   
#showup()
