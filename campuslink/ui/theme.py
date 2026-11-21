"""Solid-surface light and dark application themes."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

LIGHT = {
    "bg": "#f4f5f7", "surface": "#ffffff", "sidebar": "#17212b", "sidebar_text": "#dce3ea",
    "text": "#18202a", "muted": "#647184", "border": "#dce1e7", "accent": "#176b5b",
    "accent_hover": "#115647", "selection": "#e5f2ef", "danger": "#b42318",
}
DARK = {
    "bg": "#11161c", "surface": "#192129", "sidebar": "#0d1217", "sidebar_text": "#dce3ea",
    "text": "#edf1f5", "muted": "#9ca9b7", "border": "#2b3742", "accent": "#4db59f",
    "accent_hover": "#65c6b2", "selection": "#203a36", "danger": "#ff7b72",
}


def stylesheet(mode: str) -> str:
    colors = DARK if mode == "dark" else LIGHT
    template = """
    * { font-family: "Segoe UI"; font-size: 14px; color: %(text)s; }
    QMainWindow, QDialog, QWidget#root { background: %(bg)s; }
    QFrame#sidebar { background: %(sidebar)s; border: none; }
    QLabel#brand { color: white; font-size: 21px; font-weight: 700; }
    QLabel#brandSub { color: #9fb0bf; font-size: 12px; }
    QPushButton#nav { color: %(sidebar_text)s; text-align: left; padding: 9px 14px; border: 0;
                      border-radius: 7px; background: transparent; }
    QPushButton#nav:hover { background: #263542; color: white; }
    QPushButton#nav:checked { background: #314653; color: white; font-weight: 600;
                              border-left: 3px solid #59bda8; }
    QPushButton#nav:disabled { color: #70808e; }
    QFrame#panel, QFrame#card { background: %(surface)s; border: 1px solid %(border)s;
                               border-radius: 10px; }
    QLabel#pageTitle { font-size: 24px; font-weight: 700; }
    QLabel#sectionTitle { font-size: 16px; font-weight: 650; }
    QLabel#muted { color: %(muted)s; }
    QLabel#statusOnline { color: %(accent)s; font-weight: 600; }
    QLineEdit, QComboBox { background: %(surface)s; border: 1px solid %(border)s;
                           border-radius: 7px;
                           padding: 8px 10px; min-height: 20px; }
    QLineEdit:focus, QComboBox:focus { border: 2px solid %(accent)s; }
    QPushButton { padding: 8px 14px; border-radius: 7px; border: 1px solid %(border)s;
                  background: %(surface)s; }
    QPushButton:hover { border-color: %(accent)s; }
    QPushButton#primary { background: %(accent)s; color: white; border: none; font-weight: 600; }
    QPushButton#primary:hover { background: %(accent_hover)s; }
    QListWidget { background: transparent; border: none; outline: none; }
    QListWidget::item { padding: 10px; border-radius: 7px; }
    QListWidget::item:selected { background: %(selection)s; color: %(text)s; }
    QCheckBox { spacing: 8px; }
    QScrollArea { border: none; background: transparent; }
    """
    return template % colors  # noqa: UP031 -- Qt style sheets use literal braces.


def apply_theme(application: QApplication, mode: str) -> None:
    if mode == "system":
        mode = "dark" if application.styleHints().colorScheme().value == 2 else "light"
    application.setStyleSheet(stylesheet(mode))
