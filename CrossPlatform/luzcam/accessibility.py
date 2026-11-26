"""Accessible controls for the shared scaled QWidget scene.

Keep the existing widgets/actions and map their rectangles through the same
scene transform as the visible interface. No second UI or native dependency.
"""
import weakref
import shiboken6
from PySide6.QtCore import QPoint,QRect,QRectF,Qt
from PySide6.QtGui import QAccessible,QAccessibleValueInterface,QAccessibleActionInterface,QAccessibleSelectionInterface
from PySide6.QtWidgets import (QWidget,QAccessibleWidget,QAbstractButton,QCheckBox,
    QAbstractSlider,QComboBox,QLabel,QStackedWidget)
from .i18n import text as translate

_instances={}
_installed=False

def _context(widget):
    current=widget
    while isinstance(current,QWidget):
        ref=getattr(current,'_luzcam_accessible_view',None)
        if ref is not None:
            view=ref()
            if view is not None and shiboken6.isValid(view):return current,view
        current=current.parentWidget()
    return None,None

def mapped_rect(widget,root,view,local_rect=None):
    top=widget.window();proxy=top.graphicsProxyWidget()
    if proxy is None:
        top=root;proxy=root.graphicsProxyWidget()
    point=widget.mapTo(top,QPoint())
    area=QRectF(widget.rect() if local_rect is None else local_rect)
    area.translate(point)
    scene=proxy.mapRectToScene(area)
    local=view.viewportTransform().mapRect(scene).toAlignedRect()
    return QRect(view.viewport().mapToGlobal(local.topLeft()),local.size())

class _SliderValue(QAccessibleValueInterface):
    def __init__(self,widget):super().__init__();self.ref=weakref.ref(widget)
    def currentValue(self):return self.ref().value()
    def minimumValue(self):return self.ref().minimum()
    def maximumValue(self):return self.ref().maximum()
    def minimumStepSize(self):return self.ref().singleStep()
    def setCurrentValue(self,value):
        widget=self.ref()
        if widget is not None and shiboken6.isValid(widget) and widget.isEnabled():widget.setValue(int(value))

