# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QSWATPlus
                                 A QGIS plugin
 Create SWATPlus inputs
                              -------------------
        begin                : 2014-07-18
        copyright            : (C) 2014 by Chris George
        email                : cgeorge@mcmaster.ca
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 
 ***************************************************************************
 Acknowledgement: this code was inspired by the Hillslopes module of the 
 WhiteBox toolset of John Lindsay: 
          http://www.uoguelph.ca/~hydrogeo/Whitebox/index.html
 ***************************************************************************
"""

from qgis.PyQt.QtCore import QObject, Qt, QSettings, QTranslator, QCoreApplication

from qgis.PyQt.QtGui import QIcon, QStandardItem, QColor
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QTableWidgetItem, QAbstractItemView,\
                                QAbstractButton, QTableWidget, QStyledItemDelegate,\
                                QPushButton, QMessageBox, QFileDialog

from qgis.core import QgsProject, QgsGeometry, QgsVectorLayer, QgsWkbTypes, QgsFillSymbol, QgsLayerTreeGroup

from qgis.gui import QgsMapToolEdit, QgsMapToolPan

from functools import partial

from .drawshapedialog import drawshapedialog
from .qdraw import Qdraw
import os.path
import random





class drawshape(QObject):

    def __init__(self, iface):
        super().__init__()
        """Constructor.
        
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # self.crsProject = crsProject
        self.dlg = drawshapedialog()
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'drawshape_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Draw Shape')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        self.digitizing_toolbar = None

        self.project = QgsProject.instance()
        self.output_directory = self.project.homePath() + '/drshapes/'
        self.icon_folder = 'resources'

        # self.resNumber = 1


    # def dock_to_right(self):
    #
    #
    #
    #     if self.dlg.isVisible():
    #         self.dlg.hide()
    #     else:
    #         self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dlg.dockWidget)
    #         # self.dlg.show()

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('drawshape', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/QSWATPlus3_9/QSWATPlus/resources/icon_DrawPtDMS.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Draw shape'),
            callback=self.run,
            parent=None)

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Draw Shape'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""

        # show the dialog
        # show the dialog
        self.dlg.show()

        # Connect the method to handle the category change event
        self.dlg.comboBox_selectcategory.currentIndexChanged.connect(self.handle_button_click)

        # Create Qdraw instance
        self.qdraw_instance = Qdraw(self.iface, 1, self.output_directory, self.project,self)

        # Connect the draw methods to the buttons with qdraw_instance
        self.dlg.dRectangleButton.clicked.connect(self.qdraw_instance.drawRect)
        self.dlg.dCircleButton.clicked.connect(self.qdraw_instance.drawCircle)
        self.dlg.dPolygonButton.clicked.connect(self.qdraw_instance.drawPolygon)

        self.dlg.toolButton_Refresh.clicked.connect(self.handle_refresh_click)
        self.dlg.toolButton_load.clicked.connect(self.handle_loadshape_click)

        # Set the selection behavior to select entire rows
        self.dlg.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.handle_refresh_click()

    def create_drawings_group(self):

        group_name = "Drawings"

        root = self.project.layerTreeRoot()

        group = root.findGroup(group_name)

        if group is None:
            group = root.insertGroup(0, group_name)

        return group, group_name



    def handle_button_click(self):

        text = self.dlg.comboBox_selectcategory.currentText()
        if text == 'Reservoir':
            self.dlg.Labletest.setText(text)
            resNumber = 1
        elif text == 'Ponds':
            self.dlg.Labletest.setText(text)
            resNumber = 2
        elif text == 'Wetland':
            self.dlg.Labletest.setText(text)
            resNumber = 3
        else:
            self.dlg.Labletest.setText(text)
            resNumber = 4

            # Update resNumber in Qdraw instance
        self.qdraw_instance.updateResNumber(resNumber)

        result = self.dlg.exec_()
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass


    def handle_refresh_click(self):

        group, group_name = self.create_drawings_group()

        if group and group.nodeType() == 0:
            # group = QgsProject.instance().layerTreeRoot().findGroup(group_name)

            # Clear existing data in the table widget
            self.dlg.tableWidget.setRowCount(0)

            # Get the list of layers within the layer group
            layers = [layer.layer() for layer in group.findLayers()]

            if layers:

                # Iterate over each layer and extract desired columns
                for layer in layers:
                    # Get the attribute table
                    fields = layer.fields()

                    # Filter desired columns based on their indices
                    desired_columns = [fields[i] for i in [0, 2, 3]]

                    # Start editing the layer
                    layer.startEditing()

                    # Iterate over features and populate the table widget
                    for feature in layer.getFeatures():
                        geometry = feature.geometry()
                        area = "%.3f" % (QgsGeometry.area(geometry))
                        centroid = feature.geometry().centroid().asPoint()

                        field_index = fields.indexFromName('Area')  # Index of the 'Area' field
                        attributes = feature.attributes()  # Get the existing attribute values
                        attributes[field_index] = area  # Update the attribute value

                        field_index = layer.fields().indexFromName('CentroidX')  # Index of the 'Area' field
                        attributes[field_index] = centroid.x()  # Update the attribute value

                        field_index = layer.fields().indexFromName('CentroidY')  # Index of the 'Area' field
                        attributes[field_index] = centroid.y()  # Update the attribute value

                        feature.setAttributes(attributes)  # Set the updated attributes to the feature
                        layer.updateFeature(feature)  # Save the changes to the shapefile

                        row = []
                        for column in desired_columns:
                            # Get the attribute value for each desired column
                            attr_value = feature.attribute(column.name())
                            row.append(str(attr_value))

                        # Add the row to the table widget
                        self.dlg.tableWidget.insertRow(self.dlg.tableWidget.rowCount())

                        for i, value in enumerate(row):
                            item = QTableWidgetItem(value)
                            self.dlg.tableWidget.setItem(self.dlg.tableWidget.rowCount()-1, i, item)

                            # Create the delete link for the fourth column
                            delete_link = QPushButton()
                            icon_filename_delete = 'icon_DrawTP.png'
                            icon_path_delete = os.path.join(os.path.dirname(__file__), self.icon_folder,
                                                            icon_filename_delete)
                            icon_delete = QIcon(icon_path_delete)
                            delete_link.setIcon(icon_delete)
                            delete_link.setProperty("row", self.dlg.tableWidget.rowCount() - 1)
                            delete_link.clicked.connect(partial(DeleteTableWidget.delete_row_confirmation,
                                                                delete_link, self.iface))
                            delete_link.setStyleSheet("QPushButton { color: blue; text-decoration: underline; }")
                            self.dlg.tableWidget.setCellWidget(self.dlg.tableWidget.rowCount() - 1, 3, delete_link)

                            # Create the modify link for the fifth column
                            modify_link = QPushButton()
                            icon_filename_modify = 'icon_DrawPt.png'
                            icon_path_modify = os.path.join(os.path.dirname(__file__), self.icon_folder, icon_filename_modify)
                            icon_modify = QIcon(icon_path_modify)
                            modify_link.setIcon(icon_modify)
                            modify_link.setProperty("row", self.dlg.tableWidget.rowCount() - 1)
                            modify_link.clicked.connect(partial(ModifyTableWidget.modify_row_confirmation,modify_link,
                                                                self.iface))
                            modify_link.setStyleSheet("QPushButton { color: blue; text-decoration: underline; }")
                            self.dlg.tableWidget.setCellWidget(self.dlg.tableWidget.rowCount() - 1, 4, modify_link)

                            # Create the move link for the sixth column
                            move_link = QPushButton()
                            icon_filename_move = 'icon_DrawPtXY.png'
                            icon_path_move = os.path.join(os.path.dirname(__file__), self.icon_folder, icon_filename_move)
                            icon_move = QIcon(icon_path_move)
                            move_link.setIcon(icon_move)
                            move_link.setProperty("row", self.dlg.tableWidget.rowCount() - 1)
                            move_link.clicked.connect(
                                partial(MoveTableWidget.move_row_confirmation, move_link, self.iface))
                            move_link.setStyleSheet("QPushButton { color: blue; text-decoration: underline; }")
                            self.dlg.tableWidget.setCellWidget(self.dlg.tableWidget.rowCount() - 1, 5, move_link)

                    # Commit the changes to the layer's attribute table
                    layer.commitChanges(stopEditing=True)
                    # self.iface.mapCanvas().setMapTool(QgsMapToolPan(self.iface.mapCanvas()))
            else:
                # self.iface.messageBar().pushMessage("Error", 'There are no layers in Drawing group', level=2,
                #                                     duration=5)
                pass

        else:
            self.iface.messageBar().pushMessage("Error", 'There is no Drawings group in the tree view', level=2,
                                                duration=5)

    def generate_random_color(self):
        return QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    def handle_loadshape_click(self):

        group, group_name = self.create_drawings_group()

        if group and group.nodeType() == 0:

            file_dialog = QFileDialog()
            file_dialog.setNameFilter("Shapefiles (*.shp)")
            file_dialog.setFileMode(QFileDialog.ExistingFiles)

            if file_dialog.exec_():
                file_paths = file_dialog.selectedFiles()

                for file_path in file_paths:
                    layer_name = os.path.splitext(os.path.basename(file_path))[0]
                    layer = QgsVectorLayer(file_path, layer_name, "ogr")

                    if layer.isValid():
                        if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                            if layer.featureCount() == 1:
                                # Generate a random color for the fill symbology
                                random_fill_color = self.generate_random_color()

                                # Create fill symbol
                                fill_symbol = QgsFillSymbol.defaultSymbol(layer.geometryType())
                                fill_symbol.setColor(random_fill_color)

                                # Apply the symbology to the layer
                                layer.renderer().setSymbol(fill_symbol)

                                treelayers = [layers.layer() for layers in group.findLayers()]

                                if treelayers:
                                    # Iterate over each layer and extract desired columns
                                    for layers in treelayers:
                                        if layers and layer.name() == layers.name():
                                            ok = False
                                            break
                                        else:
                                            ok = True
                                    if ok:
                                        self.project.addMapLayer(layer, False)
                                        group.insertLayer(0, layer)
                                        self.iface.layerTreeView().refreshLayerSymbology(layer.id())
                                        self.iface.setActiveLayer(layer)
                                        self.iface.mapCanvas().refresh()
                                    if not ok:
                                        self.iface.messageBar().pushMessage("Error",
                                                                            'The layer is already imported',
                                                                            level=2, duration=5)
                                elif not treelayers:
                                    self.project.addMapLayer(layer, False)
                                    group.insertLayer(0, layer)
                                    self.iface.layerTreeView().refreshLayerSymbology(layer.id())
                                    self.iface.setActiveLayer(layer)
                                    self.iface.mapCanvas().refresh()
                                else:
                                    self.iface.messageBar().pushMessage("Error",
                                                                        'Please make sure tha the Drawings group exists',
                                                                        level=2, duration=5)
                            else:
                                self.iface.messageBar().pushMessage("Error", 'There are more than 1 row (feature) in the shapefile',
                                                                    level=2,duration=5)
                        else:
                            self.iface.messageBar().pushMessage("Error",
                                                                'Only polygon shapefile is allowed to import',
                                                                level=2, duration=5)
        self.handle_refresh_click()


    def get_selected_row(self):
        selected_items = self.dlg.tableWidget.selectedItems()

        if selected_items:
            # Assuming that all selected items belong to the same row
            first_selected_item = selected_items[0]
            selected_row = first_selected_item.row()
            return selected_row
        else:
            return -1  # No row selected


