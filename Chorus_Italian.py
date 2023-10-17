# Nome del Software: Chorus
# Autore: Luca Bocaletto
# Descrizione: Applicazione Python per creare un effetto audio Chorus.

# Importa le librerie necessarie
import sys
import numpy as np
import sounddevice as sd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QPushButton

# Definizione delle costanti
FREQUENZA_CAMPIONAMENTO = 44100  # Frequenza di campionamento per l'elaborazione audio
DIMENSIONE_BLOCCO = 8192  # Dimensione del blocco di elaborazione audio

# Crea un'applicazione basata su QWidget per l'effetto Chorus
class AppChorus(QWidget):
    def __init__(self):
        super().__init__()
        self.inizializza_predefiniti()  # Inizializza le impostazioni predefinite
        self.inizializza_UI()  # Inizializza l'interfaccia utente
        self.inizializza_Audio()  # Inizializza l'elaborazione audio
        self.is_chorus_enabled = False  # Flag per attivare/disattivare l'effetto Chorus
        self.buffer_audio = np.zeros(DIMENSIONE_BLOCCO)  # Inizializza un buffer audio

    def inizializza_predefiniti(self):
        # Parametri predefiniti per l'effetto Chorus
        self.ritardo = 0.025
        self.intensita = 0.5
        self.tasso_lfo = 0.5
        self.feedback = 0.3
        self.mischiamento = 0.5
        # Crea un buffer di ritardo per l'elaborazione audio
        self.buffer_ritardo = np.zeros(int(self.ritardo * FREQUENZA_CAMPIONAMENTO) + DIMENSIONE_BLOCCO)
        self.fase_lfo = 0

        self.slider = []  # Lista per memorizzare gli elementi dello slider

    def inizializza_UI(self):
        self.setGeometry(100, 100, 400, 400)  # Imposta le dimensioni della finestra
        self.setWindowTitle('Chorus')  # Imposta il titolo della finestra
        self.setStyleSheet("background-color: #4B0082; color: yellow;")  # Definisci lo stile della finestra

        # Crea un QLabel per visualizzare il titolo
        self.label_titolo = QLabel('Chorus')
        self.label_titolo.setAlignment(Qt.AlignCenter)  # Imposta l'allineamento del testo
        self.label_titolo.setFont(QFont('Arial', 24))  # Imposta il carattere del testo

        # Crea gli slider per regolare i parametri del Chorus
        self.slider_ritardo = self.crea_slider(self.ritardo, self.aggiornaRitardo, "Ritardo Chorus: {:.2f} ms")
        self.slider_intensita = self.crea_slider(self.intensita, self.aggiornaIntensita, "Intensità: {:.2f}")
        self.slider_tasso_lfo = self.crea_slider(self.tasso_lfo, self.aggiornaTassoLFO, "Tasso LFO: {:.2f}")
        self.slider_feedback = self.crea_slider(self.feedback, self.aggiornaFeedback, "Feedback: {:.2f}")
        self.slider_mischiamento = self.crea_slider(self.mischiamento, self.aggiornaMischiamento, "Mischiamento: {:.2f}")

        # Crea un pulsante per attivare/disattivare l'effetto Chorus
        self.pulsante_toggle = QPushButton('Attiva/Disattiva Chorus')
        self.pulsante_toggle.clicked.connect(self.cambiaStatoChorus)

        layout = QVBoxLayout()  # Crea un layout per i widget
        layout.addWidget(self.label_titolo)  # Aggiungi il label del titolo al layout

        # Aggiungi gli slider e i label al layout
        for slider, label in self.slider:
            layout.addWidget(label)
            layout.addWidget(slider)

        layout.addWidget(self.pulsante_toggle)  # Aggiungi il pulsante di attivazione al layout

        self.setLayout(layout)  # Imposta il layout per la finestra principale

    def crea_slider(self, valore, callback, formato_label):
        slider = QSlider(orientation=1)  # Crea un elemento slider
        slider.setRange(0, 100)  # Imposta il range dello slider
        slider.setValue(int(valore * 100) if isinstance(valore, float) else valore)  # Imposta il valore iniziale

        label = QLabel(formato_label.format(valore))  # Crea un label per visualizzare il valore del parametro

        slider.valueChanged.connect(callback)  # Collega lo slider alla sua funzione di callback

        self.slider.append((slider, label))  # Aggiungi lo slider e il label alla lista

        return slider

    def inizializza_Audio(self):
        def callback_audio(indata, outdata, frames, time, status):
            if status:
                print("Stato Audio:", status, file=sys.stderr)

            if self.is_chorus_enabled:
                offset = int(self.intensita * DIMENSIONE_BLOCCO * np.sin(2 * np.pi * self.fase_lfo))
                if offset >= len(self.buffer_ritardo):
                    offset = len(self.buffer_ritardo) - 1

                # Copia i campioni di input nel buffer di ritardo
                self.buffer_ritardo[:DIMENSIONE_BLOCCO] = indata[:, 0] + self.feedback * self.buffer_ritardo[:DIMENSIONE_BLOCCO]

                # Applica l'effetto Chorus mescolando l'audio in ingresso e l'audio ritardato
                bagnato = self.mischiamento * indata[:, 0] + (1 - self.mischiamento) * self.buffer_ritardo[:DIMENSIONE_BLOCCO]
                outdata[:, 0] = bagnato
                outdata[:, 1] = bagnato

                # Aggiorna la fase dell'Oscillatore a Bassa Frequenza (LFO)
                self.fase_lfo += self.tasso_lfo * DIMENSIONE_BLOCCO / FREQUENZA_CAMPIONAMENTO

            else:
                outdata[:] = indata

        # Crea uno stream audio per l'elaborazione dei dati audio
        self.stream = sd.Stream(
            callback=callback_audio,
            samplerate=FREQUENZA_CAMPIONAMENTO,
            channels=2,
            blocksize=DIMENSIONE_BLOCCO
        )

        self.stream.start()

    def aggiornaRitardo(self):
        self.ritardo = self.slider_ritardo.value() / 1000.0
        self.buffer_ritardo = np.zeros(int(self.ritardo * FREQUENZA_CAMPIONAMENTO) + DIMENSIONE_BLOCCO)
        self.slider[0][1].setText(f"Ritardo Chorus: {self.ritardo * 1000:.2f} ms")

    def aggiornaIntensita(self):
        self.intensita = self.slider_intensita.value() / 100.0
        self.slider[1][1].setText(f"Intensità: {self.intensita:.2f}")

    def aggiornaTassoLFO(self):
        self.tasso_lfo = self.slider_tasso_lfo.value() / 100.0
        self.slider[2][1].setText(f"Tasso LFO: {self.tasso_lfo:.2f}")

    def aggiornaFeedback(self):
        self.feedback = self.slider_feedback.value() / 100.0
        self.slider[3][1].setText(f"Feedback: {self.feedback:.2f}")

    def aggiornaMischiamento(self):
        self.mischiamento = self.slider_mischiamento.value() / 100.0
        self.slider[4][1].setText(f"Mischiamento: {self.mischiamento:.2f}")

    def cambiaStatoChorus(self):
        self.is_chorus_enabled = not self.is_chorus_enabled

# Punto di ingresso dell'applicazione
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AppChorus()
    ex.show()
    sys.exit(app.exec_())
