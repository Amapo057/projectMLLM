import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';

class BusService {
  static const _cityCode = '36030';
  static const _nodeId = 'SCB326009952';

  // 캐시
  static DateTime? _lastFetch;
  static String _cached = '';

  static Future<String> getSummary() async {
    // 30초 이내면 캐시 반환
    if (_lastFetch != null &&
        DateTime.now().difference(_lastFetch!).inSeconds < 30 &&
        _cached.isNotEmpty) {
      return '$_cached (캐시)';
    }

    try {
      final uri = Uri.parse(
        'http://apis.data.go.kr/1613000/ArvlInfoInqireService'
        '/getSttnAcctoArvlPrearngeInfoList'
        '?serviceKey=${Config.busApiKey}'
        '&cityCode=$_cityCode'
        '&nodeId=$_nodeId'
        '&_type=json',
      );

      final res = await http.get(uri);
      final items =
          jsonDecode(res.body)['response']['body']['items']['item'] as List;

      // 71이 포함된 버스만 필터
      final filtered = items.where((item) {
        final no = item['routeno'].toString();
        return no.contains('71');
      }).toList();

      if (filtered.isEmpty) {
        _cached = '[버스 정보] 71번 계열 버스 도착 정보 없음';
      } else {
        // 도착시간 오름차순 정렬
        filtered.sort(
          (a, b) => (a['arrtime'] as int).compareTo(b['arrtime'] as int),
        );

        final lines = filtered
            .map((item) {
              final no = item['routeno'].toString();
              final min = (item['arrtime'] as int) < 60
                  ? '잠시 후'
                  : '${((item['arrtime'] as int) / 60).round()}분 후';
              final stops = item['arrprevstationcnt'];
              return '$no번 → $min ($stops정거장 전)';
            })
            .join(' / ');

        _cached = '[부영3차.팔마중 71번 계열] $lines';
      }

      _lastFetch = DateTime.now();
      return _cached;
    } catch (e) {
      return '';
    }
  }

  static bool hasBusKeyword(String text) {
    const keywords = ['버스', '정류장', '몇 분', '몇분', '언제 와', '언제와'];
    return keywords.any((k) => text.contains(k));
  }
}
