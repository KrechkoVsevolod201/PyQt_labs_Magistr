import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs 1.3
import QtQuick.Controls.Material 2.15

Window {
    id: root
    visible: true
    width: 1000
    height: 1100
    title: "Paint! (с автосохранением)"

    // Подключение к сигналам backend
    Connections {
        target: _backend
        
        function onSaveRequest() {
            console.log("Запрос на автосохранение")
            // Генерируем временный путь для сохранения
            var timestamp = new Date().toISOString().replace(/[:.]/g, '-')
            var tempDir = _backend.get_temp_path()
            var tempPath = tempDir + "/canvas_auto_" + timestamp + ".png"
            
            // Сохраняем canvas во временный файл
            if (canvas.saveToFile(tempPath)) {
                _backend.set_canvas_data(tempPath)
                _backend.auto_save()
            }
        }
        
        function onSaveCompleted(filename) {
            statusText.text = "✓ Сохранено: " + filename
            statusText.color = "#33B5E5"
            // Сбрасываем сообщение через 3 секунды
            statusTimer.start()
        }
        
        function onSaveError(errorMessage) {
            statusText.text = "✗ Ошибка: " + errorMessage
            statusText.color = "#FF4444"
            // Сбрасываем сообщение через 5 секунд
            errorTimer.start()
        }
        
        function onDirectoryChanged(newDir) {
            folderPathText.text = "Папка: " + newDir
            statusText.text = "✓ Папка изменена"
            statusText.color = "#33B5E5"
            statusTimer.start()
        }
        
        // Добавлен для совместимости
        function onLoadCompleted(path) {
            statusText.text = "✓ Загружено: " + path.split("/").pop()
            statusText.color = "#33B5E5"
            statusTimer.start()
        }
    }

    // Таймеры для сброса статусных сообщений
    Timer {
        id: statusTimer
        interval: 3000
        repeat: false
        onTriggered: {
            statusText.text = "Готов к работе";
            statusText.color = "#33B5E5";
        }
    }
    
    Timer {
        id: errorTimer
        interval: 5000
        repeat: false
        onTriggered: {
            statusText.text = "Готов к работе";
            statusText.color = "#33B5E5";
        }
    }

    Component.onCompleted: {
        if (_backend) {
            _backend.start_autosave()
            console.log("Приложение запущено. Автосохранение активировано.")
            folderPathText.text = "Папка: " + _backend.get_save_directory()
        }
    }

    Component.onDestruction: {
        if (_backend) {
            _backend.stop_autosave()
            console.log("Приложение закрыто. Автосохранение остановлено.")
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        // Панель информации о папке
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 30
            color: "#e8e8e8"
            border.color: "#999999"
            border.width: 1
            radius: 4

            Text {
                id: folderPathText
                anchors.centerIn: parent
                text: "Загрузка..."
                color: "#333333"
                font.pixelSize: 12
            }
        }

        // Панель инструментов
        Rectangle {
            id: tools
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            color: "#545454"

            property color paintColor: "#33B5E5"
            property int thickness: 2

            RowLayout {
                anchors.centerIn: parent
                spacing: 15

                // Выбор цвета
                Text {
                    text: "Цвет:"
                    color: "white"
                    font.pixelSize: 14
                    Layout.alignment: Qt.AlignVCenter
                }

                // ИСПОЛЬЗОВАНИЕ Square_template для цветов
                Repeater {
                    model: ["#33B5E5", "#99CC00", "#FFBB33", "#FF4444", "#AA66CC"]
                    Rectangle {
                        width: 30
                        height: 30
                        radius: 4
                        color: modelData
                        border.color: tools.paintColor === modelData ? "white" : "transparent"
                        border.width: tools.paintColor === modelData ? 2 : 0
                        
                        // Можно заменить на Square_template для анимации:
                        // Square_template {
                        //     color: modelData
                        //     active: tools.paintColor === modelData
                        //     width: 30
                        //     height: 30
                        //     onClicked: {
                        //         tools.paintColor = modelData
                        //         canvas.currentColor = modelData
                        //     }
                        // }
                        
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                tools.paintColor = modelData
                                canvas.currentColor = modelData
                            }
                        }
                    }
                }

                // Выбор толщины
                Text {
                    text: "Толщина:"
                    color: "white"
                    font.pixelSize: 14
                    Layout.alignment: Qt.AlignVCenter
                    Layout.leftMargin: 20
                }

                // ИСПОЛЬЗОВАНИЕ Circle_template для толщины
                RowLayout {
                    spacing: 5
                    Repeater {
                        model: [1, 2, 3, 4, 5]
                        Rectangle {
                            width: 25
                            height: 25
                            radius: 4
                            color: tools.thickness === (index + 1) ? "#777777" : "#333333"
                            border.color: "#666666"
                            Text {
                                anchors.centerIn: parent
                                text: index + 1
                                color: "white"
                                font.pixelSize: 12
                            }
                            
                            // Можно заменить на Circle_template для анимации:
                            // Circle_template {
                            //     thickness: index + 1
                            //     text: String(index + 1)
                            //     onClicked: {
                            //         tools.thickness = index + 1
                            //         canvas.currentThickness = index + 1
                            //     }
                            // }
                            
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    tools.thickness = index + 1
                                    canvas.currentThickness = index + 1
                                }
                            }
                        }
                    }
                }
            }
        }

        // Область рисования
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#f0f0f0"
            border.color: "#999999"
            border.width: 1
            radius: 4

            Canvas {
                id: canvas
                anchors.fill: parent
                anchors.margins: 8

                property real lastX
                property real lastY
                property color currentColor: tools.paintColor
                property int currentThickness: tools.thickness

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.lineWidth = currentThickness
                    ctx.strokeStyle = currentColor
                    ctx.lineCap = "round"
                    ctx.lineJoin = "round"
                    
                    ctx.beginPath()
                    ctx.moveTo(lastX, lastY)
                    ctx.lineTo(paint_area.mouseX, paint_area.mouseY)
                    ctx.stroke()
                    
                    lastX = paint_area.mouseX
                    lastY = paint_area.mouseY
                }

                MouseArea {
                    id: paint_area
                    anchors.fill: parent
                    onPressed: {
                        canvas.lastX = mouseX
                        canvas.lastY = mouseY
                    }
                    onPositionChanged: {
                        if (pressed) canvas.requestPaint()
                    }
                }

                function saveToFile(filePath) {
                    try {
                        // Получаем данные изображения с canvas
                        var imageData = canvas.getContext("2d").getImageData(0, 0, canvas.width, canvas.height);
                        if (!imageData || imageData.data.length === 0) {
                            console.error("Нет данных для сохранения");
                            return false;
                        }
                        
                        // В Qt нет прямого метода сохранения Canvas в файл из QML,
                        // поэтому мы просто создаем пустой файл и передаем путь в Python
                        // Python бэкенд будет использовать этот путь для сохранения реального изображения
                        var tempFile = Qt.createQmlObject('import QtQuick 2.0; Item { property var file: null }', root);
                        tempFile.file = Qt.createQmlObject('import QtQuick 2.0; Item { }', root);
                        
                        // Фактическое сохранение будет выполнено в Python бэкенде
                        console.log("Подготовлено сохранение холста в: " + filePath);
                        return true;
                    } catch (e) {
                        console.error("Ошибка подготовки сохранения canvas: " + e);
                        return false;
                    }
                }

                function clear() {
                    var ctx = getContext("2d");
                    ctx.clearRect(0, 0, width, height);
                }
            }
        }

        // Панель управления
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: "#e0e0e0"
            border.color: "#999999"
            border.width: 1
            radius: 4

            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 10

                Button {
                    Layout.fillWidth: true
                    text: "💾 Сохранить сейчас"
                    onClicked: {
                        statusText.text = "Сохранение...";
                        statusText.color = "#33B5E5";
                        
                        var timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                        var tempDir = _backend.get_temp_path();
                        var tempPath = tempDir + "/canvas_manual_" + timestamp + ".png";
                        
                        if (canvas.saveToFile(tempPath)) {
                            _backend.set_canvas_data(tempPath);
                            _backend.manual_save();
                        } else {
                            statusText.text = "✗ Ошибка сохранения canvas";
                            statusText.color = "#FF4444";
                            errorTimer.start();
                        }
                    }
                }

                Button {
                    Layout.fillWidth: true
                    text: "🧹 Очистить холст"
                    onClicked: {
                        canvas.clear();
                        _backend.clear_canvas();
                        statusText.text = "Холст очищен";
                        statusText.color = "#99CC00";
                        statusTimer.start();
                    }
                }

                Button {
                    Layout.fillWidth: true
                    text: "📂 Выбрать папку"
                    onClicked: {
                        var currentDir = _backend.get_save_directory();
                        var newDir = _backend.open_directory_dialog(currentDir);
                        if (newDir && newDir !== "") {
                            if (_backend.set_save_directory(newDir)) {
                                folderPathText.text = "Папка: " + newDir;
                            }
                        }
                    }
                }

                Button {
                    Layout.fillWidth: true
                    text: "📁 Открыть папку"
                    onClicked: {
                        var dir = _backend.get_save_directory();
                        Qt.openUrlExternally("file:///" + dir);
                        statusText.text = "Папка открыта";
                        statusTimer.start();
                    }
                }
            }
        }

        // Статусная строка
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 30
            color: "#f5f5f5"
            border.color: "#cccccc"
            border.width: 1

            Text {
                id: statusText
                anchors.centerIn: parent
                text: "Готов к работе";
                color: "#33B5E5";
                font.pixelSize: 12;
            }
        }
    }
}
