#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import sqlite3
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QComboBox, QTabWidget, 
                            QTableWidget, QTableWidgetItem, QMenuBar, QMenu, 
                            QAction, QMessageBox, QStatusBar, QLabel, QHeaderView,
                            QSplitter, QTextEdit, QGroupBox, QGridLayout, QLineEdit,
                            QInputDialog, QFormLayout, QSpinBox, QDateEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib
    matplotlib.use('Qt5Agg')
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class DatabaseWorker(QThread):
    """Рабочий поток для выполнения SQL запросов"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, query, params=None):
        super().__init__()
        self.query = query
        self.params = params or []
        
    def run(self):
        try:
            # Подключение к базе данных SQLite
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            cursor.execute(self.query, self.params)
            result = cursor.fetchall()
            
            conn.close()
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


class DatabaseManager:
    """Класс для управления базой данных"""
    
    @staticmethod
    def init_database():
        """Инициализация базы данных и создание тестовых данных"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Создание таблицы
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    position TEXT,
                    department TEXT,
                    salary REAL,
                    hire_date TEXT
                )
            ''')
            
            # Добавление тестовых данных
            cursor.execute('SELECT COUNT(*) FROM employees')
            if cursor.fetchone()[0] == 0:
                test_data = [
                    ('Иванов Иван', 'Разработчик', 'IT', 85000, '2023-01-15'),
                    ('Петров Петр', 'Менеджер', 'Sales', 75000, '2022-03-20'),
                    ('Сидорова Анна', 'Аналитик', 'IT', 90000, '2023-06-10'),
                    ('Козлов Дмитрий', 'Дизайнер', 'Marketing', 70000, '2023-02-28'),
                    ('Новикова Елена', 'HR-менеджер', 'HR', 65000, '2022-11-15'),
                    ('Морозов Алексей', 'Разработчик', 'IT', 88000, '2023-04-05'),
                    ('Волкова Ольга', 'Бухгалтер', 'Finance', 72000, '2022-09-12'),
                    ('Лебедев Игорь', 'Тестировщик', 'IT', 68000, '2023-07-22'),
                    ('Соколов Максим', 'Маркетолог', 'Marketing', 73000, '2023-01-30'),
                    ('Зайцева Татьяна', 'Юрист', 'Legal', 95000, '2022-12-08')
                ]
                
                cursor.executemany(
                    'INSERT INTO employees (name, position, department, salary, hire_date) VALUES (?, ?, ?, ?, ?)',
                    test_data
                )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Ошибка инициализации БД: {e}")
            return False


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Database Application")
        self.setGeometry(100, 100, 1200, 800)
        
        # Инициализация базы данных
        DatabaseManager.init_database()
        
        # Настройка интерфейса
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # Подключение сигналов
        self.connect_signals()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        
        # Верхняя панель с кнопками и ComboBox
        top_panel = self.create_top_panel()
        main_layout.addWidget(top_panel)
        
        # QTabWidget
        self.tab_widget = QTabWidget()
        self.setup_tabs()
        main_layout.addWidget(self.tab_widget)
        
    def create_top_panel(self):
        """Создание верхней панели управления"""
        group = QGroupBox("Панель управления")
        layout = QHBoxLayout(group)
        
        # Кнопки для SQL запросов
        self.bt1 = QPushButton("📊 Показать данные")
        self.bt2 = QPushButton("📈 Статистика по отделам")
        self.bt3 = QPushButton("💰 Сотрудники с высокой зарплатой")
        
        # ComboBox для выбора колонок
        self.combo_columns = QComboBox()
        self.combo_columns.addItems([
            "Все поля",
            "Имя",
            "Должность", 
            "Отдел",
            "Зарплата",
            "Дата найма"
        ])
        self.combo_columns.setCurrentText("Все поля")
        
        # Добавление элементов в layout
        layout.addWidget(self.bt1)
        layout.addWidget(self.bt2)
        layout.addWidget(self.bt3)
        layout.addWidget(QLabel("Выберите поле:"))
        layout.addWidget(self.combo_columns)
        layout.addStretch()
        
        return group
        
    def setup_tabs(self):
        """Настройка вкладок"""
        # Tab 1 - Таблица сотрудников
        self.tab1 = QWidget()
        self.setup_tab1()
        self.tab_widget.addTab(self.tab1, "📋 Сотрудники")
        
        # Tab 2 - Статистика
        self.tab2 = QWidget()
        self.setup_tab2()
        self.tab_widget.addTab(self.tab2, "📊 Статистика")
        
        # Tab 3 - Фильтры
        self.tab3 = QWidget()
        self.setup_tab3()
        self.tab_widget.addTab(self.tab3, "🔍 Поиск и фильтры")
        
        # Tab 4 - Графики
        self.tab4 = QWidget()
        self.setup_tab4()
        self.tab_widget.addTab(self.tab4, "📈 Графики")
        
        # Tab 5 - Отчеты
        self.tab5 = QWidget()
        self.setup_tab5()
        self.tab_widget.addTab(self.tab5, "📄 Отчеты")
        
        # Tab 6 - Редактирование
        self.tab6 = QWidget()
        self.setup_tab6()
        self.tab_widget.addTab(self.tab6, "✏️ Редактирование")
        
    def setup_tab1(self):
        """Настройка Tab1 - Таблица сотрудников"""
        layout = QVBoxLayout(self.tab1)
        
        # Таблица для отображения данных
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels([
            "ID", "Имя", "Должность", "Отдел", "Зарплата", "Дата найма"
        ])
        
        # Настройка заголовков
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.table_widget)
        
    def setup_tab2(self):
        """Настройка Tab2 - Статистика"""
        layout = QVBoxLayout(self.tab2)
        
        # Текстовое поле для статистики
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont("Courier", 10))
        
        layout.addWidget(QLabel("Статистика по базе данных:"))
        layout.addWidget(self.stats_text)
        
    def setup_tab3(self):
        """Настройка Tab3 - Фильтры"""
        layout = QGridLayout(self.tab3)
        
        # Поля для фильтрации
        layout.addWidget(QLabel("Фильтр по имени:"), 0, 0)
        self.name_filter = QTextEdit()
        self.name_filter.setMaximumHeight(30)
        layout.addWidget(self.name_filter, 0, 1)
        
        layout.addWidget(QLabel("Фильтр по отделу:"), 1, 0)
        self.dept_filter = QTextEdit()
        self.dept_filter.setMaximumHeight(30)
        layout.addWidget(self.dept_filter, 1, 1)
        
        layout.addWidget(QLabel("Минимальная зарплата:"), 2, 0)
        self.min_salary = QTextEdit()
        self.min_salary.setMaximumHeight(30)
        layout.addWidget(self.min_salary, 2, 1)
        
        # Кнопка применения фильтров
        apply_filter_btn = QPushButton("Применить фильтры")
        apply_filter_btn.clicked.connect(self.apply_filters)
        layout.addWidget(apply_filter_btn, 3, 0, 1, 2)
        
        # Таблица для отфильтрованных результатов
        self.filter_table = QTableWidget()
        self.filter_table.setColumnCount(6)
        self.filter_table.setHorizontalHeaderLabels([
            "ID", "Имя", "Должность", "Отдел", "Зарплата", "Дата найма"
        ])
        header = self.filter_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.filter_table, 4, 0, 1, 2)
        
    def setup_tab5(self):
        """Настройка Tab5 - Отчеты"""
        layout = QVBoxLayout(self.tab5)
        
        # Область для отчетов
        self.reports_text = QTextEdit()
        self.reports_text.setReadOnly(True)
        self.reports_text.setFont(QFont("Courier", 10))
        
        # Кнопки генерации отчетов
        btn_layout = QHBoxLayout()
        
        report1_btn = QPushButton("Отчет по отделам")
        report1_btn.clicked.connect(self.generate_department_report)
        
        report2_btn = QPushButton("Отчет по зарплатам")
        report2_btn.clicked.connect(self.generate_salary_report)
        
        btn_layout.addWidget(report1_btn)
        btn_layout.addWidget(report2_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        layout.addWidget(QLabel("Сгенерированные отчеты:"))
        layout.addWidget(self.reports_text)
        
    def setup_tab4(self):
        """Настройка Tab4 - Графики"""
        layout = QVBoxLayout(self.tab4)
        
        if not MATPLOTLIB_AVAILABLE:
            # Сообщение если matplotlib не установлен
            no_charts_text = QTextEdit()
            no_charts_text.setReadOnly(True)
            no_charts_text.setPlainText("Для отображения графиков необходимо установить matplotlib:\n\n"
                                      "pip install matplotlib\n\n"
                                      "После установки перезапустите приложение.")
            layout.addWidget(no_charts_text)
            return
        
        # Создаем виджет для графиков
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        
        # Кнопки для разных графиков
        btn_layout = QHBoxLayout()
        
        btn_salary_chart = QPushButton("📊 Зарплаты по отделам")
        btn_salary_chart.clicked.connect(self.show_salary_chart)
        
        btn_pie_chart = QPushButton("🥧 Распределение по отделам")
        btn_pie_chart.clicked.connect(self.show_department_pie_chart)
        
        btn_hire_chart = QPushButton("📅 Динамика найма")
        btn_hire_chart.clicked.connect(self.show_hire_chart)
        
        btn_layout.addWidget(btn_salary_chart)
        btn_layout.addWidget(btn_pie_chart)
        btn_layout.addWidget(btn_hire_chart)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.canvas)
        
    def setup_tab6(self):
        """Настройка Tab6 - Редактирование"""
        layout = QVBoxLayout(self.tab6)
        
        # Форма для добавления нового сотрудника
        form_group = QGroupBox("➕ Добавить нового сотрудника")
        form_layout = QFormLayout(form_group)
        
        self.edit_name = QLineEdit()
        self.edit_position = QLineEdit()
        self.edit_department = QLineEdit()
        self.edit_salary = QLineEdit()
        self.edit_hire_date = QLineEdit()
        
        form_layout.addRow("Имя:", self.edit_name)
        form_layout.addRow("Должность:", self.edit_position)
        form_layout.addRow("Отдел:", self.edit_department)
        form_layout.addRow("Зарплата:", self.edit_salary)
        form_layout.addRow("Дата найма (ГГГГ-ММ-ДД):", self.edit_hire_date)
        
        # Кнопки для формы
        form_btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Добавить")
        add_btn.clicked.connect(self.add_employee)
        
        clear_form_btn = QPushButton("🗑️ Очистить форму")
        clear_form_btn.clicked.connect(self.clear_edit_form)
        
        form_btn_layout.addWidget(add_btn)
        form_btn_layout.addWidget(clear_form_btn)
        form_btn_layout.addStretch()
        
        form_layout.addRow(form_btn_layout)
        
        # Таблица для редактирования
        table_group = QGroupBox("📋 Редактирование существующих данных")
        table_layout = QVBoxLayout(table_group)
        
        self.edit_table = QTableWidget()
        self.edit_table.setColumnCount(7)  # +1 для кнопки удаления
        self.edit_table.setHorizontalHeaderLabels([
            "ID", "Имя", "Должность", "Отдел", "Зарплата", "Дата найма", "Действия"
        ])
        
        header = self.edit_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Кнопки для таблицы
        table_btn_layout = QHBoxLayout()
        
        refresh_table_btn = QPushButton("🔄 Обновить таблицу")
        refresh_table_btn.clicked.connect(self.refresh_edit_table)
        
        delete_selected_btn = QPushButton("🗑️ Удалить выбранное")
        delete_selected_btn.clicked.connect(self.delete_selected_employee)
        
        table_btn_layout.addWidget(refresh_table_btn)
        table_btn_layout.addWidget(delete_selected_btn)
        table_btn_layout.addStretch()
        
        table_layout.addLayout(table_btn_layout)
        table_layout.addWidget(self.edit_table)
        
        # Добавляем все на основной layout
        layout.addWidget(form_group)
        layout.addWidget(table_group)
        
        # Загружаем данные в таблицу редактирования
        self.refresh_edit_table()
        
    def setup_menu(self):
        """Настройка меню"""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu('Файл')
        
        exit_action = QAction('Выход', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню База данных
        db_menu = menubar.addMenu('База данных')
        
        refresh_action = QAction('Обновить данные', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_data)
        db_menu.addAction(refresh_action)
        
        # Меню Справка
        help_menu = menubar.addMenu('Справка')
        
        about_action = QAction('О программе', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_status_bar(self):
        """Настройка статусбара"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")
        
    def connect_signals(self):
        """Подключение сигналов к слотам"""
        self.bt1.clicked.connect(self.execute_query1)
        self.bt2.clicked.connect(self.execute_query2)
        self.bt3.clicked.connect(self.execute_query3)
        self.combo_columns.currentTextChanged.connect(self.on_column_changed)
        
    def execute_query1(self):
        """Выполнение первого запроса - SELECT Column"""
        self.status_bar.showMessage("Выполнение запроса 1...")
        column = self.combo_columns.currentText()
        
        if column == "Все поля":
            query = "SELECT * FROM employees"
        elif column == "Имя":
            query = "SELECT name FROM employees"
        elif column == "Должность":
            query = "SELECT position FROM employees"
        elif column == "Отдел":
            query = "SELECT department FROM employees"
        elif column == "Зарплата":
            query = "SELECT salary FROM employees"
        elif column == "Дата найма":
            query = "SELECT hire_date FROM employees"
        else:
            query = "SELECT * FROM employees"
            
        self.worker = DatabaseWorker(query)
        self.worker.finished.connect(self.on_query1_finished)
        self.worker.error.connect(self.on_query_error)
        self.worker.start()
        
    def execute_query2(self):
        """Выполнение второго запроса"""
        self.status_bar.showMessage("Выполнение запроса 2...")
        query = """
        SELECT department, COUNT(*) as count, AVG(salary) as avg_salary 
        FROM employees 
        GROUP BY department
        """
        
        self.worker = DatabaseWorker(query)
        self.worker.finished.connect(self.on_query2_finished)
        self.worker.error.connect(self.on_query_error)
        self.worker.start()
        
    def execute_query3(self):
        """Выполнение третьего запроса"""
        self.status_bar.showMessage("Выполнение запроса 3...")
        query = """
        SELECT name, position, salary 
        FROM employees 
        WHERE salary > (SELECT AVG(salary) FROM employees)
        ORDER BY salary DESC
        """
        
        self.worker = DatabaseWorker(query)
        self.worker.finished.connect(self.on_query3_finished)
        self.worker.error.connect(self.on_query_error)
        self.worker.start()
        
    def on_query1_finished(self, result):
        """Обработка результата запроса 1"""
        # Очищаем старые данные перед отображением новых
        self.table_widget.clearContents()
        self.table_widget.setRowCount(0)
        
        # Настраиваем колонки в зависимости от запроса
        column = self.combo_columns.currentText()
        if column == "Все поля":
            self.table_widget.setColumnCount(6)
            self.table_widget.setHorizontalHeaderLabels([
                "ID", "Имя", "Должность", "Отдел", "Зарплата", "Дата найма"
            ])
        else:
            self.table_widget.setColumnCount(1)
            self.table_widget.setHorizontalHeaderLabels([column])
        
        self.display_data_in_table(result)
        self.status_bar.showMessage(f"Данные обновлены. Найдено записей: {len(result)}")
        
    def on_query2_finished(self, result):
        """Обработка результата запроса 2"""
        stats_text = "Статистика по отделам:\n" + "="*50 + "\n"
        for row in result:
            stats_text += f"Отдел: {row[0]}\n"
            stats_text += f"  Сотрудников: {row[1]}\n"
            stats_text += f"  Средняя зарплата: {row[2]:.2f} руб.\n"
            stats_text += "-"*30 + "\n"
            
        self.stats_text.setText(stats_text)
        self.tab_widget.setCurrentIndex(1)  # Переключиться на вкладку статистики
        self.status_bar.showMessage(f"Запрос 2 выполнен. Отделов: {len(result)}")
        
    def on_query3_finished(self, result):
        """Обработка результата запроса 3"""
        report_text = "Сотрудники с зарплатой выше средней:\n" + "="*50 + "\n"
        for row in result:
            report_text += f"{row[0]} - {row[1]} - {row[2]:.2f} руб.\n"
            
        self.reports_text.setText(report_text)
        self.tab_widget.setCurrentIndex(4)  # Переключиться на вкладку отчетов
        self.status_bar.showMessage(f"Запрос 3 выполнен. Найдено: {len(result)}")
        
    def on_query_error(self, error_msg):
        """Обработка ошибок запросов"""
        QMessageBox.critical(self, "Ошибка базы данных", f"Произошла ошибка:\n{error_msg}")
        self.status_bar.showMessage("Ошибка выполнения запроса")
        
    def display_data_in_table(self, data):
        """Отображение данных в таблице"""
        if not data:
            self.table_widget.setRowCount(0)
            return
            
        self.table_widget.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.table_widget.setItem(row_idx, col_idx, item)
                
        # Настраиваем заголовки
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
                
        self.tab_widget.setCurrentIndex(0)  # Переключиться на вкладку с таблицей
        
    def on_column_changed(self, column):
        """Обработка изменения выбора колонки"""
        self.status_bar.showMessage(f"Выбрана колонка: {column}")
        
    def apply_filters(self):
        """Применение фильтров"""
        self.status_bar.showMessage("Применение фильтров...")
        
        name_filter = self.name_filter.toPlainText().strip()
        dept_filter = self.dept_filter.toPlainText().strip()
        min_salary = self.min_salary.toPlainText().strip()
        
        query = "SELECT * FROM employees WHERE 1=1"
        params = []
        
        if name_filter:
            query += " AND name LIKE ?"
            params.append(f"%{name_filter}%")
            
        if dept_filter:
            query += " AND department LIKE ?"
            params.append(f"%{dept_filter}%")
            
        if min_salary:
            try:
                salary = float(min_salary)
                query += " AND salary >= ?"
                params.append(salary)
            except ValueError:
                pass
                
        self.worker = DatabaseWorker(query, params)
        self.worker.finished.connect(self.on_filter_finished)
        self.worker.error.connect(self.on_query_error)
        self.worker.start()
        
    def on_filter_finished(self, result):
        """Обработка результата фильтрации"""
        self.filter_table.setRowCount(len(result))
        
        for row_idx, row_data in enumerate(result):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.filter_table.setItem(row_idx, col_idx, item)
                
        self.status_bar.showMessage(f"Фильтр применен. Найдено записей: {len(result)}")
        
    def generate_department_report(self):
        """Генерация отчета по отделам"""
        query = """
        SELECT department, 
               COUNT(*) as total_employees,
               MIN(salary) as min_salary,
               MAX(salary) as max_salary,
               AVG(salary) as avg_salary
        FROM employees 
        GROUP BY department
        ORDER BY avg_salary DESC
        """
        
        self.worker = DatabaseWorker(query)
        self.worker.finished.connect(self.on_department_report_finished)
        self.worker.error.connect(self.on_query_error)
        self.worker.start()
        
    def on_department_report_finished(self, result):
        """Обработка отчета по отделам"""
        report = "ОТЧЕТ ПО ОТДЕЛАМ\n" + "="*60 + "\n\n"
        
        for row in result:
            report += f"ОТДЕЛ: {row[0]}\n"
            report += f"  Всего сотрудников: {row[1]}\n"
            report += f"  Минимальная зарплата: {row[2]:.2f} руб.\n"
            report += f"  Максимальная зарплата: {row[3]:.2f} руб.\n"
            report += f"  Средняя зарплата: {row[4]:.2f} руб.\n"
            report += "-"*40 + "\n"
            
        self.reports_text.setText(report)
        self.status_bar.showMessage("Отчет по отделам сгенерирован")
        
    def generate_salary_report(self):
        """Генерация отчета по зарплатам"""
        query = """
        SELECT name, position, department, salary,
               CASE 
                   WHEN salary < 70000 THEN 'Низкая'
                   WHEN salary < 85000 THEN 'Средняя'
                   ELSE 'Высокая'
               END as salary_category
        FROM employees 
        ORDER BY salary DESC
        """
        
        self.worker = DatabaseWorker(query)
        self.worker.finished.connect(self.on_salary_report_finished)
        self.worker.error.connect(self.on_query_error)
        self.worker.start()
        
    def on_salary_report_finished(self, result):
        """Обработка отчета по зарплатам"""
        report = "ОТЧЕТ ПО ЗАРПЛАТАМ\n" + "="*60 + "\n\n"
        
        high_count = sum(1 for row in result if row[4] == 'Высокая')
        medium_count = sum(1 for row in result if row[4] == 'Средняя')
        low_count = sum(1 for row in result if row[4] == 'Низкая')
        
        report += f"Распределение по категориям:\n"
        report += f"  Высокая зарплата: {high_count} сотрудников\n"
        report += f"  Средняя зарплата: {medium_count} сотрудников\n"
        report += f"  Низкая зарплата: {low_count} сотрудников\n"
        report += "\n" + "="*60 + "\n\n"
        report += "Детальная информация:\n"
        report += "-"*60 + "\n"
        
        for row in result:
            report += f"{row[0]} ({row[1]}) - {row[2]} - {row[3]:.2f} руб. [{row[4]}]\n"
            
        self.reports_text.setText(report)
        self.status_bar.showMessage("Отчет по зарплатам сгенерирован")
        
    def refresh_data(self):
        """Обновление всех данных"""
        self.status_bar.showMessage("Обновление данных...")
        self.execute_query1()
        
    def show_about(self):
        """Показать информацию о программе"""
        QMessageBox.about(self, "О программе", 
                         "PyQt5 Database Application\n\n"
                         "Лабораторная работа по базам данных\n"
                         "Использованы технологии:\n"
                         "- Python 3\n"
                         "- PyQt5\n"
                         "- SQLite\n"
                         "- Многопоточность")
        
    def closeEvent(self, event):
        """Обработка закрытия приложения"""
        reply = QMessageBox.question(self, 'Подтверждение', 
                                   'Вы уверены, что хотите выйти?',
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    # Функции для графиков
    def show_salary_chart(self):
        """Показать график зарплат по отделам"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.status_bar.showMessage("Создание графика зарплат...")
        
        query = """
        SELECT department, AVG(salary) as avg_salary, COUNT(*) as count
        FROM employees 
        GROUP BY department
        ORDER BY avg_salary DESC
        """
        
        self.worker = DatabaseWorker(query)
        self.worker.finished.connect(self.on_salary_chart_data_ready)
        self.worker.error.connect(self.on_query_error)
        self.worker.start()
        
    def on_salary_chart_data_ready(self, data):
        """Обработка данных для графика зарплат"""
        if not data:
            return
            
        departments = [row[0] for row in data]
        avg_salaries = [row[1] for row in data]
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        bars = ax.bar(departments, avg_salaries, color='skyblue', alpha=0.7)
        ax.set_xlabel('Отдел')
        ax.set_ylabel('Средняя зарплата (руб.)')
        ax.set_title('Средняя зарплата по отделам')
        
        # Добавляем значения на столбцы
        for bar, salary in zip(bars, avg_salaries):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1000,
                   f'{salary:.0f}', ha='center', va='bottom')
        
        # Поворачиваем подписи отделов для лучшей читаемости
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        self.tab_widget.setCurrentIndex(3)  # Переключиться на вкладку графиков
        self.status_bar.showMessage("График зарплат построен")
        
    def show_department_pie_chart(self):
        """Показать круговую диаграмму распределения по отделам"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.status_bar.showMessage("Создание диаграммы распределения...")
        
        query = """
        SELECT department, COUNT(*) as count
        FROM employees 
        GROUP BY department
        ORDER BY count DESC
        """
        
        self.worker = DatabaseWorker(query)
        self.worker.finished.connect(self.on_pie_chart_data_ready)
        self.worker.error.connect(self.on_query_error)
        self.worker.start()
        
    def on_pie_chart_data_ready(self, data):
        """Обработка данных для круговой диаграммы"""
        if not data:
            return
            
        departments = [row[0] for row in data]
        counts = [row[1] for row in data]
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        colors = plt.cm.Set3(range(len(departments)))
        wedges, texts, autotexts = ax.pie(counts, labels=departments, autopct='%1.1f%%',
                                          colors=colors, startangle=90)
        
        ax.set_title('Распределение сотрудников по отделам')
        
        # Улучшаем читаемость текста
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            
        self.figure.tight_layout()
        self.canvas.draw()
        
        self.tab_widget.setCurrentIndex(3)  # Переключиться на вкладку графиков
        self.status_bar.showMessage("Диаграмма распределения построена")
        
    def show_hire_chart(self):
        """Показать график динамики найма"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.status_bar.showMessage("Создание графика динамики найма...")
        
        query = """
        SELECT hire_date, COUNT(*) as count
        FROM employees 
        GROUP BY hire_date
        ORDER BY hire_date
        """
        
        self.worker = DatabaseWorker(query)
        self.worker.finished.connect(self.on_hire_chart_data_ready)
        self.worker.error.connect(self.on_query_error)
        self.worker.start()
        
    def on_hire_chart_data_ready(self, data):
        """Обработка данных для графика динамики найма"""
        if not data:
            return
            
        dates = [row[0] for row in data]
        counts = [row[1] for row in data]
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        ax.plot(dates, counts, marker='o', linewidth=2, markersize=8, color='green')
        ax.set_xlabel('Дата найма')
        ax.set_ylabel('Количество сотрудников')
        ax.set_title('Динамика найма сотрудников')
        
        # Поворачиваем подписи дат
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Добавляем сетку
        ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        self.tab_widget.setCurrentIndex(3)  # Переключиться на вкладку графиков
        self.status_bar.showMessage("График динамики найма построен")

    # Функции для редактирования
    def add_employee(self):
        """Добавление нового сотрудника"""
        name = self.edit_name.text().strip()
        position = self.edit_position.text().strip()
        department = self.edit_department.text().strip()
        salary = self.edit_salary.text().strip()
        hire_date = self.edit_hire_date.text().strip()
        
        if not all([name, position, department, salary, hire_date]):
            QMessageBox.warning(self, "Предупреждение", "Заполните все поля!")
            return
            
        try:
            salary_val = float(salary)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Зарплата должна быть числом!")
            return
            
        query = """
        INSERT INTO employees (name, position, department, salary, hire_date)
        VALUES (?, ?, ?, ?, ?)
        """
        
        self.worker = DatabaseWorker(query, [name, position, department, salary_val, hire_date])
        self.worker.finished.connect(self.on_employee_added)
        self.worker.error.connect(self.on_query_error)
        self.worker.start()
        
    def on_employee_added(self, result):
        """Обработка добавления сотрудника"""
        QMessageBox.information(self, "Успех", "Сотрудник успешно добавлен!")
        self.clear_edit_form()
        self.refresh_edit_table()
        self.refresh_data()  # Обновляем основную таблицу
        self.status_bar.showMessage("Сотрудник добавлен")
        
    def clear_edit_form(self):
        """Очистка формы редактирования"""
        self.edit_name.clear()
        self.edit_position.clear()
        self.edit_department.clear()
        self.edit_salary.clear()
        self.edit_hire_date.clear()
        
    def refresh_edit_table(self):
        """Обновление таблицы редактирования"""
        query = "SELECT * FROM employees ORDER BY id"
        
        self.worker = DatabaseWorker(query)
        self.worker.finished.connect(self.on_edit_table_data_ready)
        self.worker.error.connect(self.on_query_error)
        self.worker.start()
        
    def on_edit_table_data_ready(self, data):
        """Обработка данных для таблицы редактирования"""
        self.edit_table.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                if col_idx < 6:  # Первые 6 колонок - данные
                    item = QTableWidgetItem(str(cell_data))
                    self.edit_table.setItem(row_idx, col_idx, item)
                    
            # Добавляем кнопку удаления в последнюю колонку
            delete_btn = QPushButton("🗑️ Удалить")
            delete_btn.clicked.connect(lambda checked, id=row_data[0]: self.delete_employee(id))
            self.edit_table.setCellWidget(row_idx, 6, delete_btn)
            
        self.status_bar.showMessage("Таблица редактирования обновлена")
        
    def delete_employee(self, employee_id):
        """Удаление сотрудника по ID"""
        reply = QMessageBox.question(self, 'Подтверждение', 
                                   f'Вы уверены, что хотите удалить сотрудника с ID {employee_id}?',
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            query = "DELETE FROM employees WHERE id = ?"
            self.worker = DatabaseWorker(query, [employee_id])
            self.worker.finished.connect(self.on_employee_deleted)
            self.worker.error.connect(self.on_query_error)
            self.worker.start()
            
    def on_employee_deleted(self, result):
        """Обработка удаления сотрудника"""
        QMessageBox.information(self, "Успех", "Сотрудник удален!")
        self.refresh_edit_table()
        self.refresh_data()  # Обновляем основную таблицу
        self.status_bar.showMessage("Сотрудник удален")
        
    def delete_selected_employee(self):
        """Удаление выбранного сотрудника"""
        current_row = self.edit_table.currentRow()
        if current_row >= 0:
            id_item = self.edit_table.item(current_row, 0)
            if id_item:
                employee_id = int(id_item.text())
                self.delete_employee(employee_id)
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите сотрудника для удаления!")


def main():
    """Главная функция"""
    app = QApplication(sys.argv)
    
    # Установка стиля приложения
    app.setStyle('Fusion')
    
    # Создание и отображение главного окна
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()