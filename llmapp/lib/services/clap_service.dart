import 'dart:async';
import 'package:detect_clap_sound_flutter/detect_clap_sound_flutter.dart';

class ClapService {
  static final _plugin = DetectClapSoundFlutter();
  static StreamSubscription<int>? _sub;
  static bool _active = false;
  static void Function()? _onClap;

  // ── 더블 박수 감지용 ────────────────────────────────────────
  static int _clapCount = 0;
  static Timer? _windowTimer;

  // 두 박수 사이 인정 최대 간격 (너무 길면 오탐, 너무 짧으면 인식 어려움)
  static const _windowDuration = Duration(milliseconds: 1200);
  // 같은 박수 이벤트 중복 처리 방지 간격
  static const _debounceDuration = Duration(milliseconds: 100);
  static DateTime _lastClapTime = DateTime(0);

  static Future<bool> init(void Function() onClap) async {
    final hasPerm = await _plugin.hasPermission() ?? false;
    if (!hasPerm) {
      final granted = await _plugin.requestPermission() ?? false;
      if (!granted) return false;
    }

    _onClap = onClap;
    _active = true;
    _clapCount = 0;
    _windowTimer?.cancel();

    _sub ??= _plugin.onListenDetectSound().listen((times) {
      if (!_active || times <= 0) return;

      final now = DateTime.now();
      // debounce: 150ms 내 중복 이벤트 무시
      if (now.difference(_lastClapTime) < _debounceDuration) return;
      _lastClapTime = now;

      _clapCount++;

      if (_clapCount == 1) {
        // 첫 번째 박수 → 윈도우 타이머 시작
        _windowTimer?.cancel();
        _windowTimer = Timer(_windowDuration, () {
          // 윈도우 만료 시 카운터 리셋 (단일 박수로 종료)
          _clapCount = 0;
        });
      } else if (_clapCount >= 2) {
        // 두 번째 박수 → 트리거
        _windowTimer?.cancel();
        _clapCount = 0;
        _onClap?.call();
      }
    });

    _plugin.startRecording(
      config: DetectConfig(
        threshold: 15000,              // 기본 30000 → 낮춰서 작은 박수도 감지
        amplitudeSpikeThreshold: 15000, // 기본 28000 → 낮춰서 덜 날카로워도 감지
        stableThreshold: 3000,          // 기본값 유지
        monitorInterval: 50,            // 기본값 유지
        windowSize: 5,                  // 기본값 유지
      ),
    );
    return true;
  }

  static Future<void> stop() async {
    _active = false;
    _clapCount = 0;
    _windowTimer?.cancel();
    await _plugin.stopRecording();
  }

  static void dispose() {
    _active = false;
    _clapCount = 0;
    _windowTimer?.cancel();
    _sub?.cancel();
    _sub = null;
    _plugin.dispose();
  }
}