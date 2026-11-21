"""CampusLink process entry point."""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from campuslink import __version__
from campuslink.app.config import SettingsStore, app_data_dir
from campuslink.app.logging_config import configure_logging
from campuslink.app.network_worker import NetworkWorker
from campuslink.database.store import Database
from campuslink.identity.device import IdentityStore
from campuslink.identity.trust import TrustStore
from campuslink.ui.main_window import MainWindow
from campuslink.ui.profile_wizard import ProfileWizard
from campuslink.ui.theme import apply_theme


def main() -> int:
    data_dir = app_data_dir()
    configure_logging(data_dir / "logs")
    logging.info("Starting CampusLink %s", __version__)

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    application = QApplication(sys.argv)
    application.setApplicationName("CampusLink")
    application.setApplicationVersion(__version__)
    application.setOrganizationName("CampusLink")

    settings_store = SettingsStore(data_dir / "settings.json")
    settings = settings_store.load()
    apply_theme(application, settings.theme)

    database = Database(data_dir / "campuslink.db")
    database.initialize()
    if database.get_profile() is None:
        wizard = ProfileWizard(database)
        if wizard.exec() != ProfileWizard.DialogCode.Accepted:
            database.close()
            return 0

    profile = database.get_profile()
    if profile is None:
        database.close()
        return 1
    identity = IdentityStore(data_dir / "identity").load_or_create(profile.display_name)
    trust = TrustStore(data_dir / "trusted-peers.json")
    network = NetworkWorker(identity, trust)
    network.start()
    window = MainWindow(database, settings_store, settings, identity, trust, network)
    application.aboutToQuit.connect(network.stop)
    application.aboutToQuit.connect(database.close)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
