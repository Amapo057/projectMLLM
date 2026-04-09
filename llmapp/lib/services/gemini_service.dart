import 'package:google_generative_ai/google_generative_ai.dart';
import '../config.dart';

class GeminiService {
  static final GenerativeModel _model = GenerativeModel(
    model: 'gemini-3.1-flash-lite-preview',
    apiKey: Config.geminiApiKey,
  );

  static Future<String> ask(String prompt, {int maxRetry = 3}) async {
    for (int i = 0; i < maxRetry; i++) {
      try {
        final result = await _model.generateContent([Content.text(prompt)]);
        return result.text ?? '응답이 없습니다.';
      } catch (e) {
        if (i == maxRetry - 1) return '오류: $e';
        await Future.delayed(Duration(seconds: 2 * (i + 1)));
      }
    }
    return '재시도 초과';
  }
}
