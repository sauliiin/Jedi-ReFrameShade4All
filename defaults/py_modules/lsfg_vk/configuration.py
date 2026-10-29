import re
from typing import Any, Dict

from .base_service import BaseService
from .config_schema import ConfigurationManager, ProfileData, UnsupportedConfigurationVersion
from .runtime_service import RuntimeService


class ConfigurationService(BaseService):
    FLATPAK_PROFILE_PREFIX = "flatpak:"
    GAME_PROFILE_PREFIX = "app:"

    def __init__(self, logger=None, runtime_service: RuntimeService = None):
        super().__init__(logger)
        self.runtime_service = runtime_service or RuntimeService(logger=self.log)

    def _default_data(self) -> ProfileData:
        return {"profiles": {}, "global_config": {"dll": "", "no_fp16": False}}

    def _reset_legacy_config(self, version: Any) -> ProfileData:
        data = self._default_data()
        self._remove_if_exists(self.config_file_path)
        content = ConfigurationManager.generate_toml_content_multi_profile(data)
        self._write_file(self.config_file_path, content)
        self.log.warning(
            f"Removed legacy configuration version {version!r}; reset conf.toml to v2 defaults"
        )
        return data

    def _get_profile_data(self) -> ProfileData:
        if not self.config_file_path.exists():
            return self._default_data()
        content = self.config_file_path.read_text(encoding="utf-8")
        try:
            return ConfigurationManager.parse_toml_content_multi_profile(content)
        except UnsupportedConfigurationVersion as error:
            if not ConfigurationManager.is_discardable_legacy_version(error.version):
                raise
            return self._reset_legacy_config(error.version)

    def _save_profile_data(self, data: ProfileData) -> None:
        content = ConfigurationManager.generate_toml_content_multi_profile(data)
        self.runtime_service.validate_config_content(content)
        self._write_file(self.config_file_path, content, 0o644)

    @classmethod
    def game_profile_name(cls, appid: str) -> str:
        """MAKO profile selected by the launch wrapper for a Steam App ID."""
        value = str(appid).strip()
        if not re.fullmatch(r"-?[0-9]+", value):
            raise ValueError("Invalid Steam App ID")
        return f"{cls.GAME_PROFILE_PREFIX}{value}"

    @classmethod
    def _appid_for_profile(cls, name: str):
        match = re.fullmatch(rf"{re.escape(cls.GAME_PROFILE_PREFIX)}(-?[0-9]+)", name)
        return match.group(1) if match else None

    @classmethod
    def flatpak_profile_name(cls, app_id: str) -> str:
        value = str(app_id).strip()
        if not value:
            raise ValueError("Flatpak application ID is required")
        return f"{cls.FLATPAK_PROFILE_PREFIX}{value}"

    @staticmethod
    def _public_config(config: Dict[str, Any]) -> Dict[str, Any]:
        return ConfigurationManager.validate_config(config)

    def get_game_configs(self) -> Dict[str, Any]:
        try:
            data = self._get_profile_data()
            games = []
            for name, raw in data["profiles"].items():
                appid = self._appid_for_profile(name)
                if appid is None:
                    continue
                games.append({"appid": appid, "profile": name, "config": self._public_config(raw)})
            return self._success_response(dict, global_config=dict(data["global_config"]), games=games)
        except Exception as error:
            self.log.error(f"Error reading game configs: {error}")
            return self._error_response(dict, str(error), games=[])

    def update_global_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = self._get_profile_data()
            merged_config = {**data["global_config"], **config}
            validated = self._public_config(merged_config)
            data["global_config"] = {
                "dll": validated["dll"],
                "no_fp16": validated["no_fp16"],
            }
            self._save_profile_data(data)
            return self._success_response(dict, global_config=dict(data["global_config"]))
        except Exception as error:
            return self._error_response(dict, str(error), global_config=None)

    def update_game_config(self, appid: str, game_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = self._get_profile_data()
            name = self.game_profile_name(appid)
            merged_config = {**data["global_config"], **{key: value for key, value in config.items() if key != "no_fp16"}}
            if not config.get("dll"):
                merged_config["dll"] = data["global_config"].get("dll", "")
            validated = self._public_config(merged_config)
            data["profiles"][name] = validated
            self._save_profile_data(data)
            return self._success_response(dict, appid=str(appid), config=validated)
        except Exception as error:
            return self._error_response(dict, str(error), appid=str(appid), config=None)

    def get_flatpak_config(self, app_id: str) -> Dict[str, Any]:
        try:
            data = self._get_profile_data()
            name = self.flatpak_profile_name(app_id)
            raw = data["profiles"].get(name)
            return self._success_response(
                dict,
                app_id=str(app_id),
                profile=name,
                exists=raw is not None,
                config=self._public_config(raw) if raw is not None else None,
                global_config=dict(data["global_config"]),
            )
        except Exception as error:
            return self._error_response(dict, str(error), app_id=str(app_id), config=None, exists=False)

    def update_flatpak_config(self, app_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = self._get_profile_data()
            name = self.flatpak_profile_name(app_id)
            merged_config = {**data["global_config"], **{key: value for key, value in config.items() if key != "no_fp16"}}
            if not config.get("dll"):
                merged_config["dll"] = data["global_config"].get("dll", "")
            validated = self._public_config(merged_config)
            data["profiles"][name] = validated
            self._save_profile_data(data)
            return self._success_response(dict, app_id=str(app_id), profile=name, exists=True, config=validated)
        except Exception as error:
            return self._error_response(dict, str(error), app_id=str(app_id), config=None, exists=False)

    def reset_flatpak_config(self, app_id: str) -> Dict[str, Any]:
        try:
            data = self._get_profile_data()
            name = self.flatpak_profile_name(app_id)
            data["profiles"].pop(name, None)
            self._save_profile_data(data)
            return self._success_response(dict, app_id=str(app_id), profile=name, exists=False)
        except Exception as error:
            return self._error_response(dict, str(error), app_id=str(app_id), config=None, exists=False)

    def reset_all_flatpak_configs(self) -> Dict[str, Any]:
        try:
            data = self._get_profile_data()
            data["profiles"] = {
                name: profile
                for name, profile in data["profiles"].items()
                if not name.startswith(self.FLATPAK_PROFILE_PREFIX)
            }
            self._save_profile_data(data)
            return self._success_response(dict, global_config=dict(data["global_config"]))
        except Exception as error:
            return self._error_response(dict, str(error))

    def reset_game_config(self, appid: str) -> Dict[str, Any]:
        try:
            data = self._get_profile_data()
            data["profiles"].pop(self.game_profile_name(appid), None)
            self._save_profile_data(data)
            return self._success_response(dict, appid=str(appid), exists=False)
        except Exception as error:
            return self._error_response(dict, str(error), appid=str(appid), config=None)

    def reset_game_configs(self, appids: list[str]) -> Dict[str, Any]:
        try:
            if not isinstance(appids, list):
                raise ValueError("appids must be a list")
            requested = set()
            for appid in appids:
                if isinstance(appid, bool) or not isinstance(appid, (str, int)):
                    raise ValueError("appids must contain only strings or integers")
                value = str(appid)
                if not re.fullmatch(r"-?[0-9]+", value):
                    raise ValueError("appids must contain only numeric App IDs")
                requested.add(value)

            data = self._get_profile_data()
            data["profiles"] = {
                name: profile
                for name, profile in data["profiles"].items()
                if self._appid_for_profile(name) not in requested
            }
            self._save_profile_data(data)
            return self._success_response(dict, global_config=dict(data["global_config"]), games=[])
        except Exception as error:
            return self._error_response(dict, str(error), games=[])

    def reset_all_game_configs(self) -> Dict[str, Any]:
        try:
            data = self._get_profile_data()
            data["profiles"] = {
                name: profile
                for name, profile in data["profiles"].items()
                if self._appid_for_profile(name) is None
            }
            self._save_profile_data(data)
            return self._success_response(dict, global_config=dict(data["global_config"]), games=[])
        except Exception as error:
            return self._error_response(dict, str(error), games=[])
