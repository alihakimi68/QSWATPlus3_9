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

from qgis.PyQt.QtCore import QObject, Qt
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QToolBar, QVBoxLayout, QTableWidgetItem, \
                                QAbstractItemView, QAbstractButton, QTableWidget, QStyledItemDelegate,\
                                QPushButton, QMessageBox, QTableView

from qgis.PyQt.QtWidgets import QApplication, QStyleOptionViewItem, QStyledItemDelegate

from qgis.core import QgsProject, QgsVectorLayer, QgsGeometry

from functools import partial

from .drawshapedialog import drawshapedialog
from .qdraw import Qdraw
import os.path





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



    # noinspection PyMethodMayBeStatic
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

        icon_path = ':/plugins/drawshape/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Draw shape'),
            callback=self.run,
            parent=None)
            # parent = self.iface.mainWindow())

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
        self.dlg.show()

        self.dlg.cShapeButton.setCheckable(True)
        # self.dlg.cShapeButton.toggle()
        self.dlg.groupBox_selectcategory.setEnabled(True)
        self.dlg.groupBox_drawpolygon.setEnabled(False)

        self.dlg.cShapeButton.clicked.connect(self.handle_button_click)

        self.dlg.toolButton_Refresh.clicked.connect(self.handle_refresh_click)

        # Set the selection behavior to select entire rows
        self.dlg.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        # self.disable_table_editing()



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

        if self.dlg.cShapeButton.isChecked():

            self.dlg.groupBox_selectcategory.setEnabled(False)
            self.dlg.groupBox_drawpolygon.setEnabled(True)
            self.dlg.cShapeButton.setText('Select Category / Draw : Draw')

            # self.iface.messageBar().pushMessage("Error", str(resNumber), level=2, duration=5)
            qdraw_instance = Qdraw(self.iface, resNumber,self.output_directory,self.project)
            self.dlg.dRectangleButton.clicked.connect(qdraw_instance.drawRect)
            self.dlg.dCircleButton.clicked.connect(qdraw_instance.drawCircle)
            self.dlg.dPolygonButton.clicked.connect(qdraw_instance.drawPolygon)

            result = self.dlg.exec_()
            if result:
                # Do something useful here - delete the line containing pass and
                # substitute with your code.
                pass


        elif not self.dlg.cShapeButton.isChecked():
            self.dlg.groupBox_selectcategory.setEnabled(True)
            self.dlg.groupBox_drawpolygon.setEnabled(False)
            self.dlg.cShapeButton.setText('Select Category / Draw : Select Catergory')
            # self.iface.messageBar().pushMessage("Error", 'not checked', level=2, duration=5)
        else:
            self.iface.messageBar().pushMessage("Error", 'This is not right', level=2, duration=5)

    def handle_refresh_click(self):
        # Assuming you have a reference to the layer group
        group_name = "Drawings"

        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(group_name)
        if group and group.nodeType() == 0:
            group = QgsProject.instance().layerTreeRoot().findGroup(group_name)

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
                        area = QgsGeometry.area(geometry)
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
                            delete_link = QPushButton("Delete")
                            delete_link.setProperty("row", self.dlg.tableWidget.rowCount() - 1)
                            delete_link.clicked.connect(partial(MyTableWidget.delete_row_confirmation, delete_link))
                            delete_link.setStyleSheet("QPushButton { color: blue; text-decoration: underline; }")
                            self.dlg.tableWidget.setCellWidget(self.dlg.tableWidget.rowCount() - 1, 3, delete_link)

                    # Commit the changes to the layer's attribute table
                    layer.commitChanges(stopEditing=True)
            else:
                self.iface.messageBar().pushMessage("Error", 'There are no layers in Drawing group', level=2,
                                                    duration=5)

        else:
            self.iface.messageBar().pushMessage("Error", 'There is no Drawing group', level=2,
                                                duration=5)

    def get_selected_row(self):
        selected_items = self.dlg.tableWidget.selectedItems()

        if selected_items:
            # Assuming that all selected items belong to the same row
            first_selected_item = selected_items[0]
            selected_row = first_selected_item.row()
            return selected_row
        else:
            return -1  # No row selected

    # Disable editing for all cells in a QTableWidget
    # def disable_table_editing(self):
    #     rows = self.dlg.tableWidget.rowCount()
    #     cols = self.dlg.tableWidget.columnCount()
    #
    #     for row in range(rows):
    #         for col in range(cols):
    #             item = self.dlg.tableWidget.item(row, col)
    #             if item is not None:
    #                 item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    #             else:
    #                 self.dlg.tableWidget.setItem(row, col, QTableWidgetItem())
    #                 self.dlg.tableWidget.item(row, col).setFlags(
    #                     self.dlg.tableWidget.item(row, col).flags() & ~Qt.ItemIsEditable
    #                 )


class DeleteLinkDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)

    def paint(self, painter, option, index):
        if index.column() == 3:
            button = QAbstractButton(index.data(), self.parent())
            button.setGeometry(option.rect)
            button.clicked.connect(self.parent().delete_row_confirmation)
            button.setAutoFillBackground(True)
            button.setStyleSheet("QPushButton { color: blue; text-decoration: underline; }")

        super().paint(painter, option, index)


class MyTableWidget(QTableWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setItemDelegate(DeleteLinkDelegate(self))

    def delete_row_confirmation(self):
        button = self.sender()
        table_widget = button.parent()
        while not isinstance(table_widget, QTableWidget):
            table_widget = table_widget.parent()
        index = table_widget.currentIndex()
        if index.isValid():
            row = index.row()
            reply = QMessageBox.question(table_widget, "Delete Row", "Are you sure you want to delete this row?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                table_widget.removeRow(row)