class _Control(QAccessibleWidget):
    def __init__(self,widget,root,view):
        role=QAccessible.Client
        if isinstance(widget,QCheckBox):role=QAccessible.CheckBox
        elif isinstance(widget,QAbstractButton):role=QAccessible.Button
        elif isinstance(widget,QAbstractSlider):role=QAccessible.ScrollBar if widget.inherits('QScrollBar') else QAccessible.Slider
        elif isinstance(widget,QComboBox):role=QAccessible.ComboBox
        elif isinstance(widget,QLabel):role=QAccessible.StaticText
        elif isinstance(widget,QStackedWidget):role=QAccessible.LayeredPane
        super().__init__(widget,role);self.root_ref=weakref.ref(root);self.view_ref=weakref.ref(view)
        self.value_proxy=_SliderValue(widget) if isinstance(widget,QAbstractSlider) else None
    def interface_cast(self,kind):
        if kind==QAccessible.ValueInterface and self.value_proxy is not None:
            # void* must be a Shiboken VoidPtr, not an integer/Python object.
            return shiboken6.VoidPtr(shiboken6.getCppPointer(self.value_proxy)[0])
        return super().interface_cast(kind)
    def window(self):
        view=self.view_ref()
        return view.window().windowHandle() if view is not None and shiboken6.isValid(view) else None
    def parent(self):
        if self.widget() is self.root_ref():return QAccessible.queryAccessibleInterface(self.view_ref())
        return super().parent()
    def rect(self):
        widget=self.widget();view=self.view_ref();root=self.root_ref()
        if not widget or not view or not root:return QRect()
        return mapped_rect(widget,root,view)
    def childCount(self):
        if isinstance(self.widget(),(QAbstractButton,QAbstractSlider,QLabel)):return 0
        return super().childCount()
    def child(self,index):
        if isinstance(self.widget(),(QAbstractButton,QAbstractSlider,QLabel)):return None
        return super().child(index)
    def text(self,kind):
        widget=self.widget()
        if kind==QAccessible.Name:
            name=widget.accessibleName()
            if not name and isinstance(widget,(QLabel,QAbstractButton)):name=widget.text()
            if not name and isinstance(widget,QComboBox):name=translate('Idioma')
            name=translate(name) if name else super().text(kind)
            if isinstance(widget,QAbstractSlider) and widget.property('luzcamValueText'):
                name+=' · '+str(widget.property('luzcamValueText'))
            return name
        if kind==QAccessible.Description:
            return translate(widget.accessibleDescription() or widget.toolTip())
        if kind==QAccessible.Value:
            if isinstance(widget,QComboBox):return widget.currentText()
            if isinstance(widget,QAbstractSlider):return str(widget.property('luzcamValueText') or widget.value())
        return super().text(kind)
    def state(self):
        state=super().state();widget=self.widget();view=self.view_ref()
        state.focusable=widget.focusPolicy()!=Qt.NoFocus;state.focused=widget.hasFocus()
        state.invisible=state.invisible or not widget.isVisible() or not view.isVisible()
        viewport=QRect(view.viewport().mapToGlobal(QPoint()),view.viewport().size())
        state.offscreen=state.offscreen or state.invisible or view.window().isMinimized() or not self.rect().intersects(viewport)
        if isinstance(widget,QAbstractButton):
            state.checkable=widget.isCheckable();state.checked=widget.isChecked();state.pressed=widget.isDown()
        if isinstance(widget,QComboBox):
            state.hasPopup=True;state.expandable=True;state.expanded=widget.view().isVisible();state.collapsed=not state.expanded
        return state
    def actionNames(self):
        widget=self.widget();names=[]
        if widget.focusPolicy()!=Qt.NoFocus:names.append(QAccessibleActionInterface.setFocusAction())
        if isinstance(widget,QAbstractButton):names.append(QAccessibleActionInterface.pressAction())
        if isinstance(widget,QComboBox):names.append(QAccessibleActionInterface.showMenuAction())
        if isinstance(widget,QAbstractSlider):names.extend((QAccessibleActionInterface.increaseAction(),QAccessibleActionInterface.decreaseAction()))
        return names
    def doAction(self,name):
        widget=self.widget()
        if not widget.isEnabled():return
        if name==QAccessibleActionInterface.setFocusAction():widget.setFocus(Qt.OtherFocusReason)
        elif name==QAccessibleActionInterface.pressAction() and isinstance(widget,QAbstractButton):widget.click()
        elif name==QAccessibleActionInterface.showMenuAction() and isinstance(widget,QComboBox):widget.showPopup()
        elif isinstance(widget,QAbstractSlider):
            if name==QAccessibleActionInterface.increaseAction():widget.setValue(widget.value()+widget.singleStep())
            elif name==QAccessibleActionInterface.decreaseAction():widget.setValue(widget.value()-widget.singleStep())
    def keyBindingsForAction(self,name):
        widget=self.widget()
        if name==QAccessibleActionInterface.pressAction() and isinstance(widget,QAbstractButton) and not widget.shortcut().isEmpty():return [widget.shortcut().toString()]
        return []

class _SceneView(QAccessibleWidget):
    def __init__(self,view):super().__init__(view,QAccessible.Client);self.view_ref=weakref.ref(view)
    def childCount(self):return 1
    def child(self,index):
        return QAccessible.queryAccessibleInterface(self.view_ref()._luzcam_accessible_root) if index==0 else None
    def indexOfChild(self,child):return 0 if child and child.object() is self.view_ref()._luzcam_accessible_root else -1
    def childAt(self,x,y):
        root=self.child(0)
        return root.childAt(x,y) or root if root and root.rect().contains(x,y) else None
    def focusChild(self):
        root=self.child(0)
        return root.focusChild() if root else None

class _ListItem(QAccessibleWidget):
    def __init__(self,owner,index):
        super().__init__(owner.widget(),QAccessible.ListItem);self.owner_ref=weakref.ref(owner);self.index=index
    def object(self):return None  # Virtual row, not another interface for the list QWidget.
    def parent(self):return self.owner_ref()
    def childCount(self):return 0
    def child(self,index):return None
    def window(self):return self.owner_ref().window()
    def rect(self):
        owner=self.owner_ref();widget=owner.widget()
        area=widget.visualRect(widget.model().index(self.index,0)).intersected(widget.viewport().rect())
        return mapped_rect(widget.viewport(),owner.root_ref(),owner.view_ref(),area)
    def text(self,kind):
        return self.owner_ref().combo_ref().itemText(self.index) if kind==QAccessible.Name else ''
    def state(self):
        state=QAccessible.State();owner=self.owner_ref();widget=owner.widget()
        state.selectable=True;state.focusable=True;state.selected=owner.combo_ref().currentIndex()==self.index
        state.focused=widget.hasFocus() and widget.currentIndex().row()==self.index
        state.invisible=not widget.isVisible();state.offscreen=state.invisible;state.disabled=not owner.combo_ref().isEnabled()
        return state
    def actionNames(self):return [QAccessibleActionInterface.pressAction(),QAccessibleActionInterface.setFocusAction()]
    def doAction(self,name):
        owner=self.owner_ref()
        if name==QAccessibleActionInterface.pressAction():owner.choose(self.index)
        elif name==QAccessibleActionInterface.setFocusAction():
            owner.widget().setCurrentIndex(owner.widget().model().index(self.index,0));owner.widget().setFocus(Qt.OtherFocusReason)
    def keyBindingsForAction(self,name):return []

