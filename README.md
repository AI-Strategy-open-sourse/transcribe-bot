# transcribe-bot
This project provides tools for audio processing and recognition using Salute Speech and Yandex SpeechKit services. It includes speech recognition features for transcribing audio files.

## Main features
- **Noise Removal** (disabled, not used): To improve audio quality, the ElevenLabs API was used. The audio file is cleared of background noise before transcription, which improves recognition accuracy.
- **Removing Silent Sections with VAD (Voice Activity Detection)**: The Silero VAD module was used to detect and remove silence and minor pauses in audio files. For audio processing, Pydub implemented the functions of converting to mono and changing the sampling frequency to 16000 Hz so that the audio meets the requirements of the VAD model. Used only for Yandex, Salute does not anomaly more after removing silent sections.
- **Format Conversion**: Added automatic conversion of audio files to a format suitable for transcription (mono, 16000 Hz), followed by returning the audio to the original sampling frequency and number of channels.

- **Hallucination filtering**: Removes filler words and stop phrases from recognized text.

## Installation

1. Clone the repository:
   ```bash
   git clone <URL-repo>
   cd transcribe_bot
   ```

2. Create a virtual environment and activate it (Use python 3.11):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `config.py` file in the root of your project and add the following variables:

```python
YANDEX_CLOUD = "<Your API key for Yandex SpeechKit>"
BUCKET_NAME = "<Name of your bucket in Yandex Cloud>"
AWS_ACCESS_KEY_ID = "<Your Access Key ID AWS>"
AWS_SECRET_ACCESS_KEY = "<Your secret access key AWS>"
YANDEX_S3_ENDPOINT_URL = "https://storage.yandexcloud.net"
ELEVENLABS_KEY = "<Your API key for ElevenLabs>"
SALUTE_CLIENT_ID = "<Your client ID for Salute Speech>"
```

## Usage

### Launching the bot

After installing and configuring dependencies, you can launch the fastAPI application:

```bash
python main.py
```

Next, follow the link:

```
http://127.0.0.1:8000/docs
```
