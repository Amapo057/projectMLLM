import 'package:flutter/material.dart';
import '../services/gemini_service.dart';
import '../services/weather_service.dart';
import '../services/bus_service.dart';
import '../services/stt_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();

  String _response = '';
  String _statusMessage = '';
  String _weatherInfo = '';
  bool _isLoading = false;
  bool _isListening = false; // ← STT 상태 추가

  // ── 생명주기 ────────────────────────────────────────────────
  @override
  void initState() {
    super.initState();
    SttService.init(); // 앱 시작 시 STT 초기화
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  // ── STT ─────────────────────────────────────────────────────
  Future<void> _toggleListening() async {
    if (SttService.isListening) {
      await SttService.stopListening();
      setState(() => _isListening = false);
    } else {
      setState(() => _isListening = true);
      await SttService.startListening((text) {
        setState(() {
          _controller.text = text;
          _isListening = false;
        });
        _send(); // 인식 완료 시 자동 전송
      });
    }
  }

  // ── Gemini 전송 ──────────────────────────────────────────────
  Future<void> _send() async {
    final prompt = _controller.text.trim();
    if (prompt.isEmpty) return;

    setState(() {
      _isLoading = true;
      _response = '';
      _statusMessage = '';
      _weatherInfo = '';
    });

    try {
      String finalPrompt = prompt;

      // 날씨 키워드 감지
      if (WeatherService.hasWeatherKeyword(prompt)) {
        setState(() => _statusMessage = '🌤 날씨 키워드 감지됨. Open-Meteo 요청 중…');
        final weatherSummary = await WeatherService.getSummary();

        if (weatherSummary.isNotEmpty) {
          setState(() {
            _weatherInfo = weatherSummary;
            _statusMessage = '✅ 날씨 정보 수신 완료. Gemini에 요청 중…';
          });
          finalPrompt = '$weatherSummary\n\n위 정보를 참고해서 답해줘: $prompt';
        } else {
          setState(() => _statusMessage = '⚠️ 날씨 수신 실패. 날씨 정보 없이 요청 중…');
        }
      }

      // 버스 키워드 감지
      if (BusService.hasBusKeyword(prompt)) {
        setState(() => _statusMessage = '🚌 버스 키워드 감지됨. 도착 정보 요청 중…');
        final busSummary = await BusService.getSummary();

        if (busSummary.isNotEmpty) {
          finalPrompt = '$finalPrompt\n$busSummary';
          setState(() => _statusMessage = '✅ 버스 정보 수신 완료. Gemini에 요청 중…');
        }
      }

      if (!WeatherService.hasWeatherKeyword(prompt) &&
          !BusService.hasBusKeyword(prompt)) {
        setState(() => _statusMessage = 'Gemini에 요청 중…');
      }

      final response = await GeminiService.ask(finalPrompt);
      setState(() {
        _response = response;
        _statusMessage = '';
      });
    } finally {
      setState(() => _isLoading = false);
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeOut,
          );
        }
      });
    }
  }

  // ── UI ───────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: cs.surface,
      appBar: AppBar(
        title: const Text('Gemini AI 비서'),
        backgroundColor: cs.inversePrimary,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 입력창
            TextField(
              controller: _controller,
              minLines: 2,
              maxLines: 5,
              decoration: InputDecoration(
                hintText: '질문을 입력하세요…',
                labelText: '입력',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
                fillColor: cs.surfaceContainerLow,
              ),
            ),
            const SizedBox(height: 12),

            // 확인 버튼 + 마이크 버튼
            Row(
              children: [
                Expanded(
                  child: FilledButton(
                    onPressed: _isLoading ? null : _send,
                    style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2.5),
                          )
                        : const Text('확인', style: TextStyle(fontSize: 16)),
                  ),
                ),
                const SizedBox(width: 8),
                // 마이크 버튼
                IconButton.filled(
                  onPressed: _isLoading ? null : _toggleListening,
                  icon: Icon(_isListening ? Icons.mic : Icons.mic_none),
                  style: IconButton.styleFrom(
                    backgroundColor: _isListening ? Colors.red : null,
                    padding: const EdgeInsets.all(14),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // 상태 메시지
            if (_statusMessage.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  _statusMessage,
                  style: TextStyle(
                    fontSize: 13,
                    color: cs.primary,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),

            // 날씨 정보 박스
            if (_weatherInfo.isNotEmpty)
              Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: cs.primaryContainer,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: cs.primary.withOpacity(0.3)),
                ),
                child: Text(
                  _weatherInfo,
                  style: TextStyle(fontSize: 12, color: cs.onPrimaryContainer),
                ),
              ),

            // 답변 출력
            if (_response.isNotEmpty) ...[
              Text(
                '답변',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                  color: cs.primary,
                ),
              ),
              const SizedBox(height: 8),
              Expanded(
                child: SingleChildScrollView(
                  controller: _scrollController,
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: cs.surfaceContainerLow,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: cs.outlineVariant),
                    ),
                    child: SelectableText(
                      _response,
                      style: const TextStyle(fontSize: 15, height: 1.6),
                    ),
                  ),
                ),
              ),
            ] else if (_isLoading)
              Expanded(
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      CircularProgressIndicator(color: cs.primary),
                      const SizedBox(height: 12),
                      Text(
                        '응답 대기 중…',
                        style: TextStyle(color: cs.onSurfaceVariant),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