class _ListSelection(QAccessibleSelectionInterface):
    def __init__(self,owner):super().__init__();self.ref=weakref.ref(owner)
    def selectedItemCount(self):return int(self.ref().combo_ref().currentIndex()>=0)
    def selectedItem(self,index):return self.ref().child(self.ref().combo_ref().currentIndex()) if index==0 else None
    def isSelected(self,child):return self.ref().indexOfChild(child)==self.ref().combo_ref().currentIndex()
    def select(self,child):return self.ref().choose(self.ref().indexOfChild(child))
    def unselect(self,child):return False  # Language must retain one choice.
    def clear(self):return False
    def selectAll(self):return self.ref().choose(0) if self.ref().childCount()==1 else False

class _ComboList(_Control):
    def __init__(self,widget,root,view,combo):
        super().__init__(widget,root,view);self.combo_ref=weakref.ref(combo);self.items={};self.selection_proxy=_ListSelection(self)
        widget.destroyed.connect(self.dispose_items)
    def role(self):return QAccessible.List
    def interface_cast(self,kind):
        if kind==QAccessible.SelectionInterface:return shiboken6.VoidPtr(shiboken6.getCppPointer(self.selection_proxy)[0])
        return super().interface_cast(kind)
    def text(self,kind):return translate('Idioma') if kind==QAccessible.Name else super().text(kind)
    def childCount(self):return self.combo_ref().count()
    def child(self,index):
        if not 0<=index<self.childCount():return None
        if index not in self.items:self.items[index]=_ListItem(self,index)
        return self.items[index]
    def indexOfChild(self,child):return child.index if isinstance(child,_ListItem) and child.owner_ref() is self else -1
    def childAt(self,x,y):
        return next((self.child(i) for i in range(self.childCount()) if self.child(i).rect().contains(x,y)),None)
    def choose(self,index):
        combo=self.combo_ref()
        if not combo.isEnabled() or not 0<=index<combo.count():return False
        combo.setCurrentIndex(index);combo.hidePopup();return True
    def dispose_items(self,*args):
        for item in self.items.values():
            if shiboken6.isValid(item):QAccessible.deleteAccessibleInterface(QAccessible.uniqueId(item))
        self.items.clear()

def _factory(class_name,widget):
    if not isinstance(widget,QWidget):return None
    if hasattr(widget,'_luzcam_accessible_root'):interface=_SceneView(widget)
    else:
        root,view=_context(widget)
        if root is None:return None
        if widget.inherits('QAbstractItemView'):
            parent=widget.parentWidget()
            while parent is not None and not isinstance(parent,QComboBox):parent=parent.parentWidget()
            if parent is None:return None
            interface=_ComboList(widget,root,view,parent)
        elif widget.inherits('QComboBoxPrivateContainer'):return None
        else:interface=_Control(widget,root,view)
    key=id(widget);_instances[key]=interface
    widget.destroyed.connect(lambda *_,key=key:_instances.pop(key,None))
    return interface

def bind_scene(view,root):
    global _installed
    if not _installed:QAccessible.installFactory(_factory);_installed=True
    # Scene insertion may have created default interfaces before the view
    # existed. Recreate only this hidden scene's initial cache entries.
    existing=[]
    for widget in [view,root,*root.findChildren(QWidget)]:
        interface=QAccessible.queryAccessibleInterface(widget)
        if interface:existing.append(QAccessible.uniqueId(interface))
    view._luzcam_accessible_root=root;root._luzcam_accessible_view=weakref.ref(view)
    for key in set(existing):QAccessible.deleteAccessibleInterface(key)
