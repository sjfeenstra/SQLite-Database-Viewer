from PySide6.QtCore import QSortFilterProxyModel


class SortFilterProxyModel(QSortFilterProxyModel):
    """A custom QSortFilterProxyModel to allow multiple column filtering"""

    def __init__(self, *args, **kwargs):
        QSortFilterProxyModel.__init__(self, *args, **kwargs)
        self.filters = {}

    def setFilterByColumn(self, regex, column):
        """Sets a filter by column using a regular expression."""
        self.filters[column] = regex
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        """Checks if row should be displayed or not based on filters"""
        for key, regex in self.filters.items():
            ix = self.sourceModel().index(source_row, key, source_parent)
            if ix.isValid():
                text = self.sourceModel().data(ix)
                match = regex.match(text)
                if not match.hasMatch():
                    return False
        return True
