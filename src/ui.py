'''
Created on Oct 27, 2015

@author: qurban.ali
'''
from uiContainer import uic
import qtify_maya_window as qtfy
from PyQt4.QtGui import QMessageBox, qApp
from PyQt4.QtCore import pyqtSignal, Qt
import os.path as osp
import qutil
import tacticCalls as tc
import cui
import appUsageApp
import imaya

reload(tc)
reload(cui)

rootPath = qutil.dirname(__file__, 2)
uiPath = osp.join(rootPath, 'ui')

contextKey = 'addAssetsContextKey'

Form, Base = uic.loadUiType(osp.join(uiPath, 'main.ui'))
class UI(Form, Base, cui.TacticUiBase):
    def __init__(self, parent=qtfy.getMayaWindow()):
        super(UI, self).__init__(parent)
        self.setupUi(self)

        self.parentWin = parent
        self.items = []
        self.title = 'Sequence Assets'
        self.projectKey = 'addAssetsProjectKey'
        self.epKey = 'addAssetsEpKey'
        
        self.setServer()
        self.setStyleSheet(cui.styleSheet)
        self.progressBar.hide()
        self.setWindowTitle(self.title)
        self.populateProjects()
        
        self.projectBox.currentIndexChanged[str].connect(self.setProject)
        self.epBox.currentIndexChanged[str].connect(self.populateSequences)
        
        self.seqBox = cui.MultiSelectComboBox(self, '--Sequence--')
        self.seqBox.setStyleSheet('QPushButton{min-width: 100px;}')
        self.layout.insertWidget(2, self.seqBox)
        self.seqBox.selectionDone.connect(self.populateAssets)
        
        self.addButton.clicked.connect(self.addAssets)
        self.contextBox.currentIndexChanged[str].connect(self.callPopulateAssets)
        self.selectAllButton.clicked.connect(self.selectAll)

        project = qutil.getOptionVar(tc.projectKey)
        ep = qutil.getOptionVar(tc.episodeKey)
        context = qutil.getOptionVar(contextKey)
        self.setContext(project, ep, None, context)
        
        appUsageApp.updateDatabase('addAssets')
        
    def setBusy(self):
        qApp.setOverrideCursor(Qt.WaitCursor)
        qApp.processEvents()
        
    def releaseBusy(self):
        qApp.restoreOverrideCursor()
        
    def populateSequences(self, ep):
        imaya.addOptionVar(tc.episodeKey, ep)
        self.setBusy()
        try:
            self.seqBox.clearItems()
            if ep != '--Select Episode--':
                seqs, errors = tc.getSequences(ep)
                if errors:
                    self.showMessage(msg='Error occurred while retrieving the Sequences',
                                     icon=QMessageBox.Critical,
                                     details=qutil.dictionaryToDetails(errors))
                self.seqBox.addItems(seqs)
        except Exception as ex:
            self.releaseBusy()
            self.showMessage(msg=str(ex), icon=QMessageBox.Critical)
        finally:
            self.releaseBusy()
        
    def getSelectedAssets(self):
        items = {}
        for item in self.items:
            if item.isSelected():
                items[item.getName()] = [item.getNum(), item.getPath()]
        return items
        
    def closeEvent(self, event):
        try:
            self.parentWin.closeEventAssetsWindow()
        except:
            pass
        
    def isSelectAll(self):
        return self.selectAllButton.isChecked()
        
    def selectAll(self):
        for item in self.items:
            if item.getPath():
                item.setSelected(self.isSelectAll())
        
    def setContext(self, pro, ep, seq, context):
        super(UI, self).setContext(pro, ep, seq)
        if context:
            for i in range(self.contextBox.count()):
                if self.contextBox.itemText(i) == context:
                    self.contextBox.setCurrentIndex(i)
                    break
    
    def callPopulateAssets(self, context):
        self.populateAssets(self.seqBox.getSelectedItems(), context)
        qutil.addOptionVar(contextKey, context)
    
    def showMessage(self, **kwargs):
        return cui.showMessage(self, title=self.title, **kwargs)
    
    def populateAssets(self, seq, context=None):
        try:
            self.setBusy()
            if not context: context = self.getContext()
            for item in self.items:
                item.deleteLater()
            del self.items[:]
            ep = self.epBox.currentText()
            if not ep or not seq: self.releaseBusy(); return
            if ep == '--Select Episode--': self.releaseBusy(); return
            assets, assets_count, errors = tc.getAssets(ep, seq, context)
            if errors:
                self.showMessage(msg='Error occurred while retrieving the Assets',
                                 icon=QMessageBox.Critical,
                                 details=qutil.dictionaryToDetails(errors))
            for name in sorted(assets.keys()):
                try:
                    num = assets_count[name]
                except KeyError:
                    num = 1
                if num < 1: num = 1
                item = Item(self, path=assets[name], num=num, name=name)
                if item.getPath():
                    item.setSelected(self.isSelectAll())
                self.itemsLayout.addWidget(item)
                self.items.append(item)
            map(lambda itm: itm.selectionChanged.connect(self.handleItemSelectionChange), self.items)
        except Exception as ex:
            self.releaseBusy()
            self.showMessage(msg=str(ex), icon=QMessageBox.Critical)
        finally:
            self.releaseBusy()
        
    def handleItemSelectionChange(self, val):
        flag = True
        for item in self.items:
            if not item.isSelected():
                flag = False
                break
        self.selectAllButton.setChecked(flag)
            
    def getContext(self):
        return self.contextBox.currentText()
            
    
    def addAssets(self):
        try:
            self.progressBar.setMaximum(len(self.items))
            self.progressBar.show()
            for i, item in enumerate(self.items):
                if item.isSelected():
                    path, num = item.getPathNum()
                    for _ in range(num):
                        qutil.addRef(path)
                self.progressBar.setValue(i+1)
                qApp.processEvents()
        except Exception as ex:
            self.showMessage(msg=str(ex), icon=QMessageBox.Critical)
        finally:
            self.progressBar.hide()
            self.progressBar.setMaximum(0)
            self.progressBar.setValue(0)
        

Form1, Base1 = uic.loadUiType(osp.join(uiPath, 'item.ui'))
class Item(Form1, Base1):
    selectionChanged = pyqtSignal(bool)
    def __init__(self, parent=None, path='', num=1, name=''):
        super(Item, self).__init__(parent)
        self.setupUi(self)
        self.num = num
        self.path = path
        self.name = name
        
        self.populate()
        
        self.numBox.valueChanged[int].connect(self.setNum)
        self.assetButton.clicked.connect(lambda: self.selectionChanged.emit(self.isSelected()))
        
    def setName(self, path):
        self.path = path
        if path is None:
            self.setEnabled(False)
            self.setSelected(False)
            self.assetButton.setText(self.name)
            return
        self.assetButton.setText(osp.basename(osp.splitext(self.path)[0]))
    
    def setNum(self, num):
        self.numBox.setValue(num)
        self.num = num
        
    def setAssetName(self, name):
        self.name = name

    def populate(self):
        self.setName(self.path)
        self.numBox.setValue(self.num)
        
    def isSelected(self):
        return self.assetButton.isChecked()
    
    def setSelected(self, selected):
        self.assetButton.setChecked(selected)
        
    def getName(self):
        return self.name
    
    def getPath(self):
        return self.path
    
    def getNum(self):
        return self.num
        
    def getPathNum(self):
        return self.path, self.num