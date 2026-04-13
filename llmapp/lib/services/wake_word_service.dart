// lib/services/wake_word_service.dart
import 'dart:async';
import 'package:speech_to_text/speech_to_text.dart';

class WakeWordService {
  final Function() onWakeWordDetected;

  static const List<String> _keywords = ['요카이', '유카이', '요카', '욕하', 'youkai'];

  final SpeechToText _stt = SpeechToText();
  bool _isRunning = false;
  Timer? _watchdog; // ← 콜백 대신 주기적 상태 감시

  WakeWordService({required this.onWakeWordDetected});

  Future<void> init() async {
    final available = await _stt.initialize();
    if (!available) return;

    _isRunning = true;
    await _startListening();

    // 1초마다 STT 상태 감시 → 꺼져 있으면 즉시 재시작
    _watchdog = Timer.periodic(const Duration(seconds: 1), (_) async {
      if (_isRunning && !_stt.isListening) {
        print('[WakeWord] STT 꺼짐 감지 → 재시작');
        await _startListening();
      }
    });
  }

  Future<void> _startListening() async {
    if (!_isRunning || _stt.isListening) return;

    await _stt.listen(
      listenFor: const Duration(seconds: 30),
      pauseFor: const Duration(seconds: 6),
      onResult: (result) {
        final text = result.recognizedWords.toLowerCase();
        if (text.isEmpty) return;

        print('[WakeWord] 인식: "$text"');

        if (_keywords.any((kw) => text.contains(kw))) {
          _isRunning = false;
          _watchdog?.cancel();
          _stt.stop();
          onWakeWordDetected();
        }
      },
      listenMode: ListenMode.dictation,
      cancelOnError: false,
    );
  }

  Future<void> stop() async {
    _isRunning = false;
    _watchdog?.cancel();
    await _stt.stop();
  }

  Future<void> dispose() async => stop();
}