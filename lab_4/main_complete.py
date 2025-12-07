import sys
import os
import json
from datetime import datetime
from pathlib import Path
import tempfile
from PyQt5.QtCore import QUrl, QObject, QTimer, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow
from PyQt5.QtQml import QQmlApplicationEngine, QQmlComponent

class Interface(QObject):
    """
    Backend для приложения painter с автосохранением и выбором директории.
    """

    # Сигналы для уведомления QML
    saveRequest = pyqtSignal()  # Сигнал для инициации сохранения
    saveCompleted = pyqtSignal(str)  # Отправляет имя сохраненного файла
    saveError = pyqtSignal(str)  # Отправляет сообщение об ошибке
    directoryChanged = pyqtSignal(str)  # Уведомляет об изменении директории
    loadCompleted = pyqtSignal(str)  # Добавлен сигнал для совместимости с QML

    def __init__(self):
        super().__init__()

        # Параметры сохранения
        self._interval_sec = 30  # Интервал автосохранения в секундах
        self.save_directory = self._get_default_save_dir()

        # Данные для сохранения
        self.canvas_data = None

        # ✅ НОВОЕ: Путь для автосохраняемого файла (перезаписывается)
        self.autosave_filename = "autosave_backup.png"
        self.autosave_path = os.path.join(self.save_directory, self.autosave_filename)

        # Настройка таймера автосохранения
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer)
        self.timer.start(self._interval_sec * 1000)

        print(f"Автосохранение включено: каждые {self._interval_sec} сек.")
        print(f"Директория сохранения: {self.save_directory}")
        print(f"Файл автосохранения: {self.autosave_filename}")

    def _get_default_save_dir(self):
        """Возвращает директорию по умолчанию для сохранения."""
        try:
            # Пытаемся использовать домашнюю директорию
            home_dir = str(Path.home())
            app_dir = os.path.join(home_dir, "PyQt_Painter_Drawings")
            Path(app_dir).mkdir(parents=True, exist_ok=True)
            return app_dir
        except Exception as e:
            print(f"Ошибка создания домашней директории: {e}")
            # Используем временную директорию как резервный вариант
            temp_dir = os.path.join(tempfile.gettempdir(), "PyQt_Painter_Drawings")
            Path(temp_dir).mkdir(parents=True, exist_ok=True)
            return temp_dir

    def _get_timestamp_filename(self):
        """Генерирует имя файла с временной меткой."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"drawing_{timestamp}.png"

    def _save_canvas_from_image(self, image_path, is_autosave=False):
        """Сохраняет изображение из временного пути в директорию сохранения.
        
        Args:
            image_path: Путь к временному изображению
            is_autosave: True = автосохранение (перезапись одного файла)
                        False = ручное сохранение (разные имена)
        """
        try:
            if not image_path:
                raise ValueError("Нет пути для сохранения")

            # ✅ РАЗНЫЕ ИМЕНА В ЗАВИСИМОСТИ ОТ ТИПА СОХРАНЕНИЯ
            if is_autosave:
                # Автосохранение: всегда один файл "autosave_backup.png"
                filepath = self.autosave_path
            else:
                # Ручное сохранение: разные имена с временной меткой
                filename = self._get_timestamp_filename()
                filepath = os.path.join(self.save_directory, filename)

            # Если это временный файл, копируем его
            if os.path.exists(image_path):
                # Загружаем и сохраняем изображение
                image = QImage(image_path)
                if image.isNull():
                    raise ValueError("Не удалось загрузить изображение из временного файла")
                
                if not image.save(filepath, "PNG"):
                    raise IOError(f"Ошибка сохранения файла: {filepath}")
                
                # Удаляем временный файл
                try:
                    os.remove(image_path)
                except:
                    pass
            else:
                # Если временный файл не существует, создаем пустое изображение
                image = QImage(1024, 768, QImage.Format_ARGB32)
                image.fill(Qt.white)
                if not image.save(filepath, "PNG"):
                    raise IOError(f"Ошибка сохранения файла: {filepath}")

            # Сохраняем метаданные
            self._save_metadata(filepath, 1024, 768)
            return filepath

        except Exception as e:
            raise Exception(f"Ошибка сохранения: {str(e)}")

    def _save_metadata(self, image_path, width, height):
        """Сохраняет метаданные о рисунке."""
        try:
            metadata = {
                "image_path": image_path,
                "width": width,
                "height": height,
                "created_at": datetime.now().isoformat(),
                "file_size": os.path.getsize(image_path) if os.path.exists(image_path) else 0
            }

            meta_filename = Path(image_path).stem + "_meta.json"
            meta_path = os.path.join(self.save_directory, meta_filename)
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения метаданных: {e}")

    @pyqtSlot()
    def _on_timer(self):
        """Обработчик таймера для автосохранения."""
        self.saveRequest.emit()

    @pyqtSlot(str)
    def set_canvas_data(self, canvas_path):
        """Устанавливает путь к данным canvas."""
        self.canvas_data = canvas_path

    @pyqtSlot(str, result=bool)
    def set_save_directory(self, directory_path):
        """Устанавливает новую директорию для сохранения."""
        try:
            new_dir = os.path.abspath(directory_path)
            Path(new_dir).mkdir(parents=True, exist_ok=True)

            # Проверяем права на запись
            test_file = os.path.join(new_dir, ".test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)

            self.save_directory = new_dir
            # ✅ ОБНОВЛЯЕМ ПУТЬ ДЛЯ АВТОСОХРАНЕНИЯ
            self.autosave_path = os.path.join(self.save_directory, self.autosave_filename)
            
            self.directoryChanged.emit(self.save_directory)
            print(f"Директория изменена на: {self.save_directory}")
            return True
        except Exception as e:
            error_msg = f"Ошибка установки директории: {str(e)}"
            self.saveError.emit(error_msg)
            print(error_msg)
            return False

    @pyqtSlot(str, result=str)
    def open_directory_dialog(self, current_dir):
        """Открывает диалог выбора директории."""
        try:
            parent = QMainWindow()
            parent.setWindowFlags(parent.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            parent.hide()

            directory = QFileDialog.getExistingDirectory(
                parent,
                "Выберите папку для сохранения",
                current_dir,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )

            return directory
        except Exception as e:
            print(f"Ошибка диалога выбора директории: {e}")
            return ""

    @pyqtSlot(result=str)
    def get_save_directory(self):
        """Возвращает текущую директорию сохранения."""
        return self.save_directory

    @pyqtSlot(result=str)
    def get_temp_path(self):
        """Возвращает путь к временной директории."""
        return tempfile.gettempdir()

    @pyqtSlot()
    def manual_save(self):
        """Ручное сохранение по запросу пользователя (разные имена файлов)."""
        try:
            if not self.canvas_data:
                raise ValueError("Нет данных canvas для сохранения")

            # ✅ is_autosave=False → разные имена с временной меткой
            filepath = self._save_canvas_from_image(self.canvas_data, is_autosave=False)

            # Отправляем только имя файла для отображения в интерфейсе
            filename = os.path.basename(filepath)
            self.saveCompleted.emit(filename)
            print(f"✓ Ручное сохранение успешно: {filepath}")
        except Exception as e:
            error_msg = str(e)
            self.saveError.emit(error_msg)
            print(f"✗ Ошибка ручного сохранения: {error_msg}")

    @pyqtSlot()
    def auto_save(self):
        """Автоматическое сохранение по таймеру (перезапись одного файла)."""
        try:
            if not self.canvas_data:
                print("Пропуск автосохранения: нет данных canvas")
                return

            # ✅ is_autosave=True → всегда один файл "autosave_backup.png"
            filepath = self._save_canvas_from_image(self.canvas_data, is_autosave=True)
            print(f"✓ Автосохранение успешно: {filepath}")
        except Exception as e:
            print(f"✗ Ошибка автосохранения: {str(e)}")

    # ====== МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ С QML ======

    @pyqtSlot()
    def start_autosave(self):
        """Для совместимости с QML - таймер уже запущен в конструкторе."""
        print("Автосохранение уже запущено")

    @pyqtSlot()
    def stop_autosave(self):
        """Останавливает таймер автосохранения."""
        if self.timer.isActive():
            self.timer.stop()
        print("Автосохранение остановлено")

    @pyqtSlot()
    def clear_canvas(self):
        """Очищает данные canvas (для совместимости)."""
        self.canvas_data = None
        print("Данные canvas очищены")


def resource_path(relative_path):
    """Получает абсолютный путь к ресурсу."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


if __name__ == '__main__':
    # Создаем экземпляр приложения
    app = QApplication(sys.argv)

    # Создаем backend
    interface = Interface()

    # Создаем QML движок
    engine = QQmlApplicationEngine()

    # Регистрируем backend в QML контексте
    engine.rootContext().setContextProperty("_backend", interface)

    # Загружаем QML файл
    qml_file = resource_path("mainWindow.qml")
    engine.load(QUrl.fromLocalFile(qml_file))

    # Проверка успешной загрузки
    if not engine.rootObjects():
        print(f"Ошибка загрузки QML файла: {qml_file}")
        sys.exit(-1)

    sys.exit(app.exec())