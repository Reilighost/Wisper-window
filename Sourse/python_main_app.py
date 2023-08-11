import os
import threading
import wave
import tkinter as tk
from PIL import Image, ImageTk
import pyaudio
import openai
import pyperclip
import webbrowser
import json
# Constants

PREFERRED_MODEL = "gpt-3.5-turbo"  # Users can change this value to their desired model
ENABLE_RESPONSE_WINDOW = False
CONFIG_PATH = "config.json"
GIF_PATHS = {
    'default': "default.gif",
    'recording': "recording.gif",
    'processing': "processing.gif"
}

class ResponseWindow:
    def __init__(self, master, response_text, api_key):
        self.master = master
        self.response_text = response_text
        self.api_key = api_key  # Storing the API key

        # Create the window
        self.response_window = tk.Toplevel(self.master)
        self.response_window.title("Transcription and Response")
        self.response_window.geometry('400x400')
        self.response_window.attributes('-topmost', True)  # Ensure transcription window is always on top

        # Add text widget to display the transcribed text
        self.transcription_widget = tk.Text(self.response_window, wrap=tk.WORD, height=10)
        self.transcription_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        self.transcription_widget.insert(tk.END, "Transcribed Text:\n" + self.response_text)
        self.transcription_widget.config(state=tk.DISABLED)  # Making the widget read-only

        # Add text widget to display GPT-4's response
        self.response_widget = tk.Text(self.response_window, wrap=tk.WORD, height=10)
        self.response_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        gpt_response = self.get_gpt4_response(self.response_text)
        self.response_widget.insert(tk.END, "GPT-4 Response:\n" + gpt_response)
        self.response_widget.config(state=tk.DISABLED)  # Making the widget read-only

    def get_gpt4_response(self, prompt):
        openai.api_key = self.api_key

        # Format the input as a conversation using the chat completions API
        conversation = {
            "model": PREFERRED_MODEL,  # or "gpt-3.5-turbo"
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        }

        # Get the response from GPT-4
        response = openai.ChatCompletion.create(**conversation)

        # Extract the assistant's message from the response
        gpt_response = response.choices[0].message['content']

        return gpt_response.strip()

    def display(self):
        self.response_window.mainloop()
class ConfigManager:
    @staticmethod
    def save_api_key(key):
        """Save the provided OpenAI API key to a configuration file in JSON format."""
        config_data = {"api_key": key}
        with open(CONFIG_PATH, "w") as file:
            json.dump(config_data, file)

    @staticmethod
    def get_api_key():
        """Retrieve the OpenAI API key from the configuration file in JSON format."""
        if not os.path.exists(CONFIG_PATH):
            return None
        with open(CONFIG_PATH, "r") as file:
            config_data = json.load(file)
            api_key = config_data.get("api_key")
            return api_key

    @staticmethod
    def open_link(event):
        """Open the provided link in the default web browser."""
        webbrowser.open("https://www.howtogeek.com/885918/how-to-get-an-openai-api-key/")
class AudioRecorder:
    def __init__(self):
        self.is_recording = False
        self.frames = []
        self.p, self.stream = None, None

    def async_record_audio(self):
        CHUNK = 1024
        self.is_recording = True
        self.frames = []
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100,
                        input=True, frames_per_buffer=CHUNK)
        self.p, self.stream = p, stream

        while self.is_recording:
            data = self.stream.read(CHUNK)
            self.frames.append(data)

    def stop_and_save(self, filename):
        self.is_recording = False
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
class AudioTranscriber:
    def __init__(self, api_key):
        openai.api_key = api_key

    def transcribe_audio(self, filename):
        with open(filename, 'rb') as audio_file:
            response = openai.Audio.transcribe("whisper-1", audio_file)
        return response['text']
