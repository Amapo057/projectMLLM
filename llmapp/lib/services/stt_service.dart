import 'package:speech_to_text/speech_to_text.dart';
import 'package:speech_to_text/speech_recognition_result.dart';

class SttService {
  static final SpeechToText _stt = SpeechToText();
  static bool _initialized = false;

  static Future<bool> init() async {
    if (_initialized) return true;
    _initialized = await _stt.initialize(
      onError: (error) => print('STT 오류: $error'),
    );
    return _initialized;
  }

  static bool get isListening => _stt.isListening;
  static bool get isAvailable => _initialized;

  static Future<void> startListening(Function(String) onResult) async {
    if (!_initialized) await init();
    await _stt.listen(
      onResult: (SpeechRecognitionResult result) {
        if (result.finalResult) onResult(result.recognizedWords);
      },
      localeId: 'ko_KR', // 한국어 인식
      listenOptions: SpeechListenOptions(
        cancelOnError: true,
        partialResults: false,
      ),
    );
  }

  static Future<void> stopListening() async {
    await _stt.stop();
  }
}
