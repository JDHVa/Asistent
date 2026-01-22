"""
Estilos y temas para la interfaz PySide6.
Tema: 'Fluent Dark' con toques modernos.
"""
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt

def apply_dark_theme(app):
    """Aplica un tema oscuro moderno a la aplicación"""
    dark_palette = QPalette()
    
    # Colores base
    dark_palette.setColor(QPalette.Window, QColor(32, 33, 36))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(41, 42, 45))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 54, 58))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(32, 33, 36))
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 54, 58))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    
    # Estados deshabilitados
    dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    
    app.setPalette(dark_palette)

def get_stylesheet():
    """Retorna el QSS para el tema oscuro"""
    return """
    /* ===== VENTANA PRINCIPAL ===== */
    QMainWindow {
        background-color: #202124;
        border: 1px solid #3c4043;
    }
    
    /* ===== BARRA DE TÍTULO PERSONALIZADA ===== */
    #TitleBar {
        background-color: #2b2d30;
        border-bottom: 1px solid #3c4043;
        padding: 5px;
    }
    
    #TitleLabel {
        font-size: 14px;
        font-weight: bold;
        color: #e8eaed;
        padding-left: 10px;
    }
    
    /* ===== PESTAÑAS ===== */
    QTabWidget::pane {
        border: 1px solid #3c4043;
        border-radius: 8px;
        background-color: #292a2d;
        margin-top: 5px;
    }
    
    QTabBar::tab {
        background-color: #35363a;
        border: 1px solid #3c4043;
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 10px 20px;
        margin-right: 2px;
        font-weight: 600;
        color: #9aa0a6;
        min-width: 100px;
    }
    
    QTabBar::tab:selected {
        background-color: #292a2d;
        color: #e8eaed;
        border-bottom: 2px solid #4285f4;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #3c4043;
        color: #e8eaed;
    }
    
    /* ===== BOTONES ===== */
    QPushButton {
        background-color: #4285f4;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 16px;
        font-weight: 600;
        font-size: 13px;
        min-height: 36px;
    }
    
    QPushButton:hover {
        background-color: #3367d6;
    }
    
    QPushButton:pressed {
        background-color: #2a56c6;
    }
    
    QPushButton:disabled {
        background-color: #5f6368;
        color: #9aa0a6;
    }
    
    /* Botones secundarios */
    QPushButton.secondary {
        background-color: #5f6368;
    }
    
    QPushButton.secondary:hover {
        background-color: #3c4043;
    }
    
    /* Botones de éxito */
    QPushButton.success {
        background-color: #34a853;
    }
    
    QPushButton.success:hover {
        background-color: #2d9249;
    }
    
    /* Botones de peligro */
    QPushButton.danger {
        background-color: #ea4335;
    }
    
    QPushButton.danger:hover {
        background-color: #d23d30;
    }
    
    /* ===== CAMPOS DE ENTRADA ===== */
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #292a2d;
        border: 1px solid #5f6368;
        border-radius: 6px;
        padding: 10px;
        color: #e8eaed;
        font-size: 14px;
        selection-background-color: #4285f4;
        selection-color: white;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 2px solid #4285f4;
        background-color: #2d2e31;
    }
    
    QLineEdit:disabled, QTextEdit:disabled {
        background-color: #3c4043;
        color: #9aa0a6;
    }
    
    /* ===== LISTAS Y TABLAS ===== */
    QListWidget, QTreeView, QTableView {
        background-color: #292a2d;
        border: 1px solid #3c4043;
        border-radius: 6px;
        color: #e8eaed;
        outline: none;
        font-size: 14px;
        alternate-background-color: #2d2e31;
    }
    
    QListWidget::item:selected, QTreeView::item:selected, QTableView::item:selected {
        background-color: #4285f4;
        color: white;
    }
    
    QListWidget::item:hover, QTreeView::item:hover {
        background-color: #3c4043;
    }
    
    /* ===== BARRAS DE DESPLAZAMIENTO ===== */
    QScrollBar:vertical {
        border: none;
        background-color: #292a2d;
        width: 12px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #5f6368;
        border-radius: 6px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #80868b;
    }
    
    /* ===== GROUP BOXES ===== */
    QGroupBox {
        font-weight: bold;
        border: 1px solid #3c4043;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 12px;
        color: #e8eaed;
        font-size: 14px;
    }
    
    /* ===== PROGRESS BAR ===== */
    QProgressBar {
        border: 1px solid #3c4043;
        border-radius: 6px;
        background-color: #292a2d;
        text-align: center;
        color: #e8eaed;
        font-size: 12px;
    }
    
    QProgressBar::chunk {
        background-color: #34a853;
        border-radius: 6px;
    }
    
    /* ===== LABELS ===== */
    QLabel {
        color: #e8eaed;
        font-size: 14px;
    }
    
    /* ===== MENÚS ===== */
    QMenu {
        background-color: #292a2d;
        border: 1px solid #3c4043;
        color: #e8eaed;
        padding: 5px;
    }
    
    QMenu::item:selected {
        background-color: #4285f4;
    }
    """