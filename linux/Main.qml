import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    id: window
    visible: true
    width: 1080
    height: 740
    minimumWidth: 560
    minimumHeight: 440
    title: "GoreeCloud Photos"
    color: palette.window

    FileDialog {
        id: picker
        title: "Add a photo or video"
        fileMode: FileDialog.OpenFiles
        nameFilters: ["Photos and videos (*.jpg *.jpeg *.png *.gif *.webp *.mp4)", "All files (*)"]
        onAccepted: for (let file of selectedFiles) photosBridge.upload(file.toString())
    }

    Connections {
        target: photosBridge
        function onError(text) { message.text = text }
        function onMessage(text) { message.text = text }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        RowLayout {
            spacing: 14
            Label { text: "✦ GoreeCloud Photos"; font.pixelSize: 24; font.bold: true; Layout.fillWidth: true }
            Button { text: "Refresh"; visible: photosBridge.loggedIn; onClicked: photosBridge.refresh() }
            Button { text: "Add photos"; visible: photosBridge.loggedIn; onClicked: picker.open() }
            Button { text: "Lock"; visible: photosBridge.loggedIn; onClicked: photosBridge.logout() }
        }

        Label {
            id: message
            Layout.fillWidth: true
            color: palette.highlight
            wrapMode: Text.WordWrap
            accessibleName: text
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !photosBridge.loggedIn

            ColumnLayout {
                anchors.centerIn: parent
                width: Math.min(parent.width, 360)
                spacing: 16
                Label { text: "Unlock your private library"; font.pixelSize: 20; font.bold: true }
                TextField {
                    id: pass
                    Layout.fillWidth: true
                    placeholderText: "Library password"
                    echoMode: TextInput.Password
                    onAccepted: { photosBridge.login(text); text = "" }
                }
                Button {
                    text: "Unlock"
                    Layout.fillWidth: true
                    onClicked: { photosBridge.login(pass.text); pass.text = "" }
                }
                Label { text: "Your password and session stay in memory."; wrapMode: Text.WordWrap }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: photosBridge.loggedIn
            clip: true
            GridView {
                id: grid
                model: photosBridge.items
                cellWidth: 192
                cellHeight: 240
                clip: true
                delegate: Rectangle {
                    width: grid.cellWidth - 12
                    height: grid.cellHeight - 10
                    radius: 18
                    color: palette.base
                    border.color: palette.mid
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 6
                        Image {
                            source: modelData.media_type.indexOf("image/") === 0
                                ? "image://preview/" + modelData.id + "?v=" + (modelData.thumbVersion || "0")
                                : ""
                            Layout.fillWidth: true
                            Layout.preferredHeight: 155
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                            sourceSize.width: 350
                            sourceSize.height: 350
                        }
                        Label { text: modelData.filename; Layout.fillWidth: true; elide: Label.ElideRight }
                        RowLayout {
                            Button {
                                text: modelData.favorite ? "♥" : "♡"
                                Accessible.name: modelData.favorite ? "Remove favorite" : "Add favorite"
                                onClicked: photosBridge.favorite(modelData.id, !modelData.favorite)
                            }
                            Button { text: "Trash"; onClicked: photosBridge.trash(modelData.id) }
                        }
                    }
                }
            }
        }
    }
}
