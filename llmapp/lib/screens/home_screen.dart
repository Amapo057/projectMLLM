import 'dart:async';
import 'package:flutter/material.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import '../services/gemini_service.dart';
import '../services/weather_service.dart';
import '../services/bus_service.dart';
import '../services/stt_service.dart';
import '../services/calendar_service.dart';
import '../services/tts_service.dart';
import '../services/wake_word_service.dart';
import '../widgets/orb_painter.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();

  String _response = '';
  bool _isLoading = false;
  bool _isListening = false;
  bool _debugMode = false;
  bool _isStandby = true;

  late WakeWordService _wakeWordService;
  Timer? _standbyTimer;
  static const _sttTimeout = Duration(seconds: 8);

  // ── 생명주기 ────────────────────────────────────────────────
  @override
  void initState() {
    super.initState();
    SttService.init();
    TtsService.init();

    _wakeWordService = WakeWordService(onWakeWordDetected: _exitStandby);

    WidgetsBinding.instance.addPostFrameCallback((_) => _enterStandby());
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _wakeWordService.dispose();
    _standbyTimer?.cancel();
    WakelockPlus.disable();
    super.dispose();
  }

  // ── 대기 모드 ────────────────────────────────────────────────
  Future<void> _enterStandby() async {
    _standbyTimer?.cancel();
    await _wakeWordService.init();
    await WakelockPlus.enable();
    if (mounted) setState(() => _isStandby = true);
  }

  Future<void> _exitStandby() async {
    await _wakeWordService.stop();
    if (!mounted) return;
    setState(() => _isStandby = false);
    await Future.delayed(const Duration(milliseconds: 300));
    _startListeningAndSend();
  }

  // ── 대기 해제 후 STT 자동 시작 ─────────────────────────────
  Future<void> _startListeningAndSend() async {
    if (SttService.isListening) return;

    _standbyTimer?.cancel();
    _standbyTimer = Timer(_sttTimeout, () {
      if (mounted && !_isLoading) _enterStandby();
    });

    setState(() => _isListening = true);
    await SttService.startListening((text) {
      _standbyTimer?.cancel();
      if (!mounted) return;
      setState(() {
        _controller.text = text;
        _isListening = false;
      });
      _send();
    });
  }

  // ── Gemini 전송 ──────────────────────────────────────────────
  Future<void> _send() async {
    final prompt = _controller.text.trim();
    if (prompt.isEmpty) {
      _enterStandby();
      return;
    }

    setState(() {
      _isLoading = true;
      _response = '';
    });

    try {
      String finalPrompt = prompt;

      if (WeatherService.hasWeatherKeyword(prompt)) {
        final weatherSummary = await WeatherService.getSummary();
        if (weatherSummary.isNotEmpty) {
          finalPrompt = '$weatherSummary\n\n위 정보를 참고해서 답해줘: $prompt';
        }
      }

      if (BusService.hasBusKeyword(prompt)) {
        final busSummary = await BusService.getSummary();
        if (busSummary.isNotEmpty) finalPrompt = '$finalPrompt\n$busSummary';
      }

      if (CalendarService.hasCalendarKeyword(prompt)) {
        final calSummary = await CalendarService.getSummary();
        if (calSummary.isNotEmpty) finalPrompt = '$finalPrompt\n$calSummary';
      }

      if (_debugMode) {
        setState(() => _response = '[DEBUG] 최종 프롬프트:\n\n$finalPrompt');
      } else {
        final response = await GeminiService.ask(finalPrompt);
        if (!mounted) return;
        setState(() {
          _response = response;
          _isLoading = false;
        });
        await TtsService.speak(response);
        if (mounted) _enterStandby();
      }
    } finally {
      if (mounted && _isLoading) setState(() => _isLoading = false);
    }
  }

  // ── UI ───────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          if (!_isStandby) _buildRedCircle(),
          if (_debugMode && _response.isNotEmpty) _buildDebugOverlay(),
          _buildCornerButtons(),
        ],
      ),
    );
  }

  // ── 붉은 원 ─────────────────────────────────────────────────
  Widget _buildRedCircle() {
    return Center(
      child: SizedBox(
        width: 200,
        height: 200,
        child: _isLoading
            ? Stack(
                alignment: Alignment.center,
                children: [
                  CustomPaint(
                    size: const Size(200, 200),
                    painter: OrbPainter(),
                  ),
                  const SizedBox(
                    width: 34,
                    height: 34,
                    child: CircularProgressIndicator(
                      color: Colors.white70,
                      strokeWidth: 2.5,
                    ),
                  ),
                ],
              )
            : CustomPaint(
                size: const Size(200, 200),
                painter: OrbPainter(),
              ),
      ),
    );
  }

  // ── 디버그 오버레이 ──────────────────────────────────────────
  Widget _buildDebugOverlay() {
    return Positioned(
      left: 16,
      right: 16,
      bottom: 40,
      height: 220,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white10,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white24),
        ),
        child: SingleChildScrollView(
          controller: _scrollController,
          child: Text(
            _response,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 13,
              height: 1.5,
            ),
          ),
        ),
      ),
    );
  }

  // ── 코너 버튼 ────────────────────────────────────────────────
  Widget _buildCornerButtons() {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            IconButton(
              icon: Icon(
                _isStandby ? Icons.radio_button_off : Icons.nightlight_round,
                color: Colors.white30,
                size: 22,
              ),
              tooltip: _isStandby ? '대기 해제' : '대기 모드',
              onPressed: _isStandby ? _exitStandby : _enterStandby,
            ),
            IconButton(
              icon: Icon(
                _debugMode ? Icons.bug_report : Icons.bug_report_outlined,
                color: _debugMode ? Colors.redAccent : Colors.white30,
                size: 22,
              ),
              tooltip: '디버그 모드',
              onPressed: () => setState(() {
                _debugMode = !_debugMode;
                if (!_debugMode) _response = '';
              }),
            ),
          ],
        ),
      ),
    );
  }
}