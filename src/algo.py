import torch
import librosa
import soundfile as sf
import matplotlib.pyplot as plt
from asteroid.models import DCCRNet  # Правильный импорт модели
from scipy.signal import butter, lfilter
import numpy as np

def plot_spectrogram(audio, sr, title):
    plt.figure(figsize=(10, 4))
    D = librosa.amplitude_to_db(np.abs(librosa.stft(audio)), ref=np.max)
    librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log')
    plt.colorbar(format='%+2.0f dB')
    plt.title(title)
    plt.tight_layout()
    plt.show()

def load_audio(input_file, sr=16000):
    y, sr = librosa.load(input_file, sr=sr, mono=True)
    return y, sr

def save_audio(y, sr, output_file):
    try:
        # Убедитесь, что y является 1D или 2D массивом
        if y.ndim == 1:
            channels = 1
        elif y.ndim == 2:
            channels = y.shape[1]
        else:
            raise ValueError("Массив аудио должен быть 1D или 2D.")
        
        # Укажите формат и подтип явно
        sf.write(output_file, y, sr, format='WAV', subtype='PCM_16')
        print(f"Сохранено: {output_file}")
    except Exception as e:
        print(f"Ошибка при сохранении аудио: {e}")

def bandpass_filter(audio, sr, lowcut=300.0, highcut=3000.0, order=4):
    nyquist = 0.5 * sr
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    y = lfilter(b, a, audio)
    return y

def dynamic_range_compression(audio, threshold=0.5, ratio=4.0):
    compressed = np.copy(audio)
    above_threshold = np.abs(audio) > threshold
    compressed[above_threshold] = np.sign(audio[above_threshold]) * (
        threshold + (np.abs(audio[above_threshold]) - threshold) / ratio
    )
    return compressed

def normalize_audio(audio, target_dBFS=-20.0):
    rms = np.sqrt(np.mean(audio**2))
    target_rms = 10**(target_dBFS / 20)
    normalized_audio = audio * (target_rms / rms)
    # Избегаем клиппинга
    normalized_audio = np.clip(normalized_audio, -1.0, 1.0)
    return normalized_audio

def enhance_audio_with_asteroid(input_file, output_file):
    print("Загрузка аудио...")
    y, sr = load_audio(input_file)
    
    print("Визуализация исходной спектрограммы...")
    
    print("Загрузка модели DCCRNet для шумоподавления...")
    try:
        model = DCCRNet.from_pretrained("JorisCos/DCCRNet_Libri1Mix_enhsingle_16k")
    except Exception as e:
        print(f"Ошибка при загрузке модели: {e}")
        return None, None
    
    model.eval()
    
    if torch.cuda.is_available():
        model = model.cuda()
        y_tensor = torch.from_numpy(y).unsqueeze(0).cuda()
    else:
        y_tensor = torch.from_numpy(y).unsqueeze(0)
    
    print("Применение шумоподавления с использованием модели DCCRNet...")
    with torch.no_grad():
        enhanced = model(y_tensor)
    enhanced = enhanced.squeeze().cpu().numpy()
    
    print("Визуализация спектрограммы после шумоподавления...")
    
    print(f"Сохранение улучшенного аудио в {output_file}...")
    save_audio(enhanced, sr, output_file)
    
    return enhanced, sr

def algo(input_audio: str, save_audio_path: str):
    enhanced_audio = "enhanced_DCCRNetet.wav"  # Исправлено название файла
    filtered_audio = f"{input_audio}filtered_audio.wav"
    compressed_audio = f"{input_audio}compressed_audio.wav"
    
    # Шаг 1: Шумоподавление с использованием Asteroid (DCCRNet)
    y_enhanced, sr = enhance_audio_with_asteroid(input_audio, enhanced_audio)
    
    if y_enhanced is None:
        print("Не удалось выполнить шумоподавление.")
        return
    
    # Шаг 2: Полосовая фильтрация
    print("Применение полосового фильтра (300-3000 Гц)...")
    y_filtered = bandpass_filter(y_enhanced, sr, lowcut=300.0, highcut=3000.0, order=4)
    save_audio(y_filtered, sr, filtered_audio)
    
    # Шаг 3: Динамическая компрессия
    print("Применение динамической компрессии...")
    y_compressed = dynamic_range_compression(y_filtered, threshold=0.5, ratio=4.0)
    save_audio(y_compressed, sr, compressed_audio)
    
    # Шаг 4: Нормализация громкости
    print("Нормализация громкости...")
    y_normalized = normalize_audio(y_compressed, target_dBFS=-20.0)
    save_audio(y_normalized, sr, save_audio_path)
    
    print(f"Все этапы обработки завершены. Итоговый файл: {save_audio_path}")
    return save_audio_path