class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.attributes('-topmost', True)  # Ensure main window is always on top

        self.audio_recorder = AudioRecorder()

        self.api_key = ConfigManager.get_api_key()
        if not self.api_key:
            self.prompt_api_key_input()
            api_key = ConfigManager.get_api_key()

        # Ensure that the audio_transcriber is initialized after the key is provided
        self.audio_transcriber = AudioTranscriber(self.api_key)

        self.setup_ui()
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        x = (event.x_root - self.x - self.root.winfo_rootx() + self.root.winfo_rootx())
        y = (event.y_root - self.y - self.root.winfo_rooty() + self.root.winfo_rooty())
        self.root.geometry("+%s+%s" % (x, y))

    def prompt_api_key_input(self):
        # Use the root itself for the API key prompt

        # Clear any existing widgets from the root window
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("API Key Required")

        def submit_api_key():
            api_key = entry.get().strip()
            if api_key:
                ConfigManager.save_api_key(api_key)
                # Initialize the transcriber with the new key
                self.initialize_transcriber(api_key)
                # Clear the root window again to prepare for the main app UI
                for widget in self.root.winfo_children():
                    widget.destroy()
                self.setup_ui()


        # Label to inform the user about the API key requirement
        tk.Label(self.root, text="The transcription process requires an API key.").pack(pady=10)

        # Link to guide
        link = tk.Label(self.root, text="Click here for a guide on how to get it.", fg="blue", cursor="hand2")
        link.pack(pady=10)
        link.bind("<Button-1>", ConfigManager.open_link)

        # Entry for API key
        tk.Label(self.root, text="Enter your OpenAI API key:").pack(pady=10)
        entry = tk.Entry(self.root, width=50)
        entry.pack(pady=10)

        # Submit button
        tk.Button(self.root, text="Submit", command=submit_api_key).pack(pady=10)

        self.root.mainloop()
    def initialize_transcriber(self, api_key):
        self.audio_transcriber = AudioTranscriber(api_key)
    def toggle_recording(self, event=None):
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

        # Check if the response window should be displayed
        if ENABLE_RESPONSE_WINDOW is True:
            # Display in a separate window using the new ResponseWindow class
            self.response_window = ResponseWindow(self.root, transcription, self.api_key)

        self.set_gif_state('default')

    def set_gif_state(self, state):
        gif_path = GIF_PATHS.get(state)
        if gif_path:
            self.gif_widget.set_gif(gif_path)
            self.gif_widget.play()

    def setup_ui(self):
        self.root.overrideredirect(True)
        self.root.title("Audio Transcription")
        self.root.geometry('150x150')
        self.root.bind('<Escape>', lambda event: self.root.destroy())  # <--- Add this line

        drag_frame = tk.Frame(self.root, bg="black")
        drag_frame.pack(fill=tk.BOTH, expand=True)
        drag_frame.bind('<Button-1>', lambda event: self.toggle_recording())

        self.gif_widget = AnimatedGIF(drag_frame, GIF_PATHS['default'], bg="black")
        self.gif_widget.pack(fill=tk.BOTH, expand=True)
        self.gif_widget.play()
        self.gif_widget.bind('<Button-1>', self.toggle_recording)
        self.gif_widget.bind('<Button-3>', self.start_move)  # Change to Button-3 for right-click
        self.gif_widget.bind("<ButtonRelease-3>", self.stop_move)
        self.gif_widget.bind("<B3-Motion>", self.do_move)  # Change to B3-Motion for right-click drag

    def run(self):
        self.root.mainloop()
class AnimatedGIF(tk.Label):
    def __init__(self, master, path, *args, **kwargs):
        self._photo_images = []  # List to store the PhotoImage objects and prevent garbage collection
        self.frames = []
        self.current_frame = 0  # Initializing current_frame
        self.load_frames(path)
        self._after_id = None  # Initializing _after_id
        super(AnimatedGIF, self).__init__(master, image=self.frames[0], *args, **kwargs)

    def load_frames(self, path):
        im = Image.open(path)
        self.frames.clear()
        self._photo_images.clear()  # Clear the previous images
        self.frames.append(ImageTk.PhotoImage(im.copy()))

        try:
            for i in range(1, 1000):
                im.seek(i)
                self.frames.append(ImageTk.PhotoImage(im.copy()))
        except EOFError:
            pass

    def play(self):
        self.stop()  # Stop any ongoing animation
        self.animate()

    def animate(self):
        if not self.frames:  # Check if frames list is empty
            return
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.config(image=self.frames[self.current_frame])
        self._after_id = self.after(20, self.animate)  # Store the after ID

    def stop(self):
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

    def set_gif(self, path):
        self.load_frames(path)
        self.config(image=self.frames[0])

def run():
    root = tk.Tk()
    app = TranscriptionApp(root)
    app.run()


# Call the standalone run function
run()
