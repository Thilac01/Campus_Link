"""First-run local profile setup."""

from __future__ import annotations

import platform

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from campuslink.database.store import Database, Profile


class ProfileWizard(QDialog):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.setWindowTitle("Welcome to CampusLink")
        self.setMinimumWidth(520)

        title = QLabel("Create your local profile")
        title.setObjectName("pageTitle")
        explanation = QLabel(
            "This profile stays on this device. It is not a university-verified identity."
        )
        explanation.setObjectName("muted")
        explanation.setWordWrap(True)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Required")
        self.email = QLineEdit()
        self.email.setPlaceholderText("Optional")
        self.department = QLineEdit()
        self.year = QLineEdit()
        self.device = QLineEdit(platform.node())

        form = QFormLayout()
        form.setSpacing(12)
        form.addRow("Display name", self.name)
        form.addRow("University email", self.email)
        form.addRow("Department", self.department)
        form.addRow("Academic year", self.year)
        form.addRow("Device nickname", self.device)

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        continue_button = QPushButton("Create profile")
        continue_button.setObjectName("primary")
        continue_button.clicked.connect(self._save)
        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(continue_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 30, 32, 28)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addWidget(explanation)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addSpacing(10)
        layout.addLayout(actions)

    def _save(self) -> None:
        try:
            self.database.save_profile(
                Profile(
                    display_name=self.name.text(), university_email=self.email.text(),
                    department=self.department.text(), academic_year=self.year.text(),
                    device_nickname=self.device.text(),
                )
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Profile incomplete", str(exc))
            return
        self.accept()
