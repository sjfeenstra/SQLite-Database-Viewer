import sys
from PySide6.QtWidgets import QApplication, QWidget, QTableView, QAbstractItemView, QHeaderView, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QLabel, QListView
from PySide6.QtCore import QRegularExpression, Qt, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem
import sqlite3 as db
import configparser
import qdarktheme
from SortFilterProxyModel import SortFilterProxyModel
from DataEditWindow import DataEditWindow


class SQLiteDatabaseViewer(QWidget):
    """SQLite Database Viewer widget."""
    closed = Signal()
    config = configparser.ConfigParser()
    config.read('app.ini')
    db_location = config.get('Database', 'db_location')

    def __init__(self, parent=None):
        super(SQLiteDatabaseViewer, self).__init__(parent)
        self.setWindowTitle("SQLite Database Viewer")
        self.initialize_database_connection()
        self.closed.connect(self.close_db_connection)

        self.get_table_config_data()

        self.create_gui_layout()
        self.fill_table_view(self.table_name)

    def get_table_config_data(self):
        """get the database table configuration data."""
        try:
            self.column_headers = [item[0] for item in self.cursor.execute("SELECT * FROM {} LIMIT 1".format(self.table_name)).description]
            self.row_count = self.cursor.execute("SELECT COUNT(*) FROM {}".format(self.table_name)).fetchone()[0]
            self.column_count = len(self.column_headers)
        except db.Error as error:
            print('Error occurred - ', error)    

    def initialize_database_connection(self):
        """Initialize the SQLite database connection."""
        try:
            self.conn = db.connect(self.db_location)
            self.cursor = self.conn.cursor()
            self.tables = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
            self.table_name = self.tables[0][0]
        except db.Error as error:
            print('Error occurred - ', error)    

    def create_gui_layout(self):
        """Create the GUI layout."""
        layout = QHBoxLayout()
        self.sidebar = QVBoxLayout()
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        self.filter_layout = QHBoxLayout()
        self.table_layout = QHBoxLayout()

        layout.addLayout(self.sidebar)
        layout.addLayout(main_layout)
        main_layout.addLayout(self.filter_layout)
        main_layout.addLayout(self.table_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(layout)

        self.create_table_view()
        self.table_layout.addWidget(self.table_view)
        self.create_sidebar()

        insert_button = QPushButton("Insert data into table")
        insert_button.setStyleSheet("QPushButton { font-size: 15px; color: black; }")
        button_layout.addWidget(insert_button)
        insert_button.clicked.connect(self.open_insert_window)
        self.create_filters()

    def create_sidebar(self):
        """Create the Sidebar."""
        tables_list_label = QLabel("Tables")
        tables_list_label.setStyleSheet("QLabel { font-size: 25px;}")
        tables_list_label.setAlignment(Qt.AlignCenter)
        self.tables_list_view =  QListView()
        self.sidebar.addWidget(tables_list_label)
        self.sidebar.addWidget(self.tables_list_view)
        self.tables_list_view.setFixedWidth(100)

        tables_model = QStandardItemModel()
        self.tables_list_view.setModel(tables_model)
        self.tables_list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tables_list_view.doubleClicked.connect(self.change_table_and_filters)
        self.tables_list_view.setStyleSheet("QListView::item { height: 30px; }")
        for table in self.tables:
            item = QStandardItem(table[0])
            tables_model.appendRow(item)

    def clear_layout(self, layout):
        """Clear the specific layout."""
        while layout.count():
            item = layout.takeAt( 0)
            if item.widget():
                item.widget().deleteLater()

    def create_filters(self):
        """Create the table filters."""
        for i in range(self.column_count):
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(self.column_headers[i])
            self.filter_layout.addWidget(line_edit)
            line_edit.textChanged.connect(lambda text, col=i:
                       self.proxy_model.setFilterByColumn(QRegularExpression(text, QRegularExpression.PatternOptions(QRegularExpression.CaseInsensitiveOption)), col))

    def change_table_and_filters(self, index):
        """Change the current table and filters"""
        row_num = index.row()
        if self.table_name != self.tables[row_num][0]:
            self.table_name = self.tables[row_num][0]
            table_view_width, table_view_height = self.table_view.width(), self.table_view.height()
            self.get_table_config_data()
            self.clear_layout(self.filter_layout)
            self.clear_layout(self.table_layout)
            self.create_filters()
            self.create_table_view()
            self.fill_table_view(self.table_name)
            self.table_view.resize(table_view_width,table_view_height)
            self.resizeEvent(None)

    def create_table_view(self):
        """Create the table view."""
        self.model = QStandardItemModel(self.row_count, self.column_count)
        self.model.setHorizontalHeaderLabels(self.column_headers)
        self.proxy_model = SortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSortingEnabled(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setStyleSheet("QHeaderView::section { color: black; font-weight: normal;}")
        self.table_view.doubleClicked.connect(self.open_edit_window)
        self.table_layout.addWidget(self.table_view)

    def open_edit_window(self, index):
        """Open the edit window."""
        row_num = index.row()
        row_data = []
        for column_num in range(len(self.column_headers)):
            column_index = self.proxy_model.index(row_num, column_num)
            row_data.append(self.proxy_model.data(column_index, Qt.ItemDataRole.DisplayRole))
        self.window2 = DataEditWindow(self.table_name, self.column_headers, row_data, "Edit/Delete", self.conn, self.cursor)
        self.window2.resize(600, 300)
        self.window2.closed.connect(self.update_data)
        self.window2.show()

    def open_insert_window(self):
        """Open the insert window."""
        self.window2 = DataEditWindow(self.table_name, self.column_headers, None, "Insert", self.conn, self.cursor)
        self.window2.resize(600, 300)
        self.window2.closed.connect(self.update_data)
        self.window2.show()

    def fill_table_view(self, table_name):
        """Fill the table view with data."""
        try:
            table_row_index = 0
            for i in self.cursor.execute("SELECT * FROM `{}`".format(table_name)):
                for y in range(self.model.columnCount()):
                    self.model.setItem(table_row_index, y, QStandardItem(i[y]))
                table_row_index += 1
        except db.Error as error:
            print('Error occurred - ', error)   

    def update_data(self):
        """Update the data."""
        self.proxy_model.removeRows(0, self.proxy_model.rowCount())
        self.proxy_model._data = []
        self.proxy_model.layoutChanged.emit()
        self.fill_table_view(self.table_name)

    def close_db_connection(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print('SQLite Connection closed')

    def resizeEvent(self, event):
        """Reimplement the resize event."""
        table_size = self.table_view.width()
        number_of_columns = self.model.columnCount()

        for column_num in range(self.model.columnCount()):
            self.table_view.setColumnWidth(column_num, int((table_size-5) / number_of_columns))
        super(SQLiteDatabaseViewer, self).resizeEvent(event)

    def closeEvent(self, event):
        """Overwrite the close event."""
        self.closed.emit()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    qdarktheme.setup_theme("light")

    viewer = SQLiteDatabaseViewer()
    viewer.resize(1200, 500)
    viewer.show()

    app.exec()