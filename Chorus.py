# Software Name: Chorus
# Author: Luca Bocaletto
# Description: A Python application for creating a Chorus audio effect.
# Import necessary libraries
import sys
import numpy as np
import sounddevice as sd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QPushButton

# Definition of constants
SAMPLE_RATE = 44100  # Sample rate for audio processing
BLOCK_SIZE = 8192    # Size of audio processing block

# Create a QWidget-based application for the Chorus effect
class ChorusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_defaults()  # Initialize default settings
        self.initUI()  # Initialize the user interface
        self.initAudio()  # Initialize audio processing
        self.is_chorus_enabled = False  # Flag to toggle the Chorus effect
        self.audio_buffer = np.zeros(BLOCK_SIZE)  # Initialize an audio buffer

    def init_defaults(self):
        # Default parameters for the Chorus effect
        self.delay = 0.025
        self.depth = 0.5
        self.lfo_rate = 0.5
        self.feedback = 0.3
        self.mix = 0.5
        # Create a delay buffer for audio processing
        self.delay_buffer = np.zeros(int(self.delay * SAMPLE_RATE) + BLOCK_SIZE)
        self.lfo_phase = 0

        self.sliders = []  # List to store slider elements

    def initUI(self):
        self.setGeometry(100, 100, 400, 400)  # Set window dimensions
        self.setWindowTitle('Chorus')  # Set the window title
        self.setStyleSheet("background-color: #4B0082; color: yellow;")  # Define the window style

        # Create a QLabel to display the title
        self.title_label = QLabel('Chorus')
        self.title_label.setAlignment(Qt.AlignCenter)  # Set text alignment
        self.title_label.setFont(QFont('Arial', 24))  # Set text font

        # Create sliders for adjusting Chorus parameters
        self.delay_slider = self.create_slider(self.delay, self.updateDelay, "Chorus Delay: {:.2f} ms")
        self.depth_slider = self.create_slider(self.depth, self.updateDepth, "Depth: {:.2f}")
        self.lfo_rate_slider = self.create_slider(self.lfo_rate, self.updateLfoRate, "LFO Rate: {:.2f}")
        self.feedback_slider = self.create_slider(self.feedback, self.updateFeedback, "Feedback: {:.2f}")
        self.mix_slider = self.create_slider(self.mix, self.updateMix, "Mix: {:.2f}")

        # Create a button to toggle the Chorus effect
        self.toggle_button = QPushButton('Toggle Chorus')
        self.toggle_button.clicked.connect(self.toggleChorus)

        layout = QVBoxLayout()  # Create a layout for widgets
        layout.addWidget(self.title_label)  # Add the title label to the layout

        # Add sliders and labels to the layout
        for slider, label in self.sliders:
            layout.addWidget(label)
            layout.addWidget(slider)

        layout.addWidget(self.toggle_button)  # Add the toggle button to the layout

        self.setLayout(layout)  # Set the layout for the main application window

    def create_slider(self, value, callback, label_format):
        slider = QSlider(orientation=1)  # Create a slider element
        slider.setRange(0, 100)  # Set the slider range
        slider.setValue(int(value * 100) if isinstance(value, float) else value)  # Set initial value

        label = QLabel(label_format.format(value))  # Create a label to display the parameter value

        slider.valueChanged.connect(callback)  # Connect the slider to its callback function

        self.sliders.append((slider, label))  # Append the slider and label to the list

        return slider

    def initAudio(self):
        def audio_callback(indata, outdata, frames, time, status):
            if status:
                print("Audio status:", status, file=sys.stderr)

            if self.is_chorus_enabled:
                offset = int(self.depth * BLOCK_SIZE * np.sin(2 * np.pi * self.lfo_phase))
                if offset >= len(self.delay_buffer):
                    offset = len(self.delay_buffer) - 1

                # Copy input samples into the delay buffer
                self.delay_buffer[:BLOCK_SIZE] = indata[:, 0] + self.feedback * self.delay_buffer[:BLOCK_SIZE]

                # Apply the chorus effect by mixing the input and delayed audio
                wet = self.mix * indata[:, 0] + (1 - self.mix) * self.delay_buffer[:BLOCK_SIZE]
                outdata[:, 0] = wet
                outdata[:, 1] = wet

                # Update the phase of the Low-Frequency Oscillator (LFO)
                self.lfo_phase += self.lfo_rate * BLOCK_SIZE / SAMPLE_RATE

            else:
                outdata[:] = indata

        # Create an audio stream for processing audio data
        self.stream = sd.Stream(
            callback=audio_callback,
            samplerate=SAMPLE_RATE,
            channels=2,
            blocksize=BLOCK_SIZE
        )

        self.stream.start()

    def updateDelay(self):
        self.delay = self.delay_slider.value() / 1000.0
        self.delay_buffer = np.zeros(int(self.delay * SAMPLE_RATE) + BLOCK_SIZE)
        self.sliders[0][1].setText(f"Chorus Delay: {self.delay * 1000:.2f} ms")

    def updateDepth(self):
        self.depth = self.depth_slider.value() / 100.0
        self.sliders[1][1].setText(f"Depth: {self.depth:.2f}")

    def updateLfoRate(self):
        self.lfo_rate = self.lfo_rate_slider.value() / 100.0
        self.sliders[2][1].setText(f"LFO Rate: {self.lfo_rate:.2f}")

    def updateFeedback(self):
        self.feedback = self.feedback_slider.value() / 100.0
        self.sliders[3][1].setText(f"Feedback: {self.feedback:.2f}")

    def updateMix(self):
        self.mix = self.mix_slider.value() / 100.0
        self.sliders[4][1].setText(f"Mix: {self.mix:.2f}")

    def toggleChorus(self):
        self.is_chorus_enabled = not self.is_chorus_enabled

# Entry point of the application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ChorusApp()
    ex.show()
    sys.exit(app.exec_())
