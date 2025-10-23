import sys
import requests
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QHBoxLayout, QListWidget, QGroupBox, QFormLayout
)
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont

# =============== Кеширование ===============
# Путь к файлу кэша курсов
CACHE_FILE = "rates_cache.json"

def save_rates_to_file(rates: dict):
    """Сохраняет курсы в JSON-файл."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(rates, f, ensure_ascii=False, indent=4)
    except Exception:
        pass  # Игнорируем ошибки записи (например, нет прав)

def load_rates_from_file() -> dict:
    """Загружает курсы из JSON-файла. Возвращает None при ошибке."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Проверяем наличие всех нужных ключей
                if all(k in data for k in ['usd_to_rub', 'eur_to_rub', 'usd_to_eur']):
                    return data
    except (json.JSONDecodeError, FileNotFoundError, KeyError, OSError):
        pass
    return None


# =============== ВАЛЮТЫ ===============
class Currency:
    def __init__(self, code: str, name: str):
        self.code = code.upper()
        self.name = name
        self.rate_to_rub = 1.0

    def set_rate_to_rub(self, rate: float):
        self.rate_to_rub = rate

    def to_rub(self, amount: float) -> float:
        return amount * self.rate_to_rub

    def from_rub(self, rub_amount: float) -> float:
        return rub_amount / self.rate_to_rub


class USD(Currency):
    def __init__(self):
        super().__init__("USD", "Доллар США (USD)")


class EUR(Currency):
    def __init__(self):
        super().__init__("EUR", "Евро (EUR)")


class RUB(Currency):
    def __init__(self):
        super().__init__("RUB", "Российский рубль (RUB)")
        self.rate_to_rub = 1.0


# =============== ПОТОК ЗАГРУЗКИ КУРСОВ ===============
class RateFetcher(QThread):
    rates_ready = pyqtSignal(dict)

    def run(self):
        try:
            response = requests.get("https://api.exchangerate-api.com/v4/latest/RUB", timeout=10)
            data = response.json()
            usd_to_rub = 1.0 / data['rates']['USD']
            eur_to_rub = 1.0 / data['rates']['EUR']
            usd_to_eur = usd_to_rub / eur_to_rub

            rates = {
                'usd_to_rub': usd_to_rub,
                'eur_to_rub': eur_to_rub,
                'usd_to_eur': usd_to_eur
            }

            # Сохраняем успешные курсы в файл
            save_rates_to_file(rates)
            self.rates_ready.emit(rates)

        except Exception as e:
            # Сначала пробуем загрузить из кэша
            cached_rates = load_rates_from_file()
            if cached_rates is not None:
                self.rates_ready.emit(cached_rates)
            else:
                # Если кэша нет — используем резервные значения
                fallback_rates = {
                    'usd_to_rub': 81.5,
                    'eur_to_rub': 94.0,
                    'usd_to_eur': 0.86
                }
                self.rates_ready.emit(fallback_rates)


