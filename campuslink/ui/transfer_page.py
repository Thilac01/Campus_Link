"""Responsive resumable transfer workspace."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from campuslink.transfers.engine import ResumableCopy, TransferResult


class CopyWorker(QThread):
    progress_changed = Signal(int, int, float)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, source: Path, destination: Path) -> None:
        super().__init__()
        self.source = source
        self.destination = destination
        self.cancel_event = threading.Event()
        self.pause_event = threading.Event()

    def run(self) -> None:
        try:
            result = ResumableCopy().copy(
                self.source,
                self.destination,
                progress=lambda transferred, total, speed: self.progress_changed.emit(
                    transferred, total, speed
                ),
                cancel=self.cancel_event,
                pause=self.pause_event,
            )
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class TransferPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.worker: CopyWorker | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        title = QLabel("File transfers")
        title.setObjectName("pageTitle")
        note = QLabel(
            "This milestone provides bounded, resumable, hash-verified transfer processing. "
            "Peer bulk-channel negotiation is still under development."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(note)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        self.source = QLineEdit()
        self.source.setPlaceholderText("Source file")
        source_row = QHBoxLayout()
        source_row.addWidget(self.source, 1)
        source_button = QPushButton("Choose file…")
        source_button.clicked.connect(self._choose_source)
        source_row.addWidget(source_button)
        self.destination = QLineEdit()
        self.destination.setPlaceholderText("Destination file")
        destination_row = QHBoxLayout()
        destination_row.addWidget(self.destination, 1)
        destination_button = QPushButton("Choose destination…")
        destination_button.clicked.connect(self._choose_destination)
        destination_row.addWidget(destination_button)
        card_layout.addLayout(source_row)
        card_layout.addLayout(destination_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.status = QLabel("Ready")
        self.status.setObjectName("muted")
        card_layout.addWidget(self.progress)
        card_layout.addWidget(self.status)

        actions = QHBoxLayout()
        self.start_button = QPushButton("Start / Resume")
        self.start_button.setObjectName("primary")
        self.start_button.clicked.connect(self._start)
        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self._toggle_pause)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._cancel)
        actions.addWidget(self.start_button)
        actions.addWidget(self.pause_button)
        actions.addWidget(self.cancel_button)
        actions.addStretch()
        card_layout.addLayout(actions)
        layout.addWidget(card)
        layout.addStretch()

    def _choose_source(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select a file to transfer")
        if path:
            self.source.setText(path)
            if not self.destination.text():
                source = Path(path)
                self.destination.setText(str(source.with_name(f"Copy of {source.name}")))

    def _choose_destination(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Select transfer destination")
        if path:
            self.destination.setText(path)

    def _start(self) -> None:
        source = Path(self.source.text().strip())
        destination = Path(self.destination.text().strip())
        if not source.is_file() or not self.destination.text().strip():
            QMessageBox.warning(self, "Invalid transfer", "Choose a source and destination file.")
            return
        self.worker = CopyWorker(source, destination)
        self.worker.progress_changed.connect(self._progress)
        self.worker.completed.connect(self._completed)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(self._worker_finished)
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.status.setText("Transferring…")
        self.worker.start()

    def _progress(self, transferred: int, total: int, speed: float) -> None:
        self.progress.setValue(1000 if total == 0 else int(transferred / total * 1000))
        self.status.setText(
            f"{transferred:,} of {total:,} bytes · {speed / (1024 * 1024):.1f} MiB/s"
        )

    def _toggle_pause(self) -> None:
        if self.worker is None:
            return
        if self.worker.pause_event.is_set():
            self.worker.pause_event.clear()
            self.pause_button.setText("Pause")
            self.status.setText("Resuming…")
        else:
            self.worker.pause_event.set()
            self.pause_button.setText("Resume")
            self.status.setText("Paused · partial data is safe")

    def _cancel(self) -> None:
        if self.worker is not None:
            self.worker.cancel_event.set()
            self.status.setText("Cancelling…")

    def _completed(self, result_object: object) -> None:
        result = result_object
        if not isinstance(result, TransferResult):
            return
        self.progress.setValue(1000)
        self.status.setText(f"Verified · SHA-256 {result.sha256[:16]}…")

    def _failed(self, detail: str) -> None:
        self.status.setText(detail)

    def _worker_finished(self) -> None:
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.pause_button.setText("Pause")
        self.worker = None
