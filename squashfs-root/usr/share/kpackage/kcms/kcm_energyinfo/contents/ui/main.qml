/***************************************************************************
 *   Copyright (C) 2015 Kai Uwe Broulik <kde@privat.broulik.de>            *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA            *
 ***************************************************************************/

import QtQuick 2.5
import QtQuick.Controls 2.5 as QQC2
import QtQuick.Layouts 1.1
import org.kde.kirigami 2.5 as Kirigami

import org.kde.kquickcontrolsaddons 2.0
import org.kde.kinfocenter.energy.private 1.0

import org.kde.plasma.core 2.0 as PlasmaCore

import org.kde.kcm 1.1 as KCM

KCM.SimpleKCM {
    id: root

    KCM.ConfigModule.quickHelp: i18n("This module lets you see energy information and statistics.")

    property QtObject currentBattery: null
    property string currentUdi: ""
    property string currentVendor: ""
    property string currentProduct: ""
    property bool compact: (root.width / units.gridUnit) < 25

    function initCurrentBattery() {
        currentBattery = kcm.batteries.data(kcm.batteries.index(0, 0), BatteryModel.BatteryRole)
        currentVendor = kcm.batteries.data(kcm.batteries.index(0, 0), BatteryModel.VendorRole)
        currentProduct = kcm.batteries.data(kcm.batteries.index(0, 0), BatteryModel.ProductRole)
        currentUdi = kcm.batteries.data(kcm.batteries.index(0, 0), BatteryModel.UdiRole)
    }

    Component.onCompleted: initCurrentBattery()

    onCurrentBatteryChanged: {
        if (!currentBattery) {
            initCurrentBattery()
        }
    }

    property bool showWakeUps: true
    property int historyType: HistoryModel.ChargeType

    readonly property var details: [
        {
            title: i18n("Battery"),
            data: [
                {label: i18n("Rechargeable"), value: "rechargeable"},
                {label: i18n("Charge state"), value: "chargeState", modifier: "chargeState"},
                {label: i18n("Current charge"), value: "chargePercent", unit: i18n("%"), precision: 0},
                {label: i18n("Health"), value: "capacity", unit: i18n("%"), precision: 0},
                {label: i18n("Vendor"), value: "vendor", source:"Vendor"},
                {label: i18n("Model"), value: "model", source:"Product"},
                {label: i18n("Serial Number"), value: "serial"}
            ]
        },
        {
            title: i18n("Energy"),
            data: [
                {label: i18nc("current power draw from the battery in W", "Consumption"), value: "energyRate", unit: i18nc("Watt", "W"), precision: 2},
                {label: i18n("Voltage"), value: "voltage", unit: i18nc("Volt", "V"), precision: 2},
                {label: i18n("Remaining energy"), value: "energy", unit: i18nc("Watt-hours", "Wh"), precision: 2},
                {label: i18n("Last full charge"), value: "energyFull", unit: i18nc("Watt-hours", "Wh"), precision: 2},
                {label: i18n("Original charge capacity"), value: "energyFullDesign", unit: i18nc("Watt-hours", "Wh"), precision: 2}
            ]
        },
        {
            title: i18n("Environment"),
            data: [
                {label: i18n("Temperature"), value: "temperature", unit: i18nc("Degree Celsius", "°C"), precision: 2}
            ]
        },
    ]

    function modifier_chargeState(value) {
        switch(value) {
        case 0: return i18n("Not charging")
        case 1: return i18n("Charging")
        case 2: return i18n("Discharging")
        case 3: return i18n("Fully charged")
        }
    }

    implicitWidth: units.gridUnit * 30
    implicitHeight: !!currentBattery ? units.gridUnit * 30 : units.gridUnit * 12

    readonly property var timespanComboChoices: [i18n("Last hour"),i18n("Last 2 hours"),i18n("Last 12 hours"),i18n("Last 24 hours"),i18n("Last 48 hours"), i18n("Last 7 days")]
    readonly property var timespanComboDurations: [3600, 7200, 43200, 86400, 172800, 604800]

    ColumnLayout {
        id: column
        QQC2.ScrollView {
            id: tabView
            Layout.fillWidth: true
            Layout.minimumHeight: units.gridUnit * 4
            Layout.maximumHeight: Layout.minimumHeight
            visible: kcm.batteries.count > 1

            Row {
                spacing: Kirigami.Units.smallSpacing
                Repeater {
                    model: kcm.batteries

                    QQC2.Button {
                        id: button
                        width: units.gridUnit * 10
                        height: tabView.height
                        checked: model.battery == root.currentBattery
                        checkable: true
                        onClicked: {
                            root.currentUdi = model.udi
                            root.currentVendor = model.vendor
                            root.currentProduct = model.product
                            root.currentBattery = model.battery

                            // override checked property
                            checked = Qt.binding(function() {
                                return model.battery == root.currentBattery
                            })

                            showWakeUps = (index === 0)
                        }

                        ColumnLayout {
                            anchors {
                                fill: parent
                                margins: units.smallSpacing * 2
                            }
                            RowLayout {

                                Kirigami.Icon {
                                    id: batteryIcon
                                    Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                                    Layout.preferredHeight: Layout.preferredWidth
                                    source: {
                                        switch(model.battery.type) {
                                        case 3: return model.battery.chargeState === 1 ? "battery-full-charging" : "battery-full"
                                        case 2: return "battery-ups"
                                        case 9: return "monitor"
                                        case 4: return "input-mouse"
                                        case 5: return "input-keyboard"
                                        case 1: return "phone"
                                        case 7: return "smartphone"
                                        default: return "paint-unknown"
                                        }
                                    }
                                }

                                QQC2.Label {
                                    Layout.fillWidth: true
                                    text: {
                                        switch(model.battery.type) {
                                        case 3: return i18n("Internal battery")
                                        case 2: return i18n("UPS battery")
                                        case 9: return i18n("Monitor battery")
                                        case 4: return i18n("Mouse battery")
                                        case 5: return i18n("Keyboard battery")
                                        case 1: return i18n("PDA battery")
                                        case 7: return i18n("Phone battery")
                                        default: return i18n("Unknown battery")
                                        }
                                    }
                                    elide: Text.ElideRight
                                }
                            }

                            RowLayout {
                                QQC2.ProgressBar {
                                    id: percentageSlider
                                    Layout.fillWidth: true
                                    from: 0
                                    to: 100
                                    value: model.battery.chargePercent
                                }

                                QQC2.Label {
                                    text: model.battery.chargeState === 1 ?
                                        i18nc("Battery charge percentage", "%1% (Charging)", Math.round(percentageSlider.value)) :
                                        i18nc("Battery charge percentage", "%1%", Math.round(percentageSlider.value))
                                }
                            }
                        }
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: units.smallSpacing
            visible: !!currentBattery

            GridLayout {
                Layout.fillWidth: true
                columns: !compact ? 5 : 3

                QQC2.Button {
                    id: chargeButton
                    checked: true
                    checkable: true
                    text: i18n("Charge Percentage")
                    onClicked: {
                        historyType = HistoryModel.ChargeType
                        rateButton.checked = false
                    }
                }

                QQC2.Button {
                    id: rateButton
                    checkable: true
                    text: i18n("Energy Consumption")
                    onClicked: {
                        historyType = HistoryModel.RateType
                        chargeButton.checked = false
                    }
                }

                Item {
                    Layout.fillWidth: true
                }

                QQC2.ComboBox {
                    id: timespanCombo
                    Layout.minimumWidth: units.gridUnit * 6
                    model: timespanComboChoices
                    Accessible.name: i18n("Timespan")
                    Accessible.description: i18n("Timespan of data to display")
                }

                QQC2.Button {
                    icon.name: "view-refresh"
                    hoverEnabled: true
                    QQC2.ToolTip.text: i18n("Refresh")
                    QQC2.ToolTip.visible: hovered
                    QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
                    Accessible.name: QQC2.ToolTip.text
                    onClicked: history.refresh()
                }
            }

            HistoryModel {
                id: history
                duration: timespanComboDurations[timespanCombo.currentIndex]
                device: currentUdi
                type: root.historyType
            }

            Graph {
                id: graph
                Layout.fillWidth: true
                Layout.minimumHeight: column.width / 3
                Layout.maximumHeight: column.width / 3
                Layout.topMargin: units.largeSpacing

                data: history.points

                readonly property real xTicksAtDontCare: 0 
                readonly property real xTicksAtTwelveOClock: 1
                readonly property real xTicksAtFullHour: 2
                readonly property real xTicksAtHalfHour: 3
                readonly property real xTicksAtFullSecondHour: 4
                readonly property real xTicksAtTenMinutes: 5            
                readonly property var xTicksAtList: [xTicksAtTenMinutes, xTicksAtHalfHour, xTicksAtHalfHour, 
                                                     xTicksAtFullHour, xTicksAtFullSecondHour, xTicksAtTwelveOClock]

                // Set grid lines distances which directly correspondent to the xTicksAt variables
                readonly property var xDivisionWidths: [1000 * 60 * 10, 1000 * 60 * 60 * 12, 1000 * 60 * 60, 1000 * 60 * 30, 1000 * 60 * 60 * 2, 1000 * 60 * 10]
                xTicksAt: xTicksAtList[timespanCombo.currentIndex]
                xDivisionWidth: xDivisionWidths[xTicksAt]

                xMin: history.firstDataPointTime
                xMax: history.lastDataPointTime
                xDuration: history.duration
    
                yUnits: root.historyType == HistoryModel.RateType ? i18nc("Shorthand for Watts","W") : i18nc("literal percent sign","%")
                yMax: {
                    if (root.historyType == HistoryModel.RateType) {
                        // ceil to nearest 10
                        var max = Math.floor(history.largestValue)
                        max = max - max % 10 + 10
                        
                        return max;
                    } else {
                        return 100;
                    }
                }
                yStep: root.historyType == HistoryModel.RateType ? 10 : 20
                visible: history.count > 1
            }

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                Layout.topMargin: units.smallSpacing
                showCloseButton: true
                text: i18n("This type of history is currently not available for this device.")
                visible: !graph.visible
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: units.smallSpacing
            visible: showWakeUps && kcm.wakeUps.count > 0

            RowLayout {
                Layout.fillWidth: true
                Kirigami.Heading {
                    Layout.fillWidth: true
                    Layout.columnSpan: 2
                    level: 4
                    text: i18n("Application Energy Consumption")
                }
            }

            GridLayout {
                id: wakeUpsGrid
                Layout.fillWidth: true
                rows: compact ? kcm.wakeUps.count : kcm.wakeUps.count / 2
                flow: GridLayout.TopToBottom
                rowSpacing: units.smallSpacing
                columnSpacing: units.smallSpacing
                property int barWidth: (compact ? root.width - units.gridUnit: root.width / 2) - units.smallSpacing * 2

                Repeater {
                    model: showWakeUps ? kcm.wakeUps : null

                    PlasmaCore.ToolTipArea { // FIXME use widget style tooltip
                        Layout.minimumWidth: wakeUpsGrid.barWidth
                        Layout.maximumWidth: wakeUpsGrid.barWidth
                        height: childrenRect.height
                        z: 2 // since the progress bar eats mouse events
                        mainText: model.prettyName || model.name
                        subText: {
                            var text = ""
                            if (model.prettyName && model.name !== model.prettyName) {
                                text += i18n("Path: %1", model.name) + "\n"
                            }
                            if (model.pid) {
                                text += i18n("PID: %1", model.pid) + "\n"
                            }
                            // FIXME format decimals
                            text += i18n("Wakeups per second: %1 (%2%)", Math.round(model.wakeUps * 100) / 100, Math.round(model.wakeUps / kcm.wakeUps.total * 100)) + "\n"
                            if (model.details) {
                                text += i18n("Details: %1", model.details)
                            }
                            return text
                        }
                        icon: model.iconName

                        RowLayout {
                            id: wakeUpItemRow
                            width: parent.width

                            QIconItem {
                                width: units.iconSizes.medium
                                height: width
                                icon: model.iconName
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0

                                RowLayout {
                                    Layout.fillWidth: true

                                    QQC2.Label {
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                        text: model.prettyName || model.name
                                    }

                                    /*QQC2.Label {
                                        text: i18n("System Service")
                                        visible: !model.userSpace
                                        opacity: 0.6
                                    }*/
                                }

                                QQC2.ProgressBar {
                                    Layout.fillWidth: true
                                    from: 0
                                    to: 100
                                    value: model.wakeUps / kcm.wakeUps.total * 100
                                }
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Kirigami.Theme.textColor // FIXME palette
            //Layout.topMargin: (compact ? units.gridUnit * 2 : 0)
            visible: wakeUpsGrid.visible
        }

        ColumnLayout {
            id: detailsColumn
            spacing: 0

            Layout.fillWidth: true
            visible: !!currentBattery

            Repeater {
                id: titleRepeater
                model: root.details
                property list<Kirigami.FormLayout> layouts

                delegate: Kirigami.FormLayout {
                    id: currentLayout

                    Component.onCompleted: {
                        // ensure that all visible FormLayout share the same set of twinFormLayouts
                        titleRepeater.layouts.push(currentLayout);
                        for (var i = 0, length = titleRepeater.layouts.length; i < length; ++i) {
                            titleRepeater.layouts[i].twinFormLayouts = titleRepeater.layouts;
                        }
                    }

                    Kirigami.Heading {
                        text: modelData.title
                        Kirigami.FormData.isSection: true
                        level: 2
                        // HACK hide section header if all labels are invisible
                        visible: {
                            for (var i = 0, length = detailsRepeater.count; i < length; ++i) {
                                var item = detailsRepeater.itemAt(i)
                                if (item && item.visible) {
                                    return true
                                }
                            }

                            return false
                        }
                    }

                    Repeater {
                        id: detailsRepeater
                        model: modelData.data || []

                        QQC2.Label {
                            id: valueLabel
                            Kirigami.FormData.label: i18n("%1:", modelData.label)
                            text: {
                                var value;
                                if (modelData.source) {
                                    value = root["current" + modelData.source];
                                } else {
                                    value = currentBattery[modelData.value]
                                }

                                if (typeof value === "boolean") {
                                    if (value) {
                                        return i18n("Yes")
                                    } else {
                                        return i18n("No")
                                    }
                                }

                                if (!value) {
                                    return ""
                                }

                                var precision = modelData.precision
                                if (typeof precision === "number") { // round to decimals
                                    value = Number(value).toLocaleString(Qt.locale(), "f", precision)
                                }

                                if (modelData.modifier && root["modifier_" + modelData.modifier]) {
                                    value = root["modifier_" + modelData.modifier](value)
                                }

                                if (modelData.unit) {
                                    value = i18nc("%1 is value, %2 is unit", "%1 %2", value, modelData.unit)
                                }

                                return value
                            }
                            visible: valueLabel.text !== ""
                        }
                    }
                }
            }
        }
    }
}
