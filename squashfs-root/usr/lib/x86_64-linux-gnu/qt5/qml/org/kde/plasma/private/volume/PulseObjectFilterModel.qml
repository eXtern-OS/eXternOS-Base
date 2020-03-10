import org.kde.plasma.core 2.1 as PlasmaCore

PlasmaCore.SortFilterModel {
    property var filters: []

    filterCallback: function(source_row, value) {
        var idx = sourceModel.index(source_row, 0);
        for (var i = 0; i < filters.length; ++i) {
            var filter = filters[i];
            if (sourceModel.data(idx, sourceModel.role(filter.role)) != filter.value) {
                return false;
            }
        }
        return true;
    }
}
