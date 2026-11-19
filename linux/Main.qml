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
    property string pendingDownloadId: ""
    property string previewId: ""
    property string previewName: ""
    property string previewMediaType: ""
    property string previewVersion: ""

    FileDialog {
        id: picker
        title: "Add a photo or video"
        fileMode: FileDialog.OpenFiles
        nameFilters: ["Photos and videos (*.jpg *.jpeg *.png *.gif *.webp *.mp4)", "All files (*)"]
        onAccepted: {
            for (let file of selectedFiles) photosBridge.upload(file.toString())
        }
    }

    FileDialog {
        id: savePicker
        title: "Save original photo or video"
        fileMode: FileDialog.SaveFile
        nameFilters: ["All files (*)"]
        onAccepted: photosBridge.download(window.pendingDownloadId, selectedFile.toString())
    }

    Dialog {
        id: securityDialog
        title: "Library security"
        modal: true
        focus: true
        width: Math.min(window.width - 36, 485)
        anchors.centerIn: parent
        closePolicy: Popup.CloseOnEscape
        property string feedback: ""
        onOpened: currentSecret.forceActiveFocus()
        onClosed: {
            currentSecret.text = ""
            newSecret.text = ""
            confirmSecret.text = ""
            feedback = ""
            securityButton.forceActiveFocus()
        }

        ColumnLayout {
            width: parent.width
            spacing: 12
            Label {
                Layout.fillWidth: true
                text: "Changing the password or signing out all devices immediately revokes every session."
                wrapMode: Text.WordWrap
            }
            TextField {
                id: currentSecret
                Layout.fillWidth: true
                placeholderText: "Current library password"
                Accessible.name: "Current library password"
                echoMode: TextInput.Password
                maximumLength: 1024
            }
            TextField {
                id: newSecret
                Layout.fillWidth: true
                placeholderText: "New password (12–1024 characters)"
                Accessible.name: "New library password"
                echoMode: TextInput.Password
                maximumLength: 1024
            }
            TextField {
                id: confirmSecret
                Layout.fillWidth: true
                placeholderText: "Confirm new password"
                Accessible.name: "Confirm new library password"
                echoMode: TextInput.Password
                maximumLength: 1024
            }
            Label {
                Layout.fillWidth: true
                visible: securityDialog.feedback.length > 0
                text: securityDialog.feedback
                wrapMode: Text.WordWrap
            }
            Button {
                Layout.fillWidth: true
                text: "Change password and sign out all devices"
                enabled: currentSecret.text.length > 0 && newSecret.text.length >= 12
                         && confirmSecret.text.length > 0
                onClicked: {
                    const current = currentSecret.text
                    const replacement = newSecret.text
                    const confirmation = confirmSecret.text
                    currentSecret.text = ""
                    newSecret.text = ""
                    confirmSecret.text = ""
                    securityDialog.feedback = ""
                    photosBridge.changePassword(current, replacement, confirmation)
                }
            }
            Button {
                Layout.fillWidth: true
                text: "Sign out all devices without changing password"
                enabled: currentSecret.text.length > 0
                onClicked: {
                    const current = currentSecret.text
                    currentSecret.text = ""
                    newSecret.text = ""
                    confirmSecret.text = ""
                    securityDialog.feedback = ""
                    photosBridge.revokeAllSessions(current)
                }
            }
            Button {
                Layout.fillWidth: true
                text: "Cancel"
                onClicked: securityDialog.close()
            }
        }
    }

    Dialog {
        id: previewDialog
        objectName: "privatePhotoPreview"
        title: window.previewName
        modal: true
        focus: true
        width: Math.min(window.width - 36, 720)
        height: Math.min(window.height - 36, 580)
        anchors.centerIn: parent
        closePolicy: Popup.CloseOnEscape
        standardButtons: Dialog.Close
        onClosed: {
            window.previewId = ""
            window.previewName = ""
            window.previewMediaType = ""
            window.previewVersion = ""
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 12
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Image {
                    anchors.fill: parent
                    visible: window.previewMediaType.indexOf("image/") === 0
                    source: visible && window.previewId.length > 0
                        ? "image://preview/" + window.previewId
                            + "?v=" + window.previewVersion : ""
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    cache: false
                    sourceSize.width: 512
                    sourceSize.height: 512
                    Accessible.name: "Private thumbnail preview of " + window.previewName
                }
                Label {
                    anchors.centerIn: parent
                    visible: window.previewMediaType.indexOf("video/") === 0
                    text: "Video preview unavailable"
                }
            }
            Label {
                Layout.fillWidth: true
                text: "Private low-resolution preview. Save the original for full quality."
                wrapMode: Text.WordWrap
            }
            Button {
                Layout.fillWidth: true
                text: "Save original"
                Accessible.name: "Save original " + window.previewName
                enabled: photosBridge.loggedIn && photosBridge.view !== "trash"
                onClicked: {
                    window.pendingDownloadId = window.previewId
                    previewDialog.close()
                    savePicker.open()
                }
            }
        }
    }

    Connections {
        target: photosBridge
        function onLoggedInChanged() {
            if (!photosBridge.loggedIn) previewDialog.close()
        }
        function onLibraryChanged() {
            if (!previewDialog.opened) return
            if (!photosBridge.loggedIn || photosBridge.view === "trash") {
                previewDialog.close()
                return
            }
            let found = false
            for (const item of photosBridge.items) {
                if (item.id !== window.previewId) continue
                window.previewVersion = item.thumbVersion || "0"
                found = true
                break
            }
            // A navigation, trash action or page change must never leave a
            // previous private media item visible in the new library view.
            if (!found) previewDialog.close()
        }
        function onError(text) {
            message.text = text
            if (securityDialog.opened) securityDialog.feedback = text
        }
        function onMessage(text) { message.text = text }
        function onSecurityCompleted() { securityDialog.close() }
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
            Button {
                id: securityButton
                text: "Security"
                visible: photosBridge.loggedIn
                Accessible.name: "Manage library password and device sessions"
                onClicked: securityDialog.open()
            }
            Button { text: "Lock"; visible: photosBridge.loggedIn; onClicked: photosBridge.logout() }
        }

        Label {
            id: message
            Layout.fillWidth: true
            color: palette.highlight
            wrapMode: Text.WordWrap
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

        RowLayout {
            visible: photosBridge.loggedIn
            Layout.fillWidth: true
            spacing: 12

            ComboBox {
                id: libraryView
                model: ["All photos", "Favorites", "Trash"]
                Accessible.name: "Library view"
                onActivated: function(index) {
                    photosBridge.setView(["library", "favorites", "trash"][index])
                }
            }
            TextField {
                id: librarySearch
                Layout.fillWidth: true
                placeholderText: "Search filenames"
                Accessible.name: "Search photo filenames"
                onAccepted: photosBridge.setSearch(text)
            }
            Button {
                text: "Search"
                onClicked: photosBridge.setSearch(librarySearch.text)
            }
            Button {
                text: "Clear"
                onClicked: { librarySearch.text = ""; photosBridge.setSearch("") }
            }
        }

        RowLayout {
            visible: photosBridge.loggedIn
            Layout.fillWidth: true
            spacing: 10
            ComboBox {
                id: albumSelection
                Layout.preferredWidth: 170
                model: photosBridge.albums
                textRole: "name"
                valueRole: "id"
                Accessible.name: "Choose album"
            }
            Button {
                text: "Open album"
                enabled: albumSelection.count > 0
                onClicked: photosBridge.viewAlbum(albumSelection.currentValue)
            }
            TextField {
                id: newAlbumName
                Layout.fillWidth: true
                placeholderText: "New album name"
                Accessible.name: "New album name"
                maximumLength: 100
                onAccepted: {
                    photosBridge.createAlbum(text)
                    text = ""
                }
            }
            Button {
                text: "Create"
                onClicked: {
                    photosBridge.createAlbum(newAlbumName.text)
                    newAlbumName.text = ""
                }
            }
            Button {
                text: "All"
                onClicked: photosBridge.setView("library")
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
                // A native photo gallery adapts its square-ish image tiles
                // to the available window width without a fixed column count.
                readonly property int columns: Math.max(1, Math.floor(width / 218))
                cellWidth: width / columns
                cellHeight: 365
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
                        Button {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 205
                            padding: 0
                            enabled: photosBridge.view !== "trash"
                            Accessible.name: "Open private preview of " + modelData.filename
                            onClicked: {
                                window.previewId = modelData.id
                                window.previewName = modelData.filename
                                window.previewMediaType = modelData.media_type
                                window.previewVersion = modelData.thumbVersion || "0"
                                previewDialog.open()
                            }
                            background: Rectangle {
                                radius: 12
                                color: palette.midlight
                            }
                            contentItem: Item {
                                Label {
                                    anchors.centerIn: parent
                                    visible: modelData.media_type.indexOf("video/") === 0
                                    text: "▶ Video"
                                    font.bold: true
                                    Accessible.name: "Video file"
                                }
                                Image {
                                    anchors.fill: parent
                                    visible: modelData.media_type.indexOf("image/") === 0
                                    source: visible
                                        ? "image://preview/" + modelData.id + "?v="
                                            + (modelData.thumbVersion || "0")
                                        : ""
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                    cache: false
                                    sourceSize.width: 410
                                    sourceSize.height: 410
                                }
                            }
                        }
                        Label {
                            text: modelData.filename
                            Accessible.name: "Photo filename " + modelData.filename
                            Layout.fillWidth: true
                            elide: Label.ElideRight
                        }
                        RowLayout {
                            Button {
                                visible: photosBridge.view !== "trash"
                                text: modelData.favorite ? "♥" : "♡"
                                Accessible.name: modelData.favorite ? "Remove favorite" : "Add favorite"
                                onClicked: photosBridge.favorite(modelData.id, !modelData.favorite)
                            }
                            Button {
                                text: "Save"
                                visible: photosBridge.view !== "trash"
                                Accessible.name: "Save original " + modelData.filename
                                onClicked: {
                                    window.pendingDownloadId = modelData.id
                                    savePicker.open()
                                }
                            }
                            Button {
                                text: "Trash"
                                visible: photosBridge.view !== "trash"
                                onClicked: photosBridge.trash(modelData.id)
                            }
                            Button {
                                text: "Restore"
                                visible: photosBridge.view === "trash"
                                onClicked: photosBridge.restore(modelData.id)
                            }
                        }
                        RowLayout {
                            visible: photosBridge.view !== "trash"
                            Button {
                                text: "Add to album"
                                visible: photosBridge.view !== "album" && albumSelection.count > 0
                                Accessible.name: "Add " + modelData.filename + " to selected album"
                                onClicked: photosBridge.addToAlbum(albumSelection.currentValue, modelData.id)
                            }
                            Button {
                                text: "Remove from album"
                                visible: photosBridge.view === "album"
                                Accessible.name: "Remove " + modelData.filename + " from this album without deleting original"
                                onClicked: photosBridge.removeFromAlbum(modelData.id)
                            }
                        }
                    }
                }
            }
        }

        RowLayout {
            visible: photosBridge.loggedIn
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: photosBridge.total + " items · Page " +
                      photosBridge.currentPage + " of " + photosBridge.pageCount
            }
            Button {
                text: "Previous"
                enabled: photosBridge.currentPage > 1
                onClicked: photosBridge.changePage(-1)
            }
            Button {
                text: "Next"
                enabled: photosBridge.currentPage < photosBridge.pageCount
                onClicked: photosBridge.changePage(1)
            }
        }
    }
}
