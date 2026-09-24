import gzip
import json
import os
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from settings_store import get_settings
import config_data as cfg


@dataclass
class WeatherResult:
    ok: bool
    location: str
    summary: str
    data: dict
    message: str = ""


class WeatherTool:
    legacy_geo_base_url = "https://geoapi.qweather.com/v2/city/lookup"
    legacy_weather_base_url = "https://devapi.qweather.com/v7/weather/now"

    def __init__(self, timeout=8):
        self.timeout = timeout

    def _decode_response_body(self, raw_body, encoding=""):
        if encoding == "gzip":
            raw_body = gzip.decompress(raw_body)
        return raw_body.decode("utf-8", errors="replace")

    def _format_error_body(self, text):
        if not text:
            return ""
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text
        error = payload.get("error") or {}
        parts = [
            f"code={payload.get('code')}" if payload.get("code") else "",
            f"type={error.get('type')}" if error.get("type") else "",
            f"message={error.get('message')}" if error.get("message") else "",
        ]
        return "，".join(part for part in parts if part) or text

    def _read_error_body(self, error):
        try:
            raw_body = error.read()
            encoding = error.headers.get("Content-Encoding", "")
            return self._format_error_body(self._decode_response_body(raw_body, encoding))
        except Exception:
            return ""

    def _request_json(self, url, headers):
        request = Request(url, headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            **headers,
        })
        with urlopen(request, timeout=self.timeout) as response:
            raw_body = response.read()
            encoding = response.headers.get("Content-Encoding", "")
            return json.loads(self._decode_response_body(raw_body, encoding))

    def _get_json(self, url, api_key):
        try:
            return self._request_json(url, {"X-QW-Api-Key": api_key})
        except HTTPError as first_error:
            separator = "&" if "?" in url else "?"
            fallback_url = f"{url}{separator}{urlencode({'key': api_key})}"
            try:
                return self._request_json(fallback_url, {})
            except HTTPError as second_error:
                body = self._read_error_body(second_error) or self._read_error_body(first_error)
                detail = f"：{body}" if body else ""
                raise ValueError(
                    f"和风天气接口请求失败：HTTP {second_error.code}{detail}。"
                    "请检查 config_data.qweather_api_host 是否为控制台中的 API Host，且 API Key 属于同一个项目。"
                ) from second_error

    def _build_url(self, base_url, params):
        return f"{base_url}?{urlencode(params)}"

    def _get_api_key(self):
        return os.getenv("QWEATHER_API_KEY") or os.getenv("HEFENG_WEATHER_API_KEY") or cfg.qweather_api_key

    def _get_api_host(self):
        return os.getenv("QWEATHER_API_HOST") or os.getenv("HEFENG_WEATHER_API_HOST") or cfg.qweather_api_host

    def _get_base_url(self, path, legacy_url):
        host = self._get_api_host().strip()
        if not host:
            return legacy_url
        host = host.removeprefix("https://").removeprefix("http://").strip("/")
        return f"https://{host}{path}"

    def _resolve_location(self, location, api_key):
        query = str(location or "").strip()
        if not query:
            query = get_settings()["weather"]["default_location"]
        if "," in query:
            return query, query

        payload = self._get_json(self._build_url(self._get_base_url(
            "/geo/v2/city/lookup",
            self.legacy_geo_base_url,
        ), {
            "location": query,
            "lang": "zh",
        }), api_key)
        if payload.get("code") != "200" or not payload.get("location"):
            raise ValueError(f"未找到位置：{query}")

        item = payload["location"][0]
        name = item.get("adm2") or item.get("name") or query
        if item.get("adm1") and item.get("adm1") not in name:
            name = f"{item.get('adm1')} · {name}"
        return item["id"], name

    def _resolve_location_by_ip(self, ip):
        """通过公网 IP 反查城市名称，优先用于浏览器无法定位的场景。"""
        if not ip or ip in ("127.0.0.1", "::1", "localhost"):
            return ""
        # 剔除内网地址
        if ip.startswith(("10.", "172.16.", "172.17.", "172.18.", "172.19.",
                          "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                          "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                          "172.30.", "172.31.", "192.168.")):
            return ""
        try:
            url = f"http://ip-api.com/json/{ip}?fields=city,regionName,country,status&lang=zh-CN"
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=4) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if payload.get("status") == "success" and payload.get("city"):
                region = payload.get("regionName", "")
                city = payload.get("city", "")
                if region and region != city:
                    return f"{city} {region}"
                return city
        except Exception:
            pass
        return ""

    def run(self, location="", client_ip=""):
        api_key = self._get_api_key()
        if not api_key:
            return WeatherResult(
                ok=False,
                location=location or "",
                summary="天气 API Key 未配置。",
                data={},
                message="请先在后端配置 QWEATHER_API_KEY 或 config_data.qweather_api_key。",
            )

        # 未提供位置时，优先尝试 IP 定位（解决公网 HTTP 下浏览器无法获取坐标的问题）
        if not location.strip() and client_ip:
            ip_location = self._resolve_location_by_ip(client_ip)
            if ip_location:
                location = ip_location

        try:
            location_id, display_name = self._resolve_location(location, api_key)
            payload = self._get_json(self._build_url(self._get_base_url(
                "/v7/weather/now",
                self.legacy_weather_base_url,
            ), {
                "location": location_id,
                "lang": "zh",
            }), api_key)
            if payload.get("code") != "200":
                raise ValueError(payload.get("message") or f"和风天气返回状态 {payload.get('code')}")
            now = payload.get("now") or {}
            summary = (
                f"{display_name}当前天气：{now.get('text', '未知')}，"
                f"温度 {now.get('temp', '-')}℃，体感 {now.get('feelsLike', '-')}℃，"
                f"湿度 {now.get('humidity', '-')}%，"
                f"风向 {now.get('windDir', '-')}，风力 {now.get('windScale', '-')}级。"
                f"更新时间：{payload.get('updateTime', '-')}"
            )
            return WeatherResult(
                ok=True,
                location=display_name,
                summary=summary,
                data={
                    "location": display_name,
                    "text": now.get("text", ""),
                    "temp": now.get("temp", ""),
                    "feels_like": now.get("feelsLike", ""),
                    "humidity": now.get("humidity", ""),
                    "wind_dir": now.get("windDir", ""),
                    "wind_scale": now.get("windScale", ""),
                    "update_time": payload.get("updateTime", ""),
                },
            )
        except Exception as error:
            return WeatherResult(
                ok=False,
                location=location or "",
                summary=f"天气查询失败：{error}",
                data={},
                message=str(error),
            )


if __name__ == "__main__":
    result = WeatherTool().run("北京")
    print("ok:", result.ok)
    print("message:", result.message)
    print("summary:", result.summary)
    print("data:", json.dumps(result.data, ensure_ascii=False, indent=2))
