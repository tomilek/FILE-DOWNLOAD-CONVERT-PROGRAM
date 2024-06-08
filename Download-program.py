import sys
import os 
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTabWidget, QMessageBox, QProgressBar, QComboBox, QFileDialog, QTextEdit, QProgressDialog
import subprocess
from pytube import YouTube
from PySide6.QtCore import Qt, QThread, Signal


class StylowaneWidgety(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #F0F0F0;
                color: #333;
                font-family: Arial, sans-serif;
            }
            QLabel {
                color: #333;
            }
            QLineEdit, QComboBox {
                background-color: #FFFFFF;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                background-color: #7289DA;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #536C8D;
            }
            QPushButton:pressed {
                background-color: #405D80;
            }
            QProgressBar {
                background-color: #FFFFFF;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 1px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;  /* Zielony kolor */
                width: 20px;
            }
        """)

class PobieraczYouTube(StylowaneWidgety):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pobieranie z YouTube")
        self.resize(800, 200)

        self.układ_główny = QVBoxLayout()

        self.etykieta_url = QLabel("Wprowadź adres URL z YouTube:")
        self.pole_url = QLineEdit()
        self.pole_url.setPlaceholderText("Wklej tutaj link")
        self.przycisk_ok = QPushButton("OK")
        self.przycisk_ok.clicked.connect(self.pobierz_tytul)

        self.etykieta_tytul = QLabel()

        self.układ_polowy = QHBoxLayout()

        self.etykieta_wybrany_format = QLabel("Wybierz format:")
        self.combo_wybrany_format = QComboBox()
        self.combo_wybrany_format.addItems(["Format MP4", "Format MP3"])

        self.przycisk_zapisu = QPushButton("Wybierz miejsce zapisu")
        self.przycisk_zapisu.clicked.connect(self.wybierz_folder)

        self.przycisk_pobierz = QPushButton("Pobierz")
        self.przycisk_pobierz.clicked.connect(self.pobierz_wideo)

        self.pasek_postepu = QProgressBar()
        self.pasek_postepu.setTextVisible(False)

        self.układ_główny.addWidget(self.etykieta_url)
        self.układ_główny.addWidget(self.pole_url)
        self.układ_główny.addWidget(self.przycisk_ok)
        self.układ_główny.addWidget(self.etykieta_tytul)

        self.układ_polowy.addWidget(self.etykieta_wybrany_format)
        self.układ_polowy.addWidget(self.combo_wybrany_format)

        self.układ_główny.addLayout(self.układ_polowy)
        self.układ_główny.addWidget(self.przycisk_zapisu)
        self.układ_główny.addWidget(self.przycisk_pobierz)
        self.układ_główny.addWidget(self.pasek_postepu, stretch=1)

        self.setLayout(self.układ_główny)

    def pobierz_tytul(self):
        url = self.pole_url.text()
        if not url:
            QMessageBox.warning(self, "Brak linku", "Proszę wprowadzić adres URL z YouTube.")
            return

        try:
            yt = YouTube(url)
            tytul = yt.title
            self.etykieta_tytul.setText(f"Tytuł: {tytul}")
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Wystąpił błąd: {e}")

    def wybierz_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder")
        if folder:
            self.folder_zapisu = folder

    def on_progress_callback(self, stream, chunk, bytes_remaining):
        total_bytes = stream.filesize
        bytes_downloaded = total_bytes - bytes_remaining
        percentage = int(bytes_downloaded / total_bytes * 100)
        self.pasek_postepu.setValue(percentage)
        self.dialog.setValue(percentage)

    def on_complete_callback(self, stream, file_handle):
        self.dialog.close()
        QMessageBox.information(self, "Sukces", "Pobieranie zakończone pomyślnie.")

    def pobierz_wideo(self):
        url = self.pole_url.text()
        if not url:
            QMessageBox.warning(self, "Brak linku", "Proszę wprowadzić adres URL.")
            return

        wybrany_format = self.combo_wybrany_format.currentText()
        try:
            yt = YouTube(url, on_progress_callback=self.on_progress_callback, on_complete_callback=self.on_complete_callback)
            if wybrany_format == "Format MP4":
                strumien = yt.streams.get_highest_resolution()
                rozszerzenie = 'mp4'
            elif wybrany_format == "Format MP3":
                strumien = yt.streams.filter(only_audio=True).first()
                rozszerzenie = 'mp3'

            if strumien is None:
                QMessageBox.warning(self, "Błąd", "Nie można pobrać wideo w wybranym formacie.")
            else:
                nazwa_pliku = f"{strumien.default_filename.split('.')[0]}.{rozszerzenie}"
                if hasattr(self, 'folder_zapisu'):
                    self.dialog = QProgressDialog("Pobieranie...", "Anuluj", 0, 100, self)
                    self.dialog.setWindowModality(Qt.WindowModal)
                    self.dialog.setWindowTitle("Pobieranie")
                    self.dialog.setAutoClose(True)
                    self.dialog.show()

                    strumien.download(output_path=self.folder_zapisu, filename=nazwa_pliku)
                else:
                    QMessageBox.warning(self, "Brak miejsca zapisu", "Proszę wybrać miejsce zapisu dla pobranych plików.")
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Wystąpił błąd: {e}")

class KonwerterThread(QThread):
    finished = Signal()

    def __init__(self, plik_wejsciowy, format_docelowy):
        super().__init__()
        self.plik_wejsciowy = plik_wejsciowy
        self.format_docelowy = format_docelowy

    def run(self):
        try:
            plik_wyjsciowy = self.plik_wejsciowy.rsplit(".", 1)[0] + "." + self.format_docelowy.lower()
            if self.format_docelowy == "MP4":
                raise ValueError("Konwersja z MP3 do MP4 nie jest obsługiwana.")
            else:
                polecenie = f"ffmpeg -i \"{self.plik_wejsciowy}\" \"{plik_wyjsciowy}\""
                wynik = subprocess.run(polecenie, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                if wynik.returncode != 0:
                    error_message = wynik.stderr.decode('utf-8')
                    self.error_message = error_message
                else:
                    self.error_message = None
        except Exception as e:
            self.error_message = str(e)

        self.finished.emit()

class KonwerterPlikow(StylowaneWidgety):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Konwerter Plików")

        self.etykieta_opis = QLabel("Wybierz plik do konwersji:")
        self.przycisk_wybierz_plik = QPushButton("Wybierz plik")
        self.przycisk_wybierz_plik.clicked.connect(self.wybierz_plik)
       
        self.pole_plik = QLineEdit()

        self.etykieta_opis_formatu = QLabel("Wybierz format docelowy:")
        self.combo_format = QComboBox()
        self.combo_format.addItems(["MP4", "MP3"])

        self.przycisk_konwertuj = QPushButton("Konwertuj")
        self.przycisk_konwertuj.clicked.connect(self.konwertuj)

        self.wyniki_konwersji = QTextEdit()
        self.wyniki_konwersji.setReadOnly(True)

        self.thread = None

        układ = QVBoxLayout()
        układ.addWidget(self.etykieta_opis)
        układ.addWidget(self.pole_plik)
        układ.addWidget(self.przycisk_wybierz_plik)
        układ.addWidget(self.etykieta_opis_formatu)
        układ.addWidget(self.combo_format)
        układ.addWidget(self.przycisk_konwertuj)
        układ.addWidget(self.wyniki_konwersji)

        self.setLayout(układ)

    def wybierz_plik(self):
        plik, _ = QFileDialog.getOpenFileName(self, "Wybierz plik do konwersji")
        if plik:
            self.pole_plik.setText(plik)

    def konwertuj(self):
        if self.thread and self.thread.isRunning():
            return

        plik_wejsciowy = self.pole_plik.text()
        if not plik_wejsciowy:
            QMessageBox.warning(self, "Brak pliku", "Proszę wybrać plik do konwersji.")
            return

        format_docelowy = self.combo_format.currentText()
        self.wyniki_konwersji.clear()
        self.wyniki_konwersji.append(f"Konwertowanie {plik_wejsciowy} do formatu {format_docelowy}...\n")

        self.thread = KonwerterThread(plik_wejsciowy, format_docelowy)
        self.thread.finished.connect(self.on_conversion_finished)
        self.thread.start()

    def on_conversion_finished(self):
        if self.thread.error_message:
            self.wyniki_konwersji.append(f"Błąd konwersji: {self.thread.error_message}\n")
        else:
            self.wyniki_konwersji.append("Konwersja zakończona pomyślnie.\n")

class Aplikacja(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aplikacja do Pobierania i Konwersji")
        self.setGeometry(100, 100, 800, 400)
        self.karta = QTabWidget()
        self.setCentralWidget(self.karta)

        self.karta.addTab(PobieraczYouTube(), "Pobieracz YouTube") 
        self.karta.addTab(KonwerterPlikow(), "Konwerter Plików")
         

if __name__ == "__main__":
    app = QApplication(sys.argv)
    okno = Aplikacja()
    okno.show()
    sys.exit(app.exec())
