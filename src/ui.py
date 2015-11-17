'''
Created on Oct 27, 2015

@author: qurban.ali
'''
parentWin = None
try:
    from uiContainer import uic
    import qtify_maya_window as qtfy
    parentWin = qtfy.getMayaWindow()
except:
    from PyQt4 import uic
from PyQt4.QtGui import QMessageBox, qApp
from PyQt4.QtCore import pyqtSignal
import os.path as osp
import qutil
import tactic_calls as tc
reload(tc)
import cui
import appUsageApp

rootPath = qutil.dirname(__file__, 2)
uiPath = osp.join(rootPath, 'ui')

projectKey = 'addAssetsProjectKey'
epKey = 'addAssetsEpKey'
contextKey = 'addAssetsContextKey'

Form, Base = uic.loadUiType(osp.join(uiPath, 'main.ui'))
class UI(Form, Base):
    def __init__(self, parent=parentWin, server=None):
        super(UI, self).__init__(parent)
        self.setupUi(self)

        self.parentWin = parent
        self.items = []
        self.title = 'Sequence Assets'
        
        self.progressBar.hide()
        self.setWindowTitle(self.title)
        self.setServer(server)
        self.populateProjects()
        
        self.projectBox.currentIndexChanged[str].connect(self.setProject)
        self.epBox.currentIndexChanged[str].connect(self.populateSequences)
        self.seqBox.currentIndexChanged[str].connect(self.populateAssets)
        self.addButton.clicked.connect(self.addAssets)
        self.contextBox.currentIndexChanged[str].connect(self.callPopulateAssets)
        self.selectAllButton.clicked.connect(self.selectAll)

        project = qutil.getOptionVar(projectKey)
        ep = qutil.getOptionVar(epKey)
        context = qutil.getOptionVar(contextKey)
        self.setContext(project, ep, None, context)
        
        appUsageApp.updateDatabase('addAssets')
        
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
        if pro:
            for i in range(self.projectBox.count()):
                if self.projectBox.itemText(i) == pro:
                    self.projectBox.setCurrentIndex(i)
                    break
        if ep:
            for i in range(self.epBox.count()):
                if self.epBox.itemText(i) == ep:
                    self.epBox.setCurrentIndex(i)
                    break
        if seq:
            for i in range(self.seqBox.count()):
                if self.seqBox.itemText(i) == seq:
                    self.seqBox.setCurrentIndex(i)
                    break
        if context:
            for i in range(self.contextBox.count()):
                if self.contextBox.itemText(i) == context:
                    self.contextBox.setCurrentIndex(i)
                    break
    
    def callPopulateAssets(self, context):
        self.populateAssets(self.seqBox.currentText(), context)
        qutil.addOptionVar(contextKey, context)
    
    def showMessage(self, **kwargs):
        return cui.showMessage(self, title=self.title, **kwargs)
        
    def setServer(self, server):
        errors = tc.setServer(server)
        if errors:
            self.showMessage(msg=errors.keys()[0], icon=QMessageBox.Critical,
                             details=errors.values()[0])
        
    def populateProjects(self):
        self.projectBox.clear()
        self.projectBox.addItem('--Select Project--')
        projects, errors = tc.getProjects()
        if errors:
            self.showMessage(msg='Error occurred while retrieving the list of projects from TACTIC',
                             icon=QMessageBox.Critical,
                             details=qutil.dictionaryToDetails(errors))
        if projects:
            self.projectBox.addItems(projects)
            
    def setProject(self, project):
        self.epBox.clear()
        qutil.addOptionVar(projectKey, project)
        self.epBox.addItem('--Select Episode--')
        if project != '--Select Project--':
            errors = tc.setProject(project)
            if errors:
                self.showMessage(msg='Error occurred while setting the project on TACTIC',
                                 icon=QMessageBox.Critical,
                                 details=qutil.dictionaryToDetails(errors))
            self.populateEpisodes()
    
    def populateEpisodes(self):
        episodes, errors = tc.getEpisodes()
        if errors:
            self.showMessage(msg='Error occurred while retrieving the Episodes',
                             icon=QMessageBox.Critical,
                             details=qutil.dictionaryToDetails(errors))
        self.epBox.addItems(episodes)
    
    def populateSequences(self, ep):
        self.seqBox.clear()
        self.seqBox.addItem('--Select Sequence--')
        qutil.addOptionVar(epKey, ep)
        if ep != '--Select Episode--':
            seqs, errors = tc.getSequences(ep)
            if errors:
                self.showMessage(msg='Error occurred while retrieving the Sequences',
                                 icon=QMessageBox.Critical,
                                 details=qutil.dictionaryToDetails(errors))
            self.seqBox.addItems(seqs)
    
    def populateAssets(self, seq, context=None):
        if not context: context = self.getContext()
        for item in self.items:
            item.deleteLater()
        del self.items[:]
        ep = self.epBox.currentText()
        if not ep or not seq: return
        if ep == '--Select Episode--' or seq == '--Select Sequence--': return
        assets, errors = tc.getAssets(ep, seq, context)
        if errors:
            self.showMessage(msg='Error occurred while retrieving the Assets',
                             icon=QMessageBox.Critical,
                             details=qutil.dictionaryToDetails(errors))
        for name, path in assets.items():
            item = Item(self, path=path, name=name)
            if item.getPath():
                item.setSelected(self.isSelectAll())
            self.itemsLayout.addWidget(item)
            self.items.append(item)
        map(lambda itm: itm.selectionChanged.connect(self.handleItemSelectionChange), self.items)
        
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