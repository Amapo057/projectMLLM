# services/weather_service.py
import requests

class WeatherService:
    def __init__(self):
        self.url = (
            "https://api.open-meteo.com/v1/forecast?"
            "latitude=34.9505&longitude=127.4878&"
            "daily=weather_code,temperature_2m_max,temperature_2m_min,"
            "apparent_temperature_min,precipitation_probability_max,precipitation_sum&"
            "timezone=Asia%2FTokyo&past_days=1&forecast_days=1"
        )

    def get_weather_context(self) -> str:
        """Open-Meteo API를 호출하여 어제와 오늘의 날씨 비교 컨텍스트를 반환합니다."""
        try:
            response = requests.get(self.url, timeout=5)
            response.raise_for_status()
            data = response.json()

            daily = data.get("daily", {})
            
            # --- [어제 날씨 데이터 (index 0)] ---
            yest_temp_max = daily.get("temperature_2m_max", [])[0]
            yest_temp_min = daily.get("temperature_2m_min", [])[0]

            # --- [오늘 날씨 데이터 (index -1)] ---
            today_code = daily.get("weather_code", [])[-1]
            today_temp_max = daily.get("temperature_2m_max", [])[-1]
            today_temp_min = daily.get("temperature_2m_min", [])[-1]
            today_app_temp_min = daily.get("apparent_temperature_min", [])[-1]
            today_precip_prob = daily.get("precipitation_probability_max", [])[-1]

            weather_desc = self._decode_weather_code(today_code)
            
            # 제미나이에게 전달될 '행동 지침'이 포함된 프롬프트 컨텍스트 조립
            context = (
                f"현재 위치는 순천시이며, 오늘 날씨는 '{weather_desc}'입니다. "
                f"[어제 기온] 최고: {yest_temp_max}도, 최저: {yest_temp_min}도. "
                f"[오늘 기온] 최고: {today_temp_max}도, 최저: {today_temp_min}도, 아침 최저 체감: {today_app_temp_min}도. "
                f"[강수 확률] {today_precip_prob}%. "
                f"명령: 위 데이터를 바탕으로 어제와 오늘의 기온 차이를 비교하여 "
                f"'오늘의 최저 기온은 ~도이고, 최고 기온은 ~도입니다. 어제보다 ~해서 춥네요/따뜻하네요' 같은 자연스러운 비서의 말투로 날씨를 브리핑해주세요."
            )
            return context

        except Exception as e:
            # print(f"[Weather Error] 날씨 조회 실패: {e}")
            return "현재 날씨 데이터를 가져오는 데 문제가 발생했습니다."

    def _decode_weather_code(self, code: int) -> str:
        # ... 기존 코드 동일 ...
        if code == 0: return "맑음"
        elif code in [1, 2, 3]: return "구름 조금/흐림"
        elif code in [45, 48]: return "안개"
        elif code in [51, 53, 55, 56, 57]: return "이슬비"
        elif code in [61, 63, 65, 66, 67]: return "비"
        elif code in [71, 73, 75, 77]: return "눈"
        elif code in [80, 81, 82]: return "소나기"
        elif code in [95, 96, 99]: return "뇌우(천둥번개)"
        return "알 수 없는 날씨"