import math
import sqlite3 as db

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QVBoxLayout, QWidget)


class DataEditWindow(QWidget):
    """Window for editing or inserting data."""

    closed = Signal()

    def __init__(self, table_name, column_headers, data, window_type, conn, cursor):
        """Initialize the window."""
        super().__init__()
        self.setWindowTitle(window_type)

        self.conn = conn
        self.cursor = cursor
        self.table_name = table_name
        self.column_headers = column_headers
        self.data = data
        self.line_edit_list = []
        self.primary_key_column = self.cursor.execute(
            "SELECT * FROM pragma_table_info(?) WHERE pk = 1", (self.table_name,)
        ).fetchone()
        if self.primary_key_column == None:
            self.primary_key_column = 0
        else:
            self.primary_key_column = self.primary_key_column[0]

        self.create_gui_layout()
        self.create_form()
        self.create_buttons(window_type)
        self.load_data(data)

    def create_gui_layout(self):
        """Create the GUI layout."""
        self.layout = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.h_Layout = QHBoxLayout()
        self.label_Layout = QHBoxLayout()
        self.layout.addLayout(self.grid_layout)
        self.layout.addLayout(self.label_Layout)
        self.layout.addLayout(self.h_Layout)
        self.setLayout(self.layout)
        self.messageLabel = QLabel()
        self.label_Layout.addWidget(self.messageLabel)

    def create_form(self):
        """Create the form for editing or inserting data."""
        max_rows = math.ceil(len(self.column_headers) / 2)
        for column in range(1, 4, 2):
            for row in range(max_rows):
                column_header_index = math.floor(column / 2) * max_rows + row
                if column_header_index == len(self.column_headers):
                    break
                line_edit = QLineEdit()
                self.line_edit_list.append(line_edit)
                label = QLabel(self.column_headers[column_header_index])
                line_edit.setPlaceholderText(
                    self.column_headers[column_header_index])
                self.grid_layout.addWidget(line_edit, row, column)
                self.grid_layout.addWidget(label, row, column - 1)

    def create_buttons(self, window_type):
        """Create the buttons for editing or inserting data."""
        if window_type == "Edit/Delete":
            edit_button = QPushButton("Edit")
            delete_button = QPushButton("Delete")
            edit_button.clicked.connect(self.update_data)
            delete_button.clicked.connect(self.delete_data)
            edit_button.setStyleSheet(" color: black;")
            delete_button.setStyleSheet(" color: red; border-color: red")
            self.h_Layout.addWidget(edit_button)
            self.h_Layout.addWidget(delete_button)
        elif window_type == "Insert":
            insert_button = QPushButton("Insert")
            insert_button.clicked.connect(self.insert_data)
            insert_button.setStyleSheet(" color: black;")
            self.h_Layout.addWidget(insert_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close_window)
        close_button.setStyleSheet("color: black;")
        self.layout.addWidget(close_button)

    def load_data(self, data):
        """Load the data into the form."""
        if data is not None:
            for i, line_edit in enumerate(self.line_edit_list):
                line_edit.setText(data[i])

    def insert_data(self):
        """Insert data into the database."""
        data = [line_edit.text() for line_edit in self.line_edit_list]
        print(data)
        if data[self.primary_key_column] != "":
            column_headers_string = ",".join(
                ["[{}]".format(header) for header in self.column_headers]
            )
            column_questionmark_string = ",".join(
                "?" for _ in range(len(self.column_headers))
            )
            try:
                self.cursor.execute(
                    "insert into {}({}) VALUES ({});".format(
                        self.table_name,
                        column_headers_string,
                        column_questionmark_string,
                    ),
                    (data),
                )
                self.conn.commit()
            except db.Error as error:
                print("Error occurred - ", error)
            self.close_window()
        else:
            self.messageLabel.setText(
                self.column_headers[self.primary_key_column] + " has no data"
            )

    def delete_data(self):
        """Delete data from the database."""
        reply = self.create_message_box().exec()
        if reply == QMessageBox.Yes:
            try:
                self.cursor.execute(
                    "DELETE FROM {} WHERE {} = ?".format(
                        self.table_name, self.column_headers[0]
                    ),
                    (self.data[0],),
                )
                self.conn.commit()
            except db.Error as error:
                print("Error occurred - ", error)
            self.close_window()

    def update_data(self):
        """Update data in the database."""
        data = [line_edit.text() for line_edit in self.line_edit_list]
        if data[self.primary_key_column] != "":
            column_headers_string = ", ".join(
                "[{}] = ?".format(header) for header in self.column_headers
            )
            try:
                self.cursor.execute(
                    "UPDATE {} SET {} WHERE {} = ?".format(
                        self.table_name, column_headers_string, self.column_headers[0]
                    ),
                    (data + [self.data[0]]),
                )
                self.conn.commit()
            except db.Error as error:
                print("Error occurred - ", error)
            self.close_window()
        else:
            self.messageLabel.setText(
                self.column_headers[self.primary_key_column] + " has no data"
            )

    def create_message_box(self):
        """Create a message box for confirmation."""
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Deleting data")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText("Are you sure you want to delete this row?")
        msg_box.setInformativeText("This action can't be undone")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        return msg_box

    def close_window(self):
        """Close the window."""
        self.close()

    def closeEvent(self, event):
        """Overwrite the close event."""
        self.closed.emit()
        event.accept()
