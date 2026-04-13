import 'dart:async';                      // ← 추가
import 'package:flutter_tts/flutter_tts.dart';

class TtsService {
  static final FlutterTts _tts = FlutterTts();
  static bool _initialized = false;
  static Completer<void>? _completer;     // ← 추가

  static Future<void> init() async {
    if (_initialized) return;
    await _tts.setLanguage('ko-KR');
    await _tts.setSpeechRate(0.5);
    await _tts.setVolume(1.0);
    await _tts.setPitch(1.0);
    await _tts.setQueueMode(0);

    // ← 추가: 발화 완료 시 Completer 해제
    _tts.setCompletionHandler(() {
      _completer?.complete();
      _completer = null;
    });

    // ← 추가: 에러 발생 시에도 Completer 해제
    _tts.setErrorHandler((msg) {
      _completer?.completeError(msg);
      _completer = null;
    });

    _initialized = true;
  }

  // ← speak() 전체 교체: 발화가 완전히 끝날 때까지 await
  static Future<void> speak(String text) async {
    await init();
    await _tts.stop();
    _completer = Completer<void>();
    await _tts.speak(text);
    await _completer!.future;   // 발화 완료까지 대기
  }

  static Future<void> stop() async {
    _completer?.complete();     // ← 추가: stop 시 Completer도 해제
    _completer = null;
    await _tts.stop();
  }
}