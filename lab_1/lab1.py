import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа — PyQt5")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowOpacity(1.0)  # Начальная непрозрачность
        self.setStyleSheet("")      # Убираем любой фон

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout — вертикальный, чтобы элементы шли сверху вниз
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Надпись — по центру
        self.label = QLabel("Надпись", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.label)

        # Кнопка 1 — меняет надпись
        btn1 = QPushButton("Кнопка1", self)
        btn1.clicked.connect(self.change_label_text)
        layout.addWidget(btn1)

        # Кнопка 2 — переключает между режимами
        self.btn2 = QPushButton("Кнопка2", self)
        self.btn2.clicked.connect(self.toggle_background_mode)
        layout.addWidget(self.btn2)

        # Переменная для отслеживания текущего режима:
        # 0 — обычный фон (непрозрачный, без PNG)
        # 1 — полупрозрачное окно
        # 2 — фон с PNG
        self.current_mode = 0

    def change_label_text(self):
        """При нажатии Кнопки1 — меняет текст надписи"""
        current_text = self.label.text()
        if current_text == "Надпись":
            self.label.setText("Текст изменён!")
        else:
            self.label.setText("Надпись")

    def toggle_background_mode(self):
        """
        При нажатии Кнопки2 — переключается между тремя режимами:
        1. Обычный фон (непрозрачный, белый/серый — зависит от системы)
        2. Полупрозрачное окно (прозрачность 60%)
        3. Фон с загруженным PNG (kirieshki.png)
        """

        # Режим 0 → переходим в режим 1 (полупрозрачность)
        if self.current_mode == 0:
            self.setWindowOpacity(0.6)
            self.setStyleSheet("")  # Убираем фон, если был
            self.btn2.setText("Кнопка2 (PNG)")
            self.label.setText("Окно полупрозрачное")
            self.current_mode = 1

        # Режим 1 → переходим в режим 2 (загружаем PNG)
        elif self.current_mode == 1:
            png_path = "PyQt_labs/lab_1/kirieshki.png"  # Имя файла с твоей картинкой, если не работает надо указать полный путь к файлу
            if os.path.exists(png_path):
                # Устанавливаем PNG как фон
                self.setStyleSheet(f"background-image: url({png_path}); background-repeat: no-repeat; background-position: center;")
                self.setWindowOpacity(1.0)  # Окно снова полностью непрозрачное
                self.btn2.setText("Кнопка2 (Обычный фон)")
                self.label.setText("Фон: Кириешки загружены!")
                self.current_mode = 2
            else:
                # Если PNG не найден — показываем предупреждение и остаёмся в режиме 1
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Файл 'kirieshki.png' не найден!\nПомести его в папку с программой."
                )
                self.label.setText("Файл kirieshki.png не найден!")
                # Можно оставить в режиме 1 или вернуться к режиму 0
                self.current_mode = 0  # Вернёмся к обычному фону
                self.setWindowOpacity(1.0)
                self.setStyleSheet("")
                self.btn2.setText("Кнопка2 (Прозрачность)")
                self.label.setText("Вернулись к обычному фону")

        # Режим 2 → переходим в режим 0 (обычный фон)
        elif self.current_mode == 2:
            self.setStyleSheet("")  # Убираем PNG фон
            self.setWindowOpacity(1.0)  # Восстанавливаем полную непрозрачность
            self.btn2.setText("Кнопка2 (Прозрачность)")
            self.label.setText("Фон сброшен — обычный фон")
            self.current_mode = 0


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
