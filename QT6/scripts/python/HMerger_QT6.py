from PySide6 import QtWidgets
import hou, os, glob, re

class HMerger (QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.resize(295, 193)

        main = QtWidgets.QVBoxLayout()
        pathLayout = QtWidgets.QHBoxLayout()
        btnLayout = QtWidgets.QHBoxLayout()

        self.ln_path = QtWidgets.QLineEdit()
        self.btn_B_file = QtWidgets.QToolButton()
        self.btn_B_file.setText('...')

        self.ch_conv = QtWidgets.QCheckBox('Convert to OBJ')
        self.ch_seq = QtWidgets.QCheckBox('Sequence')

        self.files_view = QtWidgets.QTreeWidget()
        self.files_view.setColumnCount(2)
        self.files_view.setHeaderLabels(['File','Path'])
        self.files_view.setIndentation(0)
        self.files_view.setItemsExpandable(0)
        self.files_view.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.btn_get = QtWidgets.QPushButton()
        self.btn_selAll = QtWidgets.QPushButton()
        self.btn_selCls = QtWidgets.QPushButton()
        server_env = hou.getenv('SERVER')
        if server_env:
            ptsrv = server_env + '/Houdini_pipeline/merger_Nodes'
        else:
            ptsrv = 'd:/test'
        self.ln_path.setText(ptsrv)
        pathLayout.addWidget(self.ln_path)
        pathLayout.addWidget(self.btn_B_file)

        main.addLayout(pathLayout)
        main.addWidget(self.ch_conv)
        main.addWidget(self.ch_seq)

        main.addWidget(self.files_view)
        main.addWidget(self.btn_selAll)
        main.addWidget(self.btn_selCls)
        main.addWidget(self.btn_get)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        main.addItem(spacerItem)
        self.setWindowTitle("Merger")
        self.btn_selAll.setText('Select ALL')
        self.btn_selCls.setText('Clear Selection')
        self.btn_get.setText('Merge')
        self.setLayout(main)
        self.setProperty("houdiniStyle", True)

        self.btn_B_file.clicked.connect(self.setPath)
        self.btn_get.clicked.connect(self.merge)
        self.btn_selAll.clicked.connect(self.selectAll)
        self.btn_selCls.clicked.connect(self.selectClear)

        self.ch_seq.clicked.connect(self.updateList)

        self.updateList()

    def selectAll(self):
        self.files_view.selectAll()
    def selectClear(self):
        self.files_view.clearSelection()

    def merge(self):
        self.btn_get.setText('WAIT...')
        items=self.files_view.selectedItems()
        self.files_view.clearSelection()
        self.files_view
        for item in items:
            path=os.path.normcase(item.text(1))+'\\'+item.text(0)
            nme=item.text(0)
            nme=re.sub('\$F\d','',nme)

            u=nme.split('.')
            u.reverse()
            if u[0]=='abc':
                arch=hou.node('/obj').createNode('alembicarchive', nme, run_init_scripts=True, load_contents=True, exact_type_name=False)
                arch.parm('fileName').set(self.convToHip(path))
                xform=arch.createNode('alembicxform', nme, run_init_scripts=True, load_contents=True, exact_type_name=False)
                xform.setInput(0, arch.indirectInputs()[0], 0)
                xform.parm('fileName').set(self.convToHip(path))
                geo=xform.createNode('geo', nme, run_init_scripts=False, load_contents=True, exact_type_name=False)
                geo.setInput(0, xform.indirectInputs()[0], 0)
                file=geo.createNode('alembic', nme, run_init_scripts=True, load_contents=True, exact_type_name=False)
                file.parm('fileName').set(self.convToHip(path))
                file.setName(nme+'_GEO')
                arch.moveToGoodPosition()
            else:
                nd=hou.node('/obj').createNode('geo', nme, run_init_scripts=True, load_contents=True, exact_type_name=False)
                file=nd.node('./file1')

                file.parm('file').set(self.convToHip(path))
                file.setName(nme+'_GEO')
                nd.moveToGoodPosition()

            if self.ch_conv.isChecked():  
                save=file.createOutputNode('rop_geometry')
                save.moveToGoodPosition()
                save.parm('sopoutput').set(self.convToHip(path)+'.obj')
                save.parm('execute').pressButton()

        self.updateList()
        self.btn_get.setText('Merge')
       
    def setPath(self):
        ospath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Path", self.ln_path.text())
        if ospath:
            self.ln_path.setText(ospath) 
        self.updateList()


    def defineSeq(self,files):
        cleanfiles=[]
        
        if len(files) < 2:
            return files

        cleanfiles.append(files[0])
        cleanfiles.append(files[1])

        for f in range(2,len(files),2):

            d1=re.findall('\d{1,8}',files[f])
            d1.reverse()
            
            if len(d1)!=0:
                if files[f].startswith(d1[0])==False:
                    seqLength=len(d1[0])

                    if abs(len(files[f])-len(files[f-2]))<=1:

                        d2=re.findall('\d{1,8}',files[f-2])
                        d2.reverse()

                        if len(d2)!=0:
                            if abs(int(d1[0])-int(d2[0]))==1:

                                name=files[f-2].replace(d2[0],'$F'+str(seqLength))

                                cleanfiles.pop()
                                cleanfiles.pop()
                                cleanfiles.append(name)
                                cleanfiles.append(files[f-1])
                                pass
                            else:
         
                                cleanfiles.append(files[f])
                                cleanfiles.append(files[f+1])

            else:
                cleanfiles.append(files[f])
                cleanfiles.append(files[f+1])

        return cleanfiles

    def updateList(self):      
        path=os.path.normcase(self.ln_path.text())
        fls= []
        pths= []
        ext = ['obj','bgeo','vdb','abc','fbx']
        self.files_view.clear()
        for dirpath, dirnames, files in os.walk(path):
            for name in files:
                for e in ext:
                    if name.lower().endswith(e):
                        fls.append(name)
                        fls.append(dirpath)
        
        if self.ch_seq.isChecked():
            fls=self.defineSeq(fls)

        for i in range(0,len(fls),2):
            QtWidgets.QTreeWidgetItem(self.files_view,[fls[i],fls[i+1]])
        self.files_view.resizeColumnToContents(0) 
        
    def convToHip(self, pth):
        pth=pth.replace('\\','/')
        pth=pth.replace(hou.getenv('HIP'),'$HIP')
        if hou.getenv('JOB'):
            if os.path.exists(hou.getenv('JOB')):
                pth=pth.replace(hou.getenv('JOB'),'$JOB')
        return pth
