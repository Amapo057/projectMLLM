import datetime
from collections import defaultdict

import requests

import config


class WeatherService2:
    """KMA village forecast based weather context service."""

    URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    NX = config.NX
    NY = config.NY
    START_HOUR = 6
    END_HOUR = 22
    CATEGORIES_PER_HOUR = 12

    SKY = {
        "1": "맑음",
        "3": "구름 많음",
        "4": "흐림",
    }

    PTY = {
        "0": "없음",
        "1": "비",
        "2": "비/눈",
        "3": "눈",
        "4": "소나기",
        "5": "빗방울",
        "6": "빗방울/눈날림",
        "7": "눈날림",
    }

    def __init__(self, nx: int = NX, ny: int = NY):
        self.nx = nx
        self.ny = ny

    def get_weather_context(self) -> str:
        """Fetch KMA forecast data and return a compact prompt context."""
        try:
            items = self._fetch_items()
            forecasts = self._group_by_time(items)
            filtered = self._filter_daytime_forecasts(forecasts)

            if not filtered:
                return "기상청 예보 데이터에서 오늘 오전 6시부터 오후 10시까지의 날씨 정보를 찾지 못했습니다."

            return self._format_context(filtered)
        except Exception:
            return "현재 기상청 날씨 데이터를 가져오는 데 문제가 발생했습니다."

    def _fetch_items(self) -> list[dict]:
        base_date, base_time = self._latest_base_datetime()
        hour_count = self._row_hour_count(base_time)
        num_of_rows = hour_count * self.CATEGORIES_PER_HOUR + 3

        params = {
            "serviceKey": config.API_KEY,
            "pageNo": "1",
            "numOfRows": str(num_of_rows),
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": str(self.nx),
            "ny": str(self.ny),
        }

        response = requests.get(self.URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        header = data.get("response", {}).get("header", {})
        if header.get("resultCode") != "00":
            raise RuntimeError(header.get("resultMsg", "KMA request failed"))

        items = (
            data.get("response", {})
            .get("body", {})
            .get("items", {})
            .get("item", [])
        )
        return items

    def _latest_base_datetime(self) -> tuple[str, str]:
        now = datetime.datetime.now()

        if now.hour > 5 or (now.hour == 5 and now.minute >= 10):
            base_date = now.strftime("%Y%m%d")
            return base_date, "0500"

        yesterday = now - datetime.timedelta(days=1)
        return yesterday.strftime("%Y%m%d"), "2300"

    def _row_hour_count(self, base_time: str) -> int:
        if base_time == "0500":
            return self.END_HOUR - self.START_HOUR + 1

        return self.END_HOUR + 1

    def _group_by_time(self, items: list[dict]) -> dict[tuple[str, str], dict[str, str]]:
        grouped = defaultdict(dict)

        for item in items:
            fcst_date = item.get("fcstDate")
            fcst_time = item.get("fcstTime")
            category = item.get("category")
            value = item.get("fcstValue")

            if not fcst_date or not fcst_time or not category:
                continue

            grouped[(fcst_date, fcst_time)][category] = value

        return dict(grouped)

    def _filter_daytime_forecasts(
        self, forecasts: dict[tuple[str, str], dict[str, str]]
    ) -> list[tuple[str, str, dict[str, str]]]:
        today = datetime.datetime.now().strftime("%Y%m%d")
        result = []

        for (fcst_date, fcst_time), values in sorted(forecasts.items()):
            if fcst_date != today:
                continue

            hour = int(fcst_time[:2])
            if self.START_HOUR <= hour <= self.END_HOUR:
                result.append((fcst_date, fcst_time, values))

        return result

    def _format_context(self, forecasts: list[tuple[str, str, dict[str, str]]]) -> str:
        temperatures = [
            self._to_float(values.get("TMP"))
            for _, _, values in forecasts
            if values.get("TMP") is not None
        ]
        temperatures = [temp for temp in temperatures if temp is not None]

        max_pop = max(
            (
                self._to_int(values.get("POP"))
                for _, _, values in forecasts
                if values.get("POP") is not None
            ),
            default=None,
        )

        summary_parts = ["기상청 단기예보 기준 오늘 오전 6시부터 오후 10시까지의 시간별 날씨입니다."]
        if temperatures:
            summary_parts.append(
                f"예상 기온은 최저 {min(temperatures):g}도, 최고 {max(temperatures):g}도입니다."
            )
        if max_pop is not None:
            summary_parts.append(f"가장 높은 강수확률은 {max_pop}%입니다.")

        lines = []
        for _, fcst_time, values in forecasts:
            line = self._format_hour(fcst_time, values)
            if line:
                lines.append(line)

        return (
            " ".join(summary_parts)
            + "\n"
            + "\n".join(lines)
            + "\n명령: 위 데이터를 바탕으로 사용자에게 오늘 날씨를 짧고 자연스러운 비서 말투로 브리핑하세요. "
            + "비나 눈이 오는 시간대, 기온 변화, 습도나 바람이 불편할 수 있는 시간대를 우선해서 알려주세요."
        )

    def _format_hour(self, fcst_time: str, values: dict[str, str]) -> str:
        hour = int(fcst_time[:2])
        parts = [f"{hour:02d}시"]

        temp = values.get("TMP")
        if temp is not None:
            parts.append(f"{temp}도")

        sky = self.SKY.get(values.get("SKY"))
        if sky:
            parts.append(sky)

        pop = values.get("POP")
        if pop is not None:
            parts.append(f"강수확률 {pop}%")

        pty = values.get("PTY")
        pty_text = self.PTY.get(pty)
        if pty_text and pty_text != "없음":
            parts.append(pty_text)

        pcp = values.get("PCP")
        if pcp and pcp != "강수없음":
            parts.append(f"강수량 {pcp}")

        sno = values.get("SNO")
        if sno and sno != "적설없음":
            parts.append(f"적설 {sno}")

        humidity = values.get("REH")
        if humidity is not None:
            parts.append(f"습도 {humidity}%")

        wind_speed = self._to_float(values.get("WSD"))
        if wind_speed is not None and wind_speed >= 4:
            parts.append(f"바람 {wind_speed:g}m/s")

        return ", ".join(parts)

    def _to_float(self, value: str | None) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def _to_int(self, value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(float(value))
        except ValueError:
            return None


if __name__ == "__main__":
    weather = WeatherService2()
    print(weather.get_weather_context())
