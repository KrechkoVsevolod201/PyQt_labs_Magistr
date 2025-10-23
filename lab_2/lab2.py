import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout
from PyQt5.QtCore import QObject, pyqtSignal, QThread, pyqtSlot

# Базовый класс валюты
class Currency:
    def __init__(self, code: str, name: str):
        self.code = code.upper()
        self.name = name
        self.rate_to_rub = 1.0  # по умолчанию — рубль базовая валюта

    def set_rate_to_rub(self, rate: float):
        self.rate_to_rub = rate

    def to_rub(self, amount: float) -> float:
        return amount * self.rate_to_rub

    def from_rub(self, rub_amount: float) -> float:
        return rub_amount / self.rate_to_rub


# Конкретные валюты
class USD(Currency):
    def __init__(self):
        super().__init__("USD", "Доллары (USD)")


class EUR(Currency):
    def __init__(self):
        super().__init__("EUR", "Евро (EUR)")


class RUB(Currency):
    def __init__(self):
        super().__init__("RUB", "Рубли (RUB)")
        self.rate_to_rub = 1.0  # базовая валюта


# Поток для загрузки курсов (чтобы не блокировать GUI)
class RateFetcher(QThread):
    rates_ready = pyqtSignal(dict)

    def run(self):
        try:
            # Используем бесплатный API без ключа
            response = requests.get("https://api.exchangerate-api.com/v4/latest/RUB", timeout=10)
            data = response.json()
            # Получаем курсы USD и EUR к RUB
            usd_to_rub = 1.0 / data['rates']['USD']  # потому что API даёт RUB -> USD, а нам нужно USD -> RUB
            eur_to_rub = 1.0 / data['rates']['EUR']

            rates = {
                'usd_to_rub': usd_to_rub,
                'eur_to_rub': eur_to_rub,
                'usd_to_eur': usd_to_rub / eur_to_rub  # USD -> RUB -> EUR
            }
            self.rates_ready.emit(rates)
        except Exception as e:
            # Если ошибка — используем резервные курсы
            self.rates_ready.emit({
                'usd_to_rub': 81.5,
                'eur_to_rub': 94.0,
                'usd_to_eur': 0.86
            })


class CurrencyConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Конвертер валют")
        self.setGeometry(300, 300, 400, 200)

        # Инициализация валют как объектов
        self.rub = RUB()
        self.usd = USD()
        self.eur = EUR()

        # Поля ввода
        self.usd_input = QLineEdit()
        self.eur_input = QLineEdit()
        self.rub_input = QLineEdit()

        # Флаги для предотвращения рекурсии
        self.updating_usd = False
        self.updating_eur = False
        self.updating_rub = False

        self.init_ui()
        self.load_rates()

    def init_ui(self):
        layout = QVBoxLayout()

        # USD
        usd_layout = QHBoxLayout()
        usd_layout.addWidget(QLabel(self.usd.name + ":"))
        usd_layout.addWidget(self.usd_input)
        layout.addLayout(usd_layout)

        # EUR
        eur_layout = QHBoxLayout()
        eur_layout.addWidget(QLabel(self.eur.name + ":"))
        eur_layout.addWidget(self.eur_input)
        layout.addLayout(eur_layout)

        # RUB
        rub_layout = QHBoxLayout()
        rub_layout.addWidget(QLabel(self.rub.name + ":"))
        rub_layout.addWidget(self.rub_input)
        layout.addLayout(rub_layout)

        self.setLayout(layout)

        # Подключаем сигналы
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
        # Обновляем отображение, если уже есть введённые значения
        self.update_from_existing()

    def update_from_existing(self):
        # Если уже что-то введено — пересчитываем
        if self.usd_input.text():
            self.on_usd_changed(self.usd_input.text())
        elif self.eur_input.text():
            self.on_eur_changed(self.eur_input.text())
        elif self.rub_input.text():
            self.on_rub_changed(self.rub_input.text())

    def on_usd_changed(self, text):
        if self.updating_usd:
            return
        try:
            usd = float(text)
            rub = self.usd.to_rub(usd)
            eur = self.eur.from_rub(rub)

            self.updating_eur = True
            self.eur_input.setText(f"{eur:.2f}")
            self.updating_eur = False

            self.updating_rub = True
            self.rub_input.setText(f"{rub:.2f}")
            self.updating_rub = False

        except ValueError:
            self.clear_others(exclude='usd')

    def on_eur_changed(self, text):
        if self.updating_eur:
            return
        try:
            eur = float(text)
            rub = self.eur.to_rub(eur)
            usd = self.usd.from_rub(rub)

            self.updating_usd = True
            self.usd_input.setText(f"{usd:.2f}")
            self.updating_usd = False

            self.updating_rub = True
            self.rub_input.setText(f"{rub:.2f}")
            self.updating_rub = False

        except ValueError:
            self.clear_others(exclude='eur')

    def on_rub_changed(self, text):
        if self.updating_rub:
            return
        try:
            rub = float(text)
            usd = self.usd.from_rub(rub)
            eur = self.eur.from_rub(rub)

            self.updating_usd = True
            self.usd_input.setText(f"{usd:.2f}")
            self.updating_usd = False

            self.updating_eur = True
            self.eur_input.setText(f"{eur:.2f}")
            self.updating_eur = False

        except ValueError:
            self.clear_others(exclude='rub')

    def clear_others(self, exclude: str):
        if exclude != 'usd':
            self.updating_usd = True
            self.usd_input.clear()
            self.updating_usd = False
        if exclude != 'eur':
            self.updating_eur = True
            self.eur_input.clear()
            self.updating_eur = False
        if exclude != 'rub':
            self.updating_rub = True
            self.rub_input.clear()
            self.updating_rub = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CurrencyConverter()
    window.show()
    sys.exit(app.exec_())