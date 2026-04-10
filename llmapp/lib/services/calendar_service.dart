import 'package:device_calendar_plus/device_calendar_plus.dart';

class CalendarService {
  static final _plugin = DeviceCalendar.instance;

  static Future<String> getSummary() async {
    try {
      final permission = await _plugin.requestPermissions();
      print('캘린더 권한: $permission');   // ← 추가

      if (permission != CalendarPermissionStatus.granted) {
        print('권한 거부됨: $permission');  // ← 추가
        return '';
      }

      final now = DateTime.now();
      final end = now.add(const Duration(days: 7));
      final events = await _plugin.listEvents(now, end);
      print('이벤트 수: ${events.length}');  // ← 추가

      if (events.isEmpty) return '[일정] 향후 7일간 일정 없음';

      final lines = events.map((e) {
        final date = '${e.startDate.month}/${e.startDate.day}';
        final time = e.isAllDay
            ? '종일'
            : '${e.startDate.hour.toString().padLeft(2, '0')}:'
              '${e.startDate.minute.toString().padLeft(2, '0')}';
        return '$date $time ${e.title}';
      }).join(', ');

      return '[향후 7일 일정] $lines';
    } catch (e) {
      print('캘린더 오류: $e');   // ← 기존 return '' 대신 출력
      return '';
    }
  }

  static bool hasCalendarKeyword(String text) {
    const keywords = ['일정', '스케줄', '약속', '캘린더', '오늘 뭐', '내일 뭐'];
    return keywords.any((k) => text.contains(k));
  }
}