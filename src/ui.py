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
import os.path as osp
import qutil
import tactic_calls as tc
#reload(tc)
import cui

rootPath = qutil.dirname(__file__, 2)
uiPath = osp.join(rootPath, 'ui')

Form, Base = uic.loadUiType(osp.join(uiPath, 'main.ui'))
class UI(Form, Base):
    def __init__(self, parent=parentWin):
        super(UI, self).__init__(parent)
        self.setupUi(self)
        
        self.items = []
        self.title = 'Add Assets'
        
        self.progressBar.hide()
        self.setWindowTitle(self.title)
        self.setServer()
        self.populateProjects()
        
        self.projectBox.currentIndexChanged[str].connect(self.setProject)
        self.epBox.currentIndexChanged[str].connect(self.populateSequences)
        self.seqBox.currentIndexChanged[str].connect(self.populateAssets)
        self.addButton.clicked.connect(self.addAssets)
        self.contextBox.currentIndexChanged[str].connect(self.callPopulateAssets)
    
    def callPopulateAssets(self, context):
        self.populateAssets(self.seqBox.currentText(), context)
    
    def showMessage(self, **kwargs):
        return cui.showMessage(self, title=self.title, **kwargs)
        
    def setServer(self):
        errors = tc.setServer()
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
        for asset in assets:
            item = Item(self, asset)
            self.itemsLayout.addWidget(item)
            self.items.append(item)
            
    def getContext(self):
        return self.contextBox.currentText()
            
    
    def addAssets(self):
        try:
            self.progressBar.setMaximum(len(self.items))
            self.progressBar.show( )
            for i, item in enumerate(self.items):
                if item.isSelected():
                    path, num = item.getNameNum()
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
    def __init__(self, parent=None, name='', num=1):
        super(Item, self).__init__(parent)
        self.setupUi(self)
        self.num = num
        self.name = name
        
        self.populate()
        
        self.numBox.valueChanged[int].connect(self.setNum)
        
    def setName(self, name):
        self.name = name
        self.assetButton.setText(osp.basename(osp.splitext(self.name)[0]))
    
    def setNum(self, num):
        self.numBox.setValue(num)
        self.num = num
        
    def populate(self):
        self.setName(self.name)
        self.numBox.setValue(self.num)
        
    def isSelected(self):
        return self.assetButton.isChecked()
    
    def getName(self):
        return self.name
    
    def getNum(self):
        return self.num
        
    def getNameNum(self):
        return self.name, self.num