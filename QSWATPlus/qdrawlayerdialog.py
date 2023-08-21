# -*- coding: utf-8 -*-

# QDraw: plugin that makes drawing easier
# Author: Jérémy Kalsron
#         jeremy.kalsron@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import QDialog, QComboBox, QLineEdit, QVBoxLayout, \
    QCheckBox, QDialogButtonBox, QLabel
from qgis.core import QgsProject , QgsVectorFileWriter, QgsVectorLayer, QgsLayerTreeGroup, QgsLayerTreeLayer
import os


class QDrawLayerDialog(QDialog):
    def __init__(self, iface, gtype):
        QDialog.__init__(self)

        self.setWindowTitle(self.tr('Drawing'))
        self.iface = iface
        self.name = QLineEdit()
        self.gtype = ''
        if gtype == 'point' or self.gtype == 'XYpoint':
            self.gtype = 'Point'
        elif gtype == 'line':
            self.gtype = 'LineString'
        else:
            self.gtype = 'Polygon'

        # change here by QgsMapLayerComboBox()
        self.layerBox = QComboBox()
        self.layers = []
        # for layer in QgsProject.instance().mapLayers().values():
        #     if layer.providerType() == "memory":
        #     #     # ligne suivante à remplacer par if layer.geometryType() == :
        #         if gtype in layer.dataProvider().dataSourceUri()[:26]: #  must be of the same type of the draw
        #             if 'field='+self.tr('Drawings')+':string(255,0)' in layer.dataProvider().dataSourceUri()[-28:]: # must have its first field named Drawings, string type
        # #
        #                 self.layers.append(layer)
        #                 self.layerBox.addItem(layer.name())
        #                 project = QgsProject.instance()
        #                 output_directory = project.homePath() + '/drshapes/'
        #                 os.makedirs(output_directory, exist_ok=True)
        #                 output_path = os.path.join(output_directory, layer.name())
        #
        #                 crs = project.crs()
        #                 # output_path = project.homePath()+'/drshapes/'+layer.name()
        #                 QgsVectorFileWriter.writeAsVectorFormat(layer, output_path, 'UTF-8', crs, driverName='ESRI Shapefile')
        #                 iface.addVectorLayer(output_path, 'SavedPolygon', 'ogr')

        # for add layer
        # self.addLayer = QCheckBox(self.tr('Add to an existing layer'))
        # self.addLayer.toggled.connect(self.addLayerChecked)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        # buttons.accepted.connect(self.run)
        buttons.rejected.connect(self.reject)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel(self.tr("Give a name to the feature:")))
        vbox.addWidget(self.name)
        # for add layer
        # vbox.addWidget(self.addLayer)
        # vbox.addWidget(self.layerBox)
        # if len(self.layers) == 0:
            # self.addLayer.setEnabled(False)
            # self.layerBox.setEnabled(False)
        vbox.addWidget(buttons)
        self.setLayout(vbox)

        self.layerBox.setEnabled(False)
        self.name.setFocus()

    def tr(self, message):
        return QCoreApplication.translate('Qdraw', message)

    def addLayerChecked(self):
        if self.addLayer.checkState() == Qt.Checked:
            self.layerBox.setEnabled(True)
        else:
            self.layerBox.setEnabled(False)

    def getName(self, iface, gtype):
        dialog = QDrawLayerDialog(iface, gtype)
        dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        result = dialog.exec_()
        return (
            dialog.name.text(),
            # for add layer
            # dialog.addLayer.checkState() == Qt.Checked,
            dialog.layerBox.currentIndex(),
            dialog.layers,
            result == QDialog.Accepted)

    # def run(self):
    #     project = QgsProject.instance()
    #     output_directory = project.homePath() + '/drshapes/'
    #     os.makedirs(output_directory, exist_ok=True)
    #     # layer = QgsVectorLayer(
    #     #     "Polygon?crs=" + self.iface.mapCanvas().mapSettings().destinationCrs().authid() + "&field=" + self.tr(
    #     #         'Drawings') + ":string(255)", self.name.displayText(), "memory")
    #     # output_path = os.path.join(output_directory, self.name.displayText())
    #
    #
    #     QgsVectorFileWriter.writeAsVectorFormat(layer, output_path, 'UTF-8', project.crs(), driverName='ESRI Shapefile')
    #
    #     self.iface.addVectorLayer(output_directory, self.name.displayText(), 'ogr')
    #
    #     # # Get the root layer tree
    #     # root = QgsProject.instance().layerTreeRoot()
    #     #
    #     # # Define the desired layer group name
    #     # group_name = 'Drawings'
    #     #
    #     # # Check if the layer group already exists
    #     # existing_group = root.findGroup(group_name)
    #     #
    #     # # If the layer group doesn't exist, create a new one
    #     # if existing_group is None:
    #     #     new_group = QgsLayerTreeGroup(group_name)
    #     #     # root.addGroup(new_group)
    #     #     root.insertChildNode(0, new_group)
    #     #     existing_group = new_group
    #     #
    #     # for child in root.children():
    #     #     if isinstance(child, QgsLayerTreeGroup) and child.name() == group_name:
    #     #         existing_group = child
    #     #         break
    #     #
    #     # # Create a new layer tree node for the shapefile layer
    #     # # layerShp = QgsVectorLayer(output_directory, self.name.displayText(), 'ogr')
    #     #
    #     # node = QgsLayerTreeLayer(layerShp)
    #     #
    #     # # Add the layer tree node to the layer group
    #     # existing_group.addChildNode(node)
    #     # layerShp.setVisible(True)
    #
    #     self.accept()