# =============== ОСНОВНОЙ ИНТЕРФЕЙС ===============
class CurrencyConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("💱 Конвертер валют")
        self.setGeometry(200, 200, 600, 500)

        # Валюты
        self.rub = RUB()
        self.usd = USD()
        self.eur = EUR()

        # Поля ввода
        self.usd_input = QLineEdit()
        self.eur_input = QLineEdit()
        self.rub_input = QLineEdit()

        # История
        self.history_list = QListWidget()
        self.history_entries = []

        # Флаги обновления
        self.updating_usd = False
        self.updating_eur = False
        self.updating_rub = False

        self.init_ui()
        self.load_rates()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # === Заголовок ===
        title = QLabel("Конвертер валют")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # === Блок ввода ===
        input_group = QGroupBox("Введите сумму")
        input_layout = QFormLayout()
        input_layout.setSpacing(10)

        self.usd_input.setPlaceholderText("0.00")
        self.eur_input.setPlaceholderText("0.00")
        self.rub_input.setPlaceholderText("0.00")

        input_layout.addRow(self.usd.name + ":", self.usd_input)
        input_layout.addRow(self.eur.name + ":", self.eur_input)
        input_layout.addRow(self.rub.name + ":", self.rub_input)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # === Блок курсов ===
        self.rates_label = QLabel("Курс: загрузка...")
        self.rates_label.setFont(QFont("Arial", 10))
        self.rates_label.setStyleSheet("color: #2c3e50; background-color: #ecf0f1; padding: 8px; border-radius: 5px;")
        main_layout.addWidget(self.rates_label)

        # === История ===
        history_group = QGroupBox("История конвертаций")
        history_layout = QVBoxLayout()
        history_layout.addWidget(self.history_list)
        history_group.setLayout(history_layout)
        main_layout.addWidget(history_group)

        self.setLayout(main_layout)

        # Подключение сигналов
        self.usd_input.textChanged.connect(self.on_usd_changed)
        self.eur_input.textChanged.connect(self.on_eur_changed)
        self.rub_input.textChanged.connect(self.on_rub_changed)

    def load_rates(self):
        self.fetcher = RateFetcher()
        self.fetcher.rates_ready.connect(self.on_rates_loaded)
        self.fetcher.start()

    @pyqtSlot(dict)
    def on_rates_loaded(self, rates):
        self.usd.set_rate_to_rub(rates['usd_to_rub'])
        self.eur.set_rate_to_rub(rates['eur_to_rub'])

        # Обновляем отображение курсов
        self.rates_label.setText(
            f"1 USD = {rates['usd_to_rub']:.2f} RUB  |  "
            f"1 EUR = {rates['eur_to_rub']:.2f} RUB  |  "
            f"1 USD = {rates['usd_to_eur']:.3f} EUR"
        )

        # Пересчитываем, если есть данные
        self.update_from_existing()

    def update_from_existing(self):
        if self.usd_input.text():
            self.on_usd_changed(self.usd_input.text())
        elif self.eur_input.text():
            self.on_eur_changed(self.eur_input.text())
        elif self.rub_input.text():
            self.on_rub_changed(self.rub_input.text())

    def add_to_history(self, usd, eur, rub):
        entry = f"USD: {usd} → EUR: {eur} → RUB: {rub}"
        if entry not in self.history_entries:
            self.history_entries.append(entry)
            self.history_list.addItem(entry)
            # Ограничиваем историю 20 записями
            if self.history_list.count() > 20:
                self.history_list.takeItem(0)
                self.history_entries.pop(0)

    def format_number(self, num):
        return f"{num:,.2f}".replace(",", " ")

    def on_usd_changed(self, text):
        if self.updating_usd or not text:
            return
        try:
            usd = float(text)
            rub = self.usd.to_rub(usd)
            eur = self.eur.from_rub(rub)

            self.updating_eur = True
            self.eur_input.setText(self.format_number(eur))
            self.updating_eur = False

            self.updating_rub = True
            self.rub_input.setText(self.format_number(rub))
            self.updating_rub = False

            self.add_to_history(self.format_number(usd), self.format_number(eur), self.format_number(rub))

        except ValueError:
            self.clear_others(exclude='usd')

    def on_eur_changed(self, text):
        if self.updating_eur or not text:
            return
        try:
            eur = float(text)
            rub = self.eur.to_rub(eur)
            usd = self.usd.from_rub(rub)

            self.updating_usd = True
            self.usd_input.setText(self.format_number(usd))
            self.updating_usd = False

            self.updating_rub = True
            self.rub_input.setText(self.format_number(rub))
            self.updating_rub = False

            self.add_to_history(self.format_number(usd), self.format_number(eur), self.format_number(rub))

        except ValueError:
            self.clear_others(exclude='eur')

    def on_rub_changed(self, text):
        if self.updating_rub or not text:
            return
        try:
            rub = float(text)
            usd = self.usd.from_rub(rub)
            eur = self.eur.from_rub(rub)

            self.updating_usd = True
            self.usd_input.setText(self.format_number(usd))
            self.updating_usd = False

            self.updating_eur = True
            self.eur_input.setText(self.format_number(eur))
            self.updating_eur = False

            self.add_to_history(self.format_number(usd), self.format_number(eur), self.format_number(rub))

        except ValueError:
            self.clear_others(exclude='rub')

    def clear_others(self, exclude: str):
        fields = {'usd': self.usd_input, 'eur': self.eur_input, 'rub': self.rub_input}
        for key, field in fields.items():
            if key != exclude:
                field.blockSignals(True)
                field.clear()
                field.blockSignals(False)


# =============== ЗАПУСК ===============
if __name__ == "__main__":
    from PyQt5.QtCore import Qt  # импортируем Qt для выравнивания
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget {
            font-family: Arial;
            font-size: 12px;
        }
        QLineEdit {
            padding: 6px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
        }
        QListWidget {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 4px;
        }
        QGroupBox {
            font-weight: bold;
            margin-top: 15px;
            padding: 10px;
            border: 1px solid #bdc3c7;
            border-radius: 6px;
        }
    """)
    window = CurrencyConverter()
    window.show()
    sys.exit(app.exec_())