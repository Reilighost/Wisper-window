# 🎙 SOAT: State-of-Art-Transcribing

Transcribe your spoken words into text using OpenAI's API in real-time with this intuitive desktop application.

## 🔍 Overview:

SOAT is a user-friendly audio transcription tool that lets you:

- **Record Audio**: Use your microphone to capture your voice or any audio source.
- **Transcribe**: Leveraging OpenAI's powerful API, the application transcribes the audio to text.
- **Instant Feedback**: Witness the state of the application with dynamic GIF animations.
- **Easy-to-Use GUI**: Interact seamlessly with the tool via an intuitive graphical user interface built with `tkinter`.
- **Manage API Key**: The first-time users are guided to input their OpenAI API key with easy-to-follow instructions and links.

## 🚀 Features:

- **Intuitive GIF Feedback**:
  - The application provides visual feedback using GIF animations based on the current state - whether it's recording, processing, or idle.
  
- **Microphone Selection**:
  - The application automatically selects the default microphone for recording but can be extended for custom microphone selection.
  
- **API Key Management**:
  - For first-time users, the application will prompt to enter the OpenAI API key. The key is stored locally for future sessions.
  
- **Clipboard Integration**:
  - Once transcribed, the text is instantly copied to the clipboard for easy pasting and sharing.

- **Topmost Window**:
  - The application window remains on top for easy access, ensuring a smooth user experience.

## 📦 Requirements:

- Python Libraries: `pyaudio`, `openai`, `tkinter`, `PIL`, `wave`, `pyperclip`, and `webbrowser`.
- OpenAI API Key: The application requires a personal API key from OpenAI for the transcription service.

## 🛠 How to Use:

1. Run the application inside Stable_build folder
2. If using for the first time, you will be prompted to enter your OpenAI API key.
3. Run the application again.
4. Click on the GIF animation to start recording.
5. Click again to stop recording and initiate the transcription.
6. The transcribed text will be copied to your clipboard automatically.

## 📜 License:

This project is open-source. Feel free to use, modify, and distribute as you see fit.