class DeleteTableWidget(QTableWidget):

    def __init__(self, parent):
        super().__init__(parent)

    def delete_row_confirmation(self,iface):
        self.iface = iface
        button = self.sender()
        table_widget = button.parent()

        while not isinstance(table_widget, QTableWidget):
            table_widget = table_widget.parent()
        index = table_widget.currentIndex()
        if index.isValid():
            row = index.row()
            first_column_value = table_widget.item(row, 0).text()

            # the name of the polygon from first column of the table view
            shapename = first_column_value

            # confirmation dialog
            reply = QMessageBox.question(table_widget, "Delete Row", f"Are you sure you want to delete {shapename} row?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                table_widget.removeRow(row)

                # layer group name in tree view
                drawshapemethod = drawshape(self.iface)
                group, group_name = drawshapemethod.create_drawings_group()

                if group and group.nodeType() == 0:
                    # Get the list of layers within the layer group
                    layers = [layer.layer() for layer in group.findLayers()]

                    if layers:
                        canvas = self.iface.mapCanvas()

                        # Iterate over each layer and extract desired columns
                        for layer in layers:
                            if layer and layer.name() == shapename:

                                # Remove the layer from the QGIS map view
                                QgsProject.instance().removeMapLayer(layer.id())
                                canvas.refresh()

                                break  # Exit the loop after finding and removing the layers


class ModifyTableWidget(QTableWidget):

    def __init__(self, parent):
        super().__init__(parent)

    def modify_row_confirmation(self,iface):
        self.iface = iface
        button = self.sender()
        table_widget = button.parent()

        while not isinstance(table_widget, QTableWidget):
            table_widget = table_widget.parent()
        index = table_widget.currentIndex()
        if index.isValid():
            row = index.row()
            first_column_value = table_widget.item(row, 0).text()

            # the name of the polygon from first column of the table view
            shapename = first_column_value

            # layer group name in tree view
            drawshapemethod = drawshape(self.iface)
            group, group_name = drawshapemethod.create_drawings_group()

            if group and group.nodeType() == 0:
                # Get the list of layers within the layer group
                layers = [layer.layer() for layer in group.findLayers()]

                if layers:
                    # Iterate over each layer and extract desired columns
                    for layer in layers:
                        if layer and layer.name() == shapename:
                            # save previous changes

                            layer.commitChanges(stopEditing=True)
                            self.iface.setActiveLayer(layer)

                            # Set the map canvas extent to match the layer's extent
                            canvas = self.iface.mapCanvas()
                            canvas.setExtent(layer.extent())
                            canvas.refresh()

                            # Start editing the layer
                            if not layer.isEditable():
                                layer.startEditing()
                                # Activate the vertex editing tool
                                vertex_tool = QgsMapToolEdit(canvas)

                                # Activate the Vertex Tool
                                canvas.setMapTool(vertex_tool)
                                self.iface.actionVertexToolActiveLayer().trigger()

                                # Exit the loop after finding and activating the layer for editing
                                break


class MoveTableWidget(QTableWidget):

    def __init__(self, parent):
        super().__init__(parent)

    def move_row_confirmation(self,iface):
        self.iface = iface
        button = self.sender()
        table_widget = button.parent()

        while not isinstance(table_widget, QTableWidget):
            table_widget = table_widget.parent()
        index = table_widget.currentIndex()
        if index.isValid():
            row = index.row()
            first_column_value = table_widget.item(row, 0).text()

            # the name of the polygon from first column of the table view
            shapename = first_column_value

            # layer group name in tree view
            drawshapemethod = drawshape(self.iface)
            group, group_name = drawshapemethod.create_drawings_group()

            if group and group.nodeType() == 0:
                # Get the list of layers within the layer group
                layers = [layer.layer() for layer in group.findLayers()]

                if layers:
                    # Iterate over each layer and extract desired columns
                    for layer in layers:
                        if layer and layer.name() == shapename:
                            # save previous changes
                            layer.commitChanges(stopEditing=True)
                            self.iface.setActiveLayer(layer)

                            # Set the map canvas extent to match the layer's extent
                            canvas = self.iface.mapCanvas()
                            canvas.setExtent(layer.extent())
                            canvas.refresh()

                            # Start editing the layer
                            if not layer.isEditable():
                                layer.startEditing()
                                # Activate the vertex editing tool
                                vertex_tool = QgsMapToolEdit(canvas)

                                # Activate the Vertex Tool
                                canvas.setMapTool(vertex_tool)
                                self.iface.actionMoveFeature().trigger()

                                # Exit the loop after finding and activating the layer for editing
                                break