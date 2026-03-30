import sys
from pathlib import Path

from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from ui.backend.app_controller import AppController


def qt_message_handler(mode, context, message):
    mode_name = {
        QtMsgType.QtDebugMsg: "DEBUG",
        QtMsgType.QtInfoMsg: "INFO",
        QtMsgType.QtWarningMsg: "WARNING",
        QtMsgType.QtCriticalMsg: "CRITICAL",
        QtMsgType.QtFatalMsg: "FATAL",
    }.get(mode, "LOG")
    print(f"[Qt {mode_name}] {message}")


def main():
    qInstallMessageHandler(qt_message_handler)

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    app_controller = AppController()
    engine.rootContext().setContextProperty("appController", app_controller)

    qml_file = Path(__file__).resolve().parent / "ui" / "qml" / "main.qml"
    print("QML file path:", qml_file)
    print("QML exists:", qml_file.exists())

    engine.load(str(qml_file))

    print("Root objects count:", len(engine.rootObjects()))

    if not engine.rootObjects():
        print("QML load failed.")
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
