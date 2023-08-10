import sys
import os
import threading
import wave
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import pyaudio
import openai
import pyperclip
import webbrowser

# ----- Start of the first script functionality -----

def save_api_key(key):
    """Save the provided OpenAI API key to a configuration file."""
    with open("config.txt", "w") as file:
        file.write(key)

def open_link(event):
    """Open the provided link in the default web browser."""
    webbrowser.open("https://www.howtogeek.com/885918/how-to-get-an-openai-api-key/")

def display_guide_with_link():
    """Display the guide with a clickable link to obtain the OpenAI API key."""
    guide_window = tk.Toplevel()
    guide_window.geometry('500x150')
    guide_window.title("API Key Required")

    label1 = tk.Label(guide_window, text="The transcription process requires an API key.")
    label1.pack(pady=10)
    link = tk.Label(guide_window, text="Click here for a guide on how to get it.", fg="blue", cursor="hand2")
    link.pack(pady=10)
    link.bind("<Button-1>", open_link)
    button = tk.Button(guide_window, text="Close", command=guide_window.destroy)
    button.pack(pady=10)

def get_api_key_from_user():
    """Prompt the user to input the OpenAI API key in a larger window."""
    def submit_api_key():
        api_key = entry.get().strip()
        if api_key:
            save_api_key(api_key)
            messagebox.showinfo("Success", "API key saved successfully!")
            root.destroy()
        else:
            messagebox.showwarning("Error", "API key was not entered!")

    display_guide_with_link()
    root = tk.Toplevel()
    root.geometry('400x150')
    label = tk.Label(root, text="Enter your personal OpenAI API key:")
    label.pack(pady=20)
    entry = tk.Entry(root, width=50)
    entry.pack(pady=10)
    button = tk.Button(root, text="Submit", command=submit_api_key)
    button.pack(pady=10)
    root.mainloop()

def check_and_get_api_key():
    if not os.path.exists("config.txt"):
        root = tk.Tk()
        root.withdraw()
        get_api_key_from_user()

def get_config_path():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # If the application is run as a bundle/exe
        application_path = sys._MEIPASS
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(application_path, 'config.txt')
# Audio Recording Functionality
class AudioRecorder:
    def __init__(self):
        self.is_recording = False
        self.frames = []
        self.p, self.stream = None, None

    def list_microphones(self):
        p = pyaudio.PyAudio()
        microphones = {}
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev['maxInputChannels'] > 0:
                microphones[i] = dev['name']
        p.terminate()
        return microphones

    def start_audio_stream(self, device_index):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100

        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=CHUNK)
        return p, stream

    def stop_audio_stream(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def async_record_audio(self):
        CHUNK = 1024
        print("Starting recording...")

        self.is_recording = True
        self.frames = []

        microphones = self.list_microphones()
        if microphones:
            index = list(microphones.keys())[0]
            self.p, self.stream = self.start_audio_stream(index)

        while self.is_recording:
            data = self.stream.read(CHUNK)
            self.frames.append(data)

    def stop_and_save(self, filename):
        print("Stopping recording...")

        self.is_recording = False
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        self.stop_audio_stream()


# Audio Transcription Functionality
class AudioTranscriber:
    def __init__(self, api_key):
        openai.api_key = api_key

    def transcribe_audio(self, filename):
        with open(filename, 'rb') as audio_file:
            response = openai.Audio.transcribe("whisper-1", audio_file)
        return response['text']


# GUI Functionality
class AnimatedGIF(tk.Label):
    def __init__(self, master, path, *args, **kwargs):
        self._photo_images = []  # List to store the PhotoImage objects and prevent garbage collection
        self.frames = []
        self.load_frames(path)
        self.current_frame = 0
        super(AnimatedGIF, self).__init__(master, image=self.frames[0], *args, **kwargs)
        self.is_playing = False

    def load_frames(self, path):
        im = Image.open(path)
        self.frames.clear()
        self._photo_images.clear()  # Clear the previous images
        photo = ImageTk.PhotoImage(im.copy())
        self._photo_images.append(photo)  # Keep a reference
        self.frames.append(photo)
        try:
            for i in range(1, 1000):
                im.seek(i)
                photo = ImageTk.PhotoImage(im.copy())
                self._photo_images.append(photo)  # Keep a reference
                self.frames.append(photo)
        except EOFError:
            pass

    def play(self):
        if not self.is_playing:
            self.is_playing = True
            self.animate()

    def stop(self):
        self.is_playing = False

    def animate(self):
        if self.is_playing:
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                self.current_frame = 0
            self.config(image=self.frames[self.current_frame])
            self.after(40, self.animate)

    def set_gif(self, path):
        self.load_frames(path)
        self.current_frame = 0
        self.config(image=self.frames[0])


# Combined UI and Functionality
class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.audio_recorder = AudioRecorder()
        self.audio_transcriber = AudioTranscriber(self.get_api_key_from_config())

        self.gif_widget = None
        self.setup_ui()

    @staticmethod
    def get_api_key_from_config():
        config_path = get_config_path()
        with open(config_path, "r") as file:
            # You find a secret API-key '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' Use it! But don't tell to others, ok?
            return file.readline().strip()
    def set_gif_state(self, state):
        gif_paths = {
            'default': "default.gif",
            'recording': "recording.gif",
            'processing': "processing.gif"
        }
        gif_path = gif_paths.get(state)
        if not os.path.exists(gif_path):
            print(f"File {gif_path} not found!")
            return
        self.gif_widget.set_gif(gif_path)
        self.gif_widget.play()

    def toggle_recording(self):
        if not self.audio_recorder.is_recording:
            self.set_gif_state('recording')
            threading.Thread(target=self.audio_recorder.async_record_audio).start()
        else:
            self.set_gif_state('processing')
            threading.Thread(target=self.stop_and_transcribe).start()

    def stop_and_transcribe(self):
        self.audio_recorder.stop_and_save("voice_sample.wav")
        transcription = self.audio_transcriber.transcribe_audio("voice_sample.wav")
        pyperclip.copy(transcription)
        print("Transcription:", transcription)
        self.root.after(0, lambda: self.set_gif_state('default'))

    def setup_ui(self):
        self.root.title("Audio Transcription")
        self.root.geometry('150x150')

        drag_frame = tk.Frame(self.root, bg="black")
        drag_frame.pack(fill=tk.BOTH, expand=True)
        drag_frame.bind('<Button-1>', lambda event: self.toggle_recording())

        style = ttk.Style()
        style.configure('TButton', background='black', foreground='black')
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.configure(background='black')

        self.gif_widget = AnimatedGIF(drag_frame, "default.gif", bg="black")
        self.gif_widget.pack(fill=tk.BOTH, expand=True)
        self.gif_widget.play()
        self.gif_widget.bind('<Button-1>', lambda event: self.toggle_recording())

    def run(self):
        self.root.mainloop()

# Define the standalone run() function
def run(root=None):
    if not root:
        root = tk.Tk()
    app = TranscriptionApp(root)
    app.run()


if __name__ == "__main__":
    check_and_get_api_key()
    run()  # Call the standalone run function