"""Three-column CampusLink workspace."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from campuslink.app.config import AppSettings, SettingsStore
from campuslink.app.network_worker import NetworkWorker
from campuslink.database.store import Database
from campuslink.identity.device import DeviceIdentity
from campuslink.identity.trust import TrustStore
from campuslink.ui.chat_page import ChatPage
from campuslink.ui.theme import apply_theme
from campuslink.ui.transfer_page import TransferPage

IMPLEMENTED = {"Home", "Chats", "File Transfers", "Settings"}
NAVIGATION = [
    ("Home", "⌂"), ("Chats", "●"), ("Groups", "◆"), ("Nearby Devices", "◉"),
    ("File Transfers", "⇄"), ("Shared Files", "▣"), ("Screen Sharing", "▤"),
    ("Remote Assistance", "◇"), ("Live Location", "⌖"), ("Study Rooms", "▦"),
    ("Notifications", "○"), ("Settings", "⚙"),
]


class MainWindow(QMainWindow):
    def __init__(
        self,
        database: Database,
        settings_store: SettingsStore,
        settings: AppSettings,
        identity: DeviceIdentity,
        trust: TrustStore,
        network: NetworkWorker,
    ) -> None:
        super().__init__()
        self.database = database
        self.settings_store = settings_store
        self.settings = settings
        self.identity = identity
        self.trust = trust
        self.network = network
        self.setWindowTitle("CampusLink")
        self.resize(settings.window_width, settings.window_height)
        self.setMinimumSize(1020, 680)

        root = QWidget()
        root.setObjectName("root")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())
        layout.addWidget(self._build_workspace(), 1)
        self.setCentralWidget(root)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 18)
        layout.setSpacing(3)

        brand = QLabel("CampusLink")
        brand.setObjectName("brand")
        subtitle = QLabel("University workspace")
        subtitle.setObjectName("brandSub")
        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(22)

        self.nav_buttons: dict[str, QPushButton] = {}
        for label, symbol in NAVIGATION:
            button = QPushButton(f"{symbol}   {label}")
            button.setObjectName("nav")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            if label not in IMPLEMENTED:
                button.setEnabled(False)
                button.setToolTip("Planned for a later development phase")
            else:
                button.clicked.connect(lambda checked=False, name=label: self._select(name))
            self.nav_buttons[label] = button
            layout.addWidget(button)
        layout.addStretch()

        status = QLabel("●  Local mode")
        status.setObjectName("brandSub")
        status.setToolTip("Networking is introduced in Phase 2")
        layout.addWidget(status)
        return sidebar

    def _build_workspace(self) -> QWidget:
        workspace = QWidget()
        layout = QHBoxLayout(workspace)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        self.middle = QFrame()
        self.middle.setObjectName("panel")
        self.middle.setMinimumWidth(250)
        self.middle.setMaximumWidth(330)
        middle_layout = QVBoxLayout(self.middle)
        middle_layout.setContentsMargins(18, 18, 18, 18)
        heading = QLabel("Workspace")
        heading.setObjectName("sectionTitle")
        search = QLineEdit()
        search.setPlaceholderText("Search (Ctrl+K)")
        self.module_list = QListWidget()
        self.module_list.addItem("Overview")
        self.module_list.addItem("Recent activity")
        self.module_list.setCurrentRow(0)
        middle_layout.addWidget(heading)
        middle_layout.addWidget(search)
        middle_layout.addWidget(self.module_list, 1)
        layout.addWidget(self.middle)

        self.pages = QStackedWidget()
        self.home_page = self._build_home()
        self.chat_page = ChatPage(
            self.database, self.identity, self.trust, self.network
        )
        self.transfer_page = TransferPage()
        self.settings_page = self._build_settings()
        self.pages.addWidget(self.home_page)
        self.pages.addWidget(self.chat_page)
        self.pages.addWidget(self.transfer_page)
        self.pages.addWidget(self.settings_page)
        layout.addWidget(self.pages, 1)
        self._select("Home")
        return workspace

    def _card(self, title: str, body: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        text = QLabel(body)
        text.setObjectName("muted")
        text.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(text)
        return card

    def _build_home(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(14)
        profile = self.database.get_profile()
        title = QLabel(f"Welcome, {profile.display_name if profile else 'there'}")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Your private, local-first university workspace")
        subtitle.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(6)
        layout.addWidget(self._card(
            "Desktop foundation ready",
            "Your profile and settings are stored locally. Networking is intentionally disabled "
            "until authenticated transport and device trust are delivered in Phase 2.",
        ))
        layout.addWidget(self._card(
            "Privacy by default",
            "Nearby discoverability is off. Message previews are hidden in notifications. "
            "CampusLink does not present this local profile as a verified university identity.",
        ))
        layout.addWidget(self._card(
            "Coming next",
            "Secure device identity, explicit pairing, local discovery, and encrypted connections. "
            "Unavailable navigation items are disabled so unfinished features cannot be "
            "mistaken for working ones.",
        ))
        layout.addStretch()
        return page

    def _build_settings(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 4, 20, 4)
        layout.setSpacing(14)
        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        appearance = QFrame()
        appearance.setObjectName("card")
        box = QVBoxLayout(appearance)
        heading = QLabel("Appearance")
        heading.setObjectName("sectionTitle")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        self.theme_combo.setCurrentText(self.settings.theme.title())
        self.theme_combo.currentTextChanged.connect(self._change_theme)
        box.addWidget(heading)
        box.addWidget(QLabel("Color mode"))
        box.addWidget(self.theme_combo)
        layout.addWidget(appearance)

        privacy = QFrame()
        privacy.setObjectName("card")
        box = QVBoxLayout(privacy)
        heading = QLabel("Privacy & notifications")
        heading.setObjectName("sectionTitle")
        self.notifications = QCheckBox("Enable desktop notifications")
        self.notifications.setChecked(self.settings.notifications_enabled)
        self.previews = QCheckBox("Show message text in notifications")
        self.previews.setChecked(self.settings.show_message_preview)
        self.discoverable = QCheckBox("Allow nearby devices to discover this profile")
        self.discoverable.setChecked(self.settings.discoverable)
        self.discoverable.setEnabled(False)
        self.discoverable.setToolTip("Available after secure discovery is implemented in Phase 2")
        for checkbox in (self.notifications, self.previews):
            checkbox.toggled.connect(self._save_preferences)
        box.addWidget(heading)
        box.addWidget(self.notifications)
        box.addWidget(self.previews)
        box.addWidget(self.discoverable)
        layout.addWidget(privacy)

        phase = QLabel("CampusLink 0.1.0 · Phase 1 desktop foundation")
        phase.setObjectName("muted")
        layout.addWidget(phase)
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _select(self, name: str) -> None:
        for label, button in self.nav_buttons.items():
            button.setChecked(label == name)
        page = {
            "Home": self.home_page,
            "Chats": self.chat_page,
            "File Transfers": self.transfer_page,
            "Settings": self.settings_page,
        }[name]
        self.pages.setCurrentWidget(page)
        self.module_list.clear()
        items = {
            "Home": ["Overview", "Recent activity"],
            "Chats": ["Direct messages", "Pair a peer"],
            "File Transfers": ["Active transfer", "Transfer history"],
            "Settings": ["General", "Privacy", "About"],
        }[name]
        self.module_list.addItems(items)
        self.module_list.setCurrentRow(0)

    def _change_theme(self, label: str) -> None:
        self.settings.theme = label.lower()
        application = QApplication.instance()
        if isinstance(application, QApplication):
            apply_theme(application, self.settings.theme)
        self.settings_store.save(self.settings)

    def _save_preferences(self) -> None:
        self.settings.notifications_enabled = self.notifications.isChecked()
        self.settings.show_message_preview = self.previews.isChecked()
        self.settings_store.save(self.settings)

    def closeEvent(self, event: object) -> None:
        self.settings.window_width = self.width()
        self.settings.window_height = self.height()
        self.settings_store.save(self.settings)
        super().closeEvent(event)  # type: ignore[arg-type]
