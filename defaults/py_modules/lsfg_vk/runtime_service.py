import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Sequence

from .base_service import BaseService
from .config_schema import ConfigurationManager
from .constants import CLI_FILENAME, LOSSLESS_DLL_FILENAME


class RuntimeService(BaseService):
    COMMAND_TIMEOUT_SECONDS = 10
    MAX_OUTPUT_LENGTH = 12_000
    # Variables that would make mako-cli read another profile source.
    IGNORED_ENVIRONMENT = ("MAKO_CONFIG", "MAKO_ENV", "MAKO_PROFILE", "MAKO_PROFILE_FALLBACK")

    def _environment(self) -> dict[str, str]:
        environment = self._host_environment()
        for name in self.IGNORED_ENVIRONMENT:
            environment.pop(name, None)
        return environment

    @classmethod
    def _output(cls, stdout: Any, stderr: Any) -> str:
        values = []
        for value in (stdout, stderr):
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="replace")
            if value:
                values.append(str(value).strip())
        output = "\n".join(value for value in values if value)
        return output if len(output) <= cls.MAX_OUTPUT_LENGTH else output[: cls.MAX_OUTPUT_LENGTH]

    def _run(self, arguments: Sequence[str]) -> tuple[int, str]:
        if not self.cli_path.is_file() or not os.access(self.cli_path, os.X_OK):
            raise FileNotFoundError(f"{CLI_FILENAME} is not installed at {self.cli_path}")
        result = subprocess.run(
            [str(self.cli_path), *arguments],
            cwd=str(self.user_home),
            env=self._environment(),
            capture_output=True,
            text=True,
            timeout=self.COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
        return result.returncode, self._output(result.stdout, result.stderr)

    def validate_config_content(self, content: str) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.config_dir,
                prefix=".conf.toml.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(content)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            returncode, output = self._run(("validate", "--config", str(temporary_path)))
            if returncode != 0:
                raise ValueError(output or "MAKO Renderer rejected the generated configuration")
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def check_lossless_scaling(self) -> dict[str, Any]:
        """Report whether the configured Lossless.dll is readable."""
        if not self.config_file_path.is_file():
            return {"installed": False, "status": "Configuration is not installed"}
        try:
            data = ConfigurationManager.parse_toml_content_multi_profile(
                self.config_file_path.read_text(encoding="utf-8")
            )
        except Exception as error:
            return {"installed": False, "status": str(error)}
        dll = data["global_config"].get("dll") or ""
        if not dll:
            return {"installed": False, "status": f"Lossless Scaling's {LOSSLESS_DLL_FILENAME} was not found"}
        if not Path(dll).is_file():
            return {"installed": False, "status": f"{LOSSLESS_DLL_FILENAME} does not exist: {dll}"}
        return {"installed": True, "status": "Lossless Scaling detected"}
