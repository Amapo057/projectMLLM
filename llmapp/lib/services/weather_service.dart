import 'dart:convert';
import 'package:http/http.dart' as http;

class WeatherService {
  static const _url =
      'https://api.open-meteo.com/v1/forecast'
      '?latitude=34.9505&longitude=127.4878'
      '&daily=weather_code,temperature_2m_max,temperature_2m_min'
      ',apparent_temperature_min,precipitation_probability_max,precipitation_sum'
      '&timezone=Asia%2FTokyo&past_days=1&forecast_days=1';

  static String _codeToDesc(int code) {
    if (code == 0) return '맑음';
    if (code <= 3) return '구름 조금';
    if (code <= 48) return '안개';
    if (code <= 67) return '비';
    if (code <= 77) return '눈';
    if (code <= 82) return '소나기';
    return '뇌우';
  }

  static Future<String> getSummary() async {
    try {
      final res = await http.get(Uri.parse(_url));
      final data = jsonDecode(res.body)['daily'];
      return '[오늘 순천 날씨] ${data['time'][1]} / '
          '${_codeToDesc(data['weather_code'][1])} / '
          '최고 ${data['temperature_2m_max'][1]}°C '
          '최저 ${data['temperature_2m_min'][1]}°C / '
          '체감 ${data['apparent_temperature_min'][1]}°C / '
          '강수확률 ${data['precipitation_probability_max'][1]}% / '
          '강수량 ${data['precipitation_sum'][1]}mm';
    } catch (e) {
      return '';
    }
  }

  static bool hasWeatherKeyword(String text) {
    const keywords = ['날씨', '기온', '온도', '비', '눈', '흐림', '맑', '우산', '강수'];
    return keywords.any((k) => text.contains(k));
  }
}
