import 'package:flutter_tts/flutter_tts.dart';

class TtsService {
  static final FlutterTts _tts = FlutterTts();
  static bool _initialized = false;

  static Future<void> init() async {
    if (_initialized) return;

    await _tts.setEngine('com.google.android.tts');
    await _tts.setLanguage('ko-KR');
    await _tts.setVoice({'name': 'ko-kr-x-ism-local', 'locale': 'ko-KR'});
    await _tts.setSpeechRate(0.5);
    await _tts.setVolume(0.9);
    await _tts.setPitch(1.0);
    await _tts.setQueueMode(0); // 0: flush, 1: add

    _initialized = true;
  }

  static Future<void> speak(String text) async {
    await init();
    await _tts.stop(); // 이전 발화 중단 후 재생
    await _tts.speak(text);
  }

  static Future<void> stop() async {
    await _tts.stop();
  }
}