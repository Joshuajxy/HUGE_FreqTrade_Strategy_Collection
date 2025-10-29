"""Backtest executor"""
import subprocess
import sys
import json
import tempfile
import time
import threading
import zipfile
import shutil
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
from uuid import uuid4

import pandas as pd

from utils.data_models import (
    BacktestConfig,
    BacktestResult,
    PerformanceMetrics,
    ExecutionStatus,
    TradeRecord,
)
from utils.error_handling import ErrorHandler, ExecutionError, error_handler
from components.results.parser import ResultParser

class BacktestExecutor:
    """Backtest executor"""

    _data_lock = threading.Lock()
    
    def __init__(self, freqtrade_path: str = "freqtrade"):
        """
        Initialize executor
        
        Args:
            freqtrade_path: freqtrade command path
        """
        self.freqtrade_path = freqtrade_path
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        self.user_data_dir = Path("user_data")
        self.user_data_dir.mkdir(exist_ok=True)
        (self.user_data_dir / "data").mkdir(exist_ok=True)
        (self.user_data_dir / "strategies").mkdir(exist_ok=True)
        (self.user_data_dir / "plot").mkdir(exist_ok=True)
        self.exchange = "binance"
        self.data_dir = self.user_data_dir / "data" / self.exchange
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.freqtrade_available = False
        self._run_metadata_lock = threading.Lock()
        
        # Validate freqtrade availability
        self._validate_freqtrade()
    
    def _validate_freqtrade(self):
        """Validate freqtrade availability"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "freqtrade", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                ErrorHandler.log_info(f"Freqtrade validation successful: {result.stdout.strip()}")
                self.freqtrade_available = True
            else:
                raise ExecutionError(f"Freqtrade validation failed: {result.stderr}")
        
        except FileNotFoundError:
            self.freqtrade_available = False
            ErrorHandler.log_warning(f"Freqtrade command not found: {self.freqtrade_path}")
            ErrorHandler.log_info("To install freqtrade, run: pip install freqtrade")
            raise ExecutionError(f"Freqtrade command not found: {self.freqtrade_path}\n💡 Install with: pip install freqtrade")
        
        except subprocess.TimeoutExpired:
            self.freqtrade_available = False
            raise ExecutionError("Freqtrade command timeout")
        
        except Exception as e:
            self.freqtrade_available = False
            raise ExecutionError(f"Freqtrade validation failed: {str(e)}")

    def _load_run_metadata(self, metadata_path: Path) -> Dict[str, Any]:
        """Safely load run metadata from disk."""
        if metadata_path.exists():
            try:
                return json.loads(metadata_path.read_text(encoding='utf-8'))
            except Exception as exc:
                ErrorHandler.log_warning(f"Failed to read run metadata {metadata_path.name}: {exc}")
        return {}

    def _write_run_metadata(self, metadata_path: Path, metadata: Dict[str, Any]) -> None:
        """Persist run metadata with automatic timestamp update."""
        metadata['last_updated'] = datetime.now().isoformat()
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')

    def _update_strategy_metadata(self, run_dir: Path, strategy_name: str, updates: Dict[str, Any]) -> None:
        """Update metadata entry for a specific strategy within a run."""
        metadata_path = run_dir / "run_metadata.json"
        with self._run_metadata_lock:
            metadata = self._load_run_metadata(metadata_path)
            metadata.setdefault("strategies", [])
            if strategy_name not in metadata["strategies"]:
                metadata["strategies"].append(strategy_name)

            results = metadata.setdefault("results", {})
            strategy_record = results.setdefault(strategy_name, {})
            strategy_record.update(updates)

            self._finalize_run_status(metadata)
            self._write_run_metadata(metadata_path, metadata)

    def _finalize_run_status(self, metadata: Dict[str, Any]) -> None:
        """Update overall run status based on individual strategy statuses."""
        strategies = metadata.get("strategies", [])
        results = metadata.get("results", {})
        if not strategies:
            metadata["status"] = "running"
            return

        statuses = [results.get(name, {}).get("status") for name in strategies]
        if statuses and all(status in {ExecutionStatus.COMPLETED.value, ExecutionStatus.FAILED.value} for status in statuses):
            metadata["status"] = "completed"
            metadata.setdefault("completed_at", datetime.now().isoformat())
        else:
            metadata["status"] = "running"
            metadata.pop("completed_at", None)

    def _ensure_run_directory(self, config: BacktestConfig, strategy_name: Optional[str] = None) -> Path:
        """Ensure run directory exists and baseline metadata is recorded."""
        with self._run_metadata_lock:
            if not config.run_id:
                config.run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")

            base_dir = self.user_data_dir / "backtest_results"
            run_dir = base_dir / config.run_id
            run_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = run_dir / "run_metadata.json"
            metadata = self._load_run_metadata(metadata_path)

            if not metadata:
                metadata = {
                    "run_id": config.run_id,
                    "created_at": datetime.now().isoformat(),
                    "config": config.to_dict(),
                    "strategies": [],
                    "results": {},
                    "status": "running"
                }
            else:
                metadata.setdefault("config", config.to_dict())
                metadata.setdefault("strategies", [])
                metadata.setdefault("results", {})
                metadata.setdefault("status", "running")

            if strategy_name and strategy_name not in metadata["strategies"]:
                metadata["strategies"].append(strategy_name)

            strategy_record = metadata["results"].setdefault(strategy_name, {}) if strategy_name else None
            if strategy_record is not None:
                strategy_record.setdefault("strategy_name", strategy_name)
                strategy_record.setdefault("status", ExecutionStatus.RUNNING.value)
                strategy_record.setdefault("started_at", datetime.now().isoformat())

            metadata.setdefault("logs", {})
            self._write_run_metadata(metadata_path, metadata)

        return run_dir

    def _get_run_directory(self, config: BacktestConfig) -> Optional[Path]:
        """Return run directory if run_id is present and directory exists."""
        if not config.run_id:
            return None
        run_dir = self.user_data_dir / "backtest_results" / config.run_id
        return run_dir if run_dir.exists() else None

    def _timeframe_to_minutes(self, timeframe: str) -> Optional[int]:
        """Convert timeframe string to minutes."""
        try:
            if timeframe.endswith("m"):
                return int(timeframe[:-1])
            if timeframe.endswith("h"):
                return int(timeframe[:-1]) * 60
            if timeframe.endswith("d"):
                return int(timeframe[:-1]) * 1440
            if timeframe.endswith("w"):
                return int(timeframe[:-1]) * 10080
        except ValueError:
            return None
        return None

    def _estimate_expected_bars(self, config: BacktestConfig) -> Optional[int]:
        """Estimate expected number of candles for the configured timerange."""
        timeframe_minutes = self._timeframe_to_minutes(config.timeframe)
        if not timeframe_minutes:
            return None
        start_dt = datetime.combine(config.start_date, datetime.min.time())
        end_dt = datetime.combine(config.end_date, datetime.min.time())
        if end_dt <= start_dt:
            return None
        total_minutes = (end_dt - start_dt).total_seconds() / 60
        return max(0, int(total_minutes // timeframe_minutes))

    def _get_data_file_path(self, pair: str, timeframe: str) -> Path:
        """Return the expected feather file path for a pair/timeframe."""
        file_name = f"{pair.replace('/', '_')}-{timeframe}.feather"
        return self.data_dir / file_name

    def _check_data_integrity(self, config: BacktestConfig) -> Tuple[bool, list[str]]:
        """Validate downloaded data files."""
        issues: list[str] = []
        expected_bars = self._estimate_expected_bars(config)

        for pair in config.pairs:
            file_path = self._get_data_file_path(pair, config.timeframe)
            if not file_path.exists():
                issues.append(f"{pair} 缺少数据文件：{file_path.name}")
                continue

            if file_path.stat().st_size < 1024:
                issues.append(f"{pair} 数据文件大小异常：{file_path.name}")
                continue

            try:
                data = pd.read_feather(file_path)
            except Exception as exc:
                issues.append(f"{pair} 数据读取失败：{exc}")
                continue

            bars = len(data)
            if expected_bars and bars < max(20, int(expected_bars * 0.6)):
                issues.append(f"{pair} 数据量不足：预期不少于 {expected_bars} 条，实际 {bars} 条")

        return len(issues) == 0, issues

    def _cleanup_corrupt_data_files(self, config: BacktestConfig, issues: list[str]) -> None:
        """Remove problematic data files to allow fresh download."""
        if not issues:
            return

        for pair in config.pairs:
            file_path = self._get_data_file_path(pair, config.timeframe)
            if not file_path.exists():
                continue

            remove_file = False
            if file_path.stat().st_size < 1024:
                remove_file = True
            else:
                for issue in issues:
                    if pair in issue:
                        remove_file = True
                        break

            if remove_file:
                try:
                    file_path.unlink()
                    ErrorHandler.log_warning(f"已删除异常数据文件：{file_path.name}")
                except Exception as exc:
                    ErrorHandler.log_warning(f"删除异常数据文件失败 {file_path.name}：{exc}")

    def ensure_data_ready(self, config: BacktestConfig) -> Tuple[bool, list[str]]:
        """Ensure historical data exists and is usable before execution."""
        ready, issues = self._check_data_integrity(config)
        if ready:
            return True, []

        try:
            self._ensure_data_downloaded(config)
        except ExecutionError as exc:
            return False, [str(exc)]

        return self._check_data_integrity(config)

    def _ensure_data_downloaded(self, config: BacktestConfig):
        """Download historical data if needed with concurrency protection."""
        try:
            with self._data_lock:
                ready, issues = self._check_data_integrity(config)
                if ready:
                    ErrorHandler.log_info("历史数据已准备就绪，跳过下载步骤。")
                    return True

                cleanup_required = bool(issues)
                if cleanup_required:
                    self._cleanup_corrupt_data_files(config, issues)

                ready_after_cleanup, cleanup_issues = self._check_data_integrity(config)
                if ready_after_cleanup:
                    ErrorHandler.log_info("清理异常数据后数据完整，跳过下载步骤。")
                    return True

                ErrorHandler.log_info("Ensuring historical data is available...")
                print("\n📥 Ensuring historical data is available...")

                cmd = [
                    sys.executable, "-m", "freqtrade",
                    "download-data",
                    "--exchange", self.exchange,
                    "-t", config.timeframe,
                    "--pairs", *config.pairs,
                    "--timerange", f"{config.start_date.strftime('%Y%m%d')}-{config.end_date.strftime('%Y%m%d')}"
                ]

                if cleanup_required or cleanup_issues:
                    cmd.append("--erase")

                ErrorHandler.log_info(f"Executing data download command: {' '.join(cmd)}")
                print(f"🔩 Executing command: {' '.join(cmd)}")

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    universal_newlines=True
                )

                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if line:
                        print(f"   {line}")
                        ErrorHandler.log_info(f"DATA_DOWNLOAD: {line}")

                process.wait()

                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, cmd, "Data download script failed.")

                ready_after, issues_after = self._check_data_integrity(config)
                if not ready_after:
                    joined = "；".join(issues_after)
                    raise ExecutionError(f"数据下载完成但完整性校验失败：{joined}")

                print("✅ Data download check completed successfully.")
                ErrorHandler.log_info("Successfully ensured data is available for backtest.")
                return True
        except subprocess.CalledProcessError as e:
            error_msg = f"Data download failed with return code {e.returncode}."
            print(f"❌ {error_msg}")
            ErrorHandler.log_error(error_msg)
            raise ExecutionError(error_msg) from e
        except ExecutionError:
            raise
        except Exception as e:
            error_msg = f"An unknown error occurred during data download: {e}"
            print(f"❌ {error_msg}")
            ErrorHandler.log_error(error_msg)
            raise ExecutionError(error_msg) from e

    @error_handler(ExecutionError, show_error=False)
    def execute_backtest(self, task_id: str, strategy_info: "StrategyInfo", config: BacktestConfig) -> BacktestResult:
        """
        Execute backtest with detailed logging, ensuring data is downloaded first.
        
        Args:
            task_id: The unique ID for this execution task.
            strategy_info: strategy information object
            config: backtest configuration
            
        Returns:
            backtest result
        """
        from utils.data_models import StrategyInfo # For type hint
        start_time = time.time()
        strategy_name = strategy_info.name
        run_dir = self._ensure_run_directory(config, strategy_name)
        run_start_time = datetime.now().isoformat()
        self._update_strategy_metadata(run_dir, strategy_name, {
            "task_id": task_id,
            "status": ExecutionStatus.RUNNING.value,
            "started_at": run_start_time
        })

        try:
            # Step 1: Ensure data is downloaded
            self._ensure_data_downloaded(config)

            # Step 2: Proceed with backtest execution
            log_line = f"🏁 STARTING BACKTEST EXECUTION: {strategy_name}"
            print(f"\n{log_line}")
            ErrorHandler.log_info(log_line)

            # Log configuration details
            config_info = f"Backtest config - Timeframe: {config.timeframe}, Pairs: {len(config.pairs)}, Start: {config.start_date}, End: {config.end_date}"
            print(f"📊 CONFIG: {config_info}")
            ErrorHandler.log_info(config_info)
            
            # Create temporary configuration file and prepare export targets
            archive_dir = None
            export_filename: Optional[Path] = None
            if run_dir:
                archive_dir = run_dir / "results" / "archives"
                archive_dir.mkdir(parents=True, exist_ok=True)

            timestamp_token = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_token = uuid4().hex[:8]
            safe_strategy = strategy_name.replace("/", "-").replace("\\", "-")
            export_basename = f"{safe_strategy}_{timestamp_token}_{unique_token}.zip"
            if archive_dir:
                export_filename = archive_dir / export_basename
            else:
                export_filename = Path("user_data/backtest_results") / export_basename

            config_file = self._create_temp_config(strategy_name, config, export_filename)

            # Track existing export archives so we can identify the fresh one later
            existing_exports = self._collect_export_files()

            # Execute freqtrade backtest
            output = self._run_freqtrade_backtest_with_logging(
                task_id,
                strategy_info,
                config_file,
                export_filename,
            )

            # Persist backtest stdout to file and re-parse from file
            output_file = self._persist_raw_output(strategy_name, output, run_dir=run_dir)
            result = None
            summary_file: Optional[Path] = None
            timestamp_override: Optional[str] = None

            archive_path: Optional[Path] = None
            effective_export_path: Optional[Path] = None
            if run_dir:
                effective_export_path = self._resolve_export_zip(
                    export_filename,
                    existing_exports,
                    run_dir,
                    strategy_name,
                )

            if effective_export_path and run_dir:
                export_payload = self._load_result_from_freqtrade_export(
                    effective_export_path, strategy_name, config, run_dir
                )
                if export_payload:
                    result, summary_file, timestamp_override = export_payload
                    ErrorHandler.log_info(
                        f"Loaded backtest metrics for {strategy_name} from freqtrade export {effective_export_path.name}"
                    )
                if effective_export_path.exists():
                    archive_path = effective_export_path

            if result is None:
                parser = ResultParser()
                if output_file and output_file.exists():
                    result = parser.parse_backtest_file(output_file, strategy_name, config)
                    result.source_file = str(output_file)
                    result_path = self._persist_parsed_result(result, output_file, run_dir=run_dir)
                else:
                    result = parser.parse_backtest_output(output, strategy_name, config)
                    result_path = self._persist_parsed_result(result, None, run_dir=run_dir)
            else:
                result_path = self._persist_parsed_result(
                    result,
                    summary_file,
                    run_dir=run_dir,
                    timestamp_override=timestamp_override,
                )

            # Set execution time
            result.execution_time = time.time() - start_time
            result.status = ExecutionStatus.COMPLETED

            metrics_summary = {
                "total_return_pct": result.metrics.total_return_pct,
                "win_rate": result.metrics.win_rate,
                "max_drawdown_pct": result.metrics.max_drawdown_pct,
                "sharpe_ratio": result.metrics.sharpe_ratio,
                "sortino_ratio": result.metrics.sortino_ratio,
                "total_trades": result.metrics.total_trades
            }

            self._update_strategy_metadata(run_dir, strategy_name, {
                "status": ExecutionStatus.COMPLETED.value,
                "completed_at": datetime.now().isoformat(),
                "execution_time": result.execution_time,
                "result_path": str(result_path.relative_to(run_dir)) if run_dir and result_path else None,
                "archive_path": str(archive_path.relative_to(run_dir)) if run_dir and archive_path else None,
                "metrics": metrics_summary,
                "error_message": None
            })

            success_msg = f"Backtest execution completed: {strategy_name} (Time: {result.execution_time:.2f}s, Return: {result.metrics.total_return_pct:.2f}%)"
            print(f"✅ {success_msg}")
            ErrorHandler.log_info(success_msg)
            return result
        
        except Exception as e:
            # The error (including from data download) is caught here
            ErrorHandler.log_error(f"Backtest execution failed for {strategy_name}: {str(e)}")
            self._update_strategy_metadata(run_dir, strategy_name, {
                "status": ExecutionStatus.FAILED.value,
                "completed_at": datetime.now().isoformat(),
                "execution_time": time.time() - start_time,
                "error_message": str(e)
            })
            
            # Create error result
            error_result = BacktestResult(
                strategy_name=strategy_name,
                config=config,
                metrics=PerformanceMetrics(),
                trades=[],
                timestamp=datetime.now(),
                execution_time=time.time() - start_time,
                error_message=str(e),
                status=ExecutionStatus.FAILED
            )
            
            return error_result
        
        finally:
            # Clean up temporary files
            self._cleanup_temp_files()
    
    def _create_temp_config(
        self,
        strategy_name: str,
        config: BacktestConfig,
        export_filename: Optional[Path] = None,
    ) -> Path:
        """Create temporary configuration file"""
        try:
            # Convert to freqtrade configuration format and add modern pairlist handling
            base_config = config.to_freqtrade_config(strategy_name)
            
            # The 'pairs' key is now handled within 'pairlists'
            pairs = base_config.pop("pairs", [])

            freqtrade_config = {
                "pairlists": [
                    {"method": "StaticPairList", "pairs": pairs}
                ],
                **base_config
            }
            
            # Add additional required configurations
            freqtrade_config.update({
                "datadir": str(self.user_data_dir / "data"),
                "user_data_dir": str(self.user_data_dir),
                "logfile": f"logs/freqtrade_{strategy_name}.log",
                "db_url": f"sqlite:///tradesv3_{strategy_name}.sqlite",
                # strategy_path is now handled by the command line argument
                "export": "trades"
            })

            if export_filename is not None:
                freqtrade_config["exportfilename"] = export_filename.as_posix()
            
            # Create temporary configuration file
            config_file = self.temp_dir / f"config_{strategy_name}_{int(time.time())}.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(freqtrade_config, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Temporary configuration file created: {config_file}")
            return config_file
        
        except Exception as e:
            raise ExecutionError(f"Failed to create temporary configuration: {str(e)}")


    def _persist_raw_output(self, strategy_name: str, output: str, run_dir: Optional[Path] = None) -> Path:
        """Persist raw freqtrade stdout to timestamped log file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if run_dir:
                logs_dir = run_dir / "logs"
            else:
                logs_dir = self.user_data_dir / "backtest_logs"
            logs_dir.mkdir(parents=True, exist_ok=True)

            file_path = logs_dir / f"{strategy_name}_{timestamp}.log"

            file_path.write_text(output, encoding='utf-8')
            ErrorHandler.log_info(f"Raw backtest output saved to {file_path}")

            if run_dir:
                metadata_path = run_dir / "run_metadata.json"
                with self._run_metadata_lock:
                    metadata = self._load_run_metadata(metadata_path)
                    metadata.setdefault("logs", {})
                    metadata["logs"][strategy_name] = {
                        "path": str(file_path.relative_to(run_dir)),
                        "timestamp": timestamp
                    }
                    self._write_run_metadata(metadata_path, metadata)

            return file_path
        except Exception as exc:
            ErrorHandler.log_warning(f"Failed to persist raw output for {strategy_name}: {exc}")
            return Path()

    def _persist_parsed_result(
        self,
        result: BacktestResult,
        output_file: Optional[Path],
        run_dir: Optional[Path] = None,
        timestamp_override: Optional[str] = None,
    ) -> Optional[Path]:
        """Persist parsed BacktestResult to JSON for later analysis."""
        try:
            if run_dir:
                results_dir = run_dir / "results"
            else:
                results_dir = self.user_data_dir / "backtest_results"
            results_dir.mkdir(parents=True, exist_ok=True)

            timestamp = timestamp_override or ""
            if output_file and output_file.stem:
                name = output_file.stem
                match = re.search(r"(\d{4}-\d{2}-\d{2})[_-](\d{2}-\d{2}-\d{2})", name)
                if match:
                    timestamp = match.group(1).replace("-", "") + "_" + match.group(2).replace("-", "")
                else:
                    parts = name.split("_")
                    if len(parts) >= 2 and not timestamp:
                        timestamp = parts[-1]
            if not timestamp:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            file_path = results_dir / f"{result.strategy_name}_{timestamp}.json"
            result.save_to_file(file_path)
            ErrorHandler.log_info(f"Parsed backtest result saved to {file_path}")
            return file_path
        except Exception as exc:
            ErrorHandler.log_warning(f"Failed to persist parsed result for {result.strategy_name}: {exc}")
            return None

    def _resolve_export_zip(
        self,
        export_filename: Optional[Path],
        previous_exports: Dict[str, Path],
        run_dir: Path,
        strategy_name: str,
    ) -> Optional[Path]:
        """Ensure the export ZIP is located within the run directory archives."""

        if export_filename and export_filename.exists():
            return export_filename

        new_export = self._find_new_export(previous_exports)
        if not new_export or not new_export.exists():
            return export_filename if export_filename and export_filename.exists() else None

        target_path: Optional[Path] = export_filename
        try:
            if target_path is None:
                archives_dir = run_dir / "results" / "archives"
                archives_dir.mkdir(parents=True, exist_ok=True)
                timestamp_token = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_token = uuid4().hex[:8]
                safe_strategy = strategy_name.replace("/", "-").replace("\\", "-")
                target_path = archives_dir / f"{safe_strategy}_{timestamp_token}_{unique_token}.zip"
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(new_export), str(target_path))
            meta_src = new_export.with_suffix(".meta.json")
            if meta_src.exists():
                shutil.move(str(meta_src), str(target_path.with_suffix(".meta.json")))

            try:
                rel_path = target_path.relative_to(run_dir)
                ErrorHandler.log_info(
                    f"Relocated freqtrade export {new_export.name} -> {rel_path}"
                )
            except ValueError:
                ErrorHandler.log_info(
                    f"Relocated freqtrade export {new_export.name} -> {target_path}"
                )

            return target_path
        except Exception as exc:  # noqa: BLE001
            ErrorHandler.log_warning(
                f"Failed to relocate freqtrade export {new_export}: {exc}"
            )
            if target_path and target_path.exists():
                return target_path
            if new_export.exists():
                return new_export
            return None

    def _collect_export_files(self) -> Dict[str, Path]:
        """Return mapping of freqtrade export stems to their paths."""
        export_dir = self.user_data_dir / "backtest_results"
        if not export_dir.exists():
            return {}
        exports: Dict[str, Path] = {}
        for path in export_dir.glob("backtest-result-*.zip"):
            exports[path.stem] = path
        return exports

    def _find_new_export(self, previous_exports: Dict[str, Path]) -> Optional[Path]:
        """Identify the newest export file generated after a backtest run."""
        current_exports = self._collect_export_files()
        if not current_exports:
            return None

        new_candidates = [path for stem, path in current_exports.items() if stem not in previous_exports]
        if new_candidates:
            return max(new_candidates, key=lambda p: p.stat().st_mtime)

        return max(current_exports.values(), key=lambda p: p.stat().st_mtime)

    def _persist_run_archive(
        self,
        export_path: Path,
        run_dir: Path,
        strategy_name: str,
        timestamp_override: Optional[str],
    ) -> Optional[Path]:
        """Copy the exported ZIP into the run directory with strategy-specific naming."""

        if not export_path.exists():
            return None

        archives_dir = run_dir / "results" / "archives"
        archives_dir.mkdir(parents=True, exist_ok=True)

        timestamp = timestamp_override or datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_strategy = strategy_name.replace("/", "-")
        target_zip = archives_dir / f"{safe_strategy}_{timestamp}.zip"

        try:
            shutil.copy(export_path, target_zip)
            meta_src = export_path.with_suffix(".meta.json")
            if meta_src.exists():
                shutil.copy(meta_src, target_zip.with_suffix(".meta.json"))
            ErrorHandler.log_info(
                f"Copied freqtrade export {export_path.name} -> {target_zip.relative_to(run_dir)}"
            )
            return target_zip
        except Exception as exc:  # noqa: BLE001
            ErrorHandler.log_warning(
                f"Failed to persist archive for {strategy_name} from {export_path.name}: {exc}"
            )
            return None

    def _load_result_from_freqtrade_export(
        self,
        export_path: Path,
        strategy_name: str,
        config: BacktestConfig,
        run_dir: Path,
    ) -> Optional[Tuple[BacktestResult, Optional[Path], Optional[str]]]:
        """Unpack freqtrade export and convert it into BacktestResult."""
        try:
            meta_data: Dict[str, Any] = {}
            meta_path = export_path.with_suffix(".meta.json")
            if meta_path.exists():
                try:
                    meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
                except Exception as exc:
                    ErrorHandler.log_warning(f"Failed to read export meta {meta_path.name}: {exc}")

            export_target = run_dir / "results" / "freqtrade_export" / export_path.stem
            if export_target.exists():
                shutil.rmtree(export_target, ignore_errors=True)
            export_target.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(export_path, "r") as archive:
                archive.extractall(export_target)

            if meta_path.exists():
                try:
                    shutil.copy(meta_path, export_target / meta_path.name)
                except Exception as exc:
                    ErrorHandler.log_warning(f"Failed to copy meta file {meta_path.name}: {exc}")

            summary_candidates = [p for p in export_target.glob("*.json") if "backtest-result" in p.stem]
            if not summary_candidates:
                ErrorHandler.log_warning(f"No summary JSON found in freqtrade export {export_path.name}")
                return None

            summary_path = max(summary_candidates, key=lambda p: p.stat().st_mtime)
            summary_data = json.loads(summary_path.read_text(encoding="utf-8"))

            trades_payload: List[Dict[str, Any]] = []
            trades_dir = export_target / "trades"
            if trades_dir.exists():
                trade_files = [p for p in trades_dir.glob("**/*.json") if strategy_name.lower() in p.stem.lower()]
                if trade_files:
                    trade_file = max(trade_files, key=lambda p: p.stat().st_mtime)
                    try:
                        trades_payload_raw = json.loads(trade_file.read_text(encoding="utf-8"))
                        if isinstance(trades_payload_raw, dict):
                            trades_payload = trades_payload_raw.get("trades") or trades_payload_raw.get("data") or []
                        elif isinstance(trades_payload_raw, list):
                            trades_payload = trades_payload_raw
                    except Exception as exc:
                        ErrorHandler.log_warning(f"Failed to read trades file {trade_file.name}: {exc}")

            conversion = self._build_result_from_freqtrade_data(
                summary_data,
                trades_payload,
                strategy_name,
                config,
                meta_data,
            )

            if not conversion:
                return None

            result, timestamp_override = conversion
            try:
                result.source_file = str(summary_path.relative_to(run_dir))
            except ValueError:
                result.source_file = str(summary_path)

            return result, summary_path, timestamp_override
        except Exception as exc:
            ErrorHandler.log_warning(
                f"Failed to unpack freqtrade export {export_path.name} for {strategy_name}: {exc}"
            )
            return None

    def _build_result_from_freqtrade_data(
        self,
        summary_data: Dict[str, Any],
        trades_payload: List[Dict[str, Any]],
        strategy_name: str,
        config: BacktestConfig,
        meta_data: Dict[str, Any],
    ) -> Optional[Tuple[BacktestResult, Optional[str]]]:
        strategies_section = summary_data.get("strategy") or summary_data.get("strategies") or {}
        strategy_block = strategies_section.get(strategy_name)
        if strategy_block is None:
            for key, value in strategies_section.items():
                if isinstance(key, str) and key.lower() == strategy_name.lower():
                    strategy_block = value
                    break

        if strategy_block is None:
            ErrorHandler.log_warning(
                f"Strategy {strategy_name} not found inside freqtrade export summary."
            )
            return None

        def _as_float(payload: Dict[str, Any], key: str) -> float:
            raw = payload.get(key, 0.0)
            try:
                return float(raw)
            except (TypeError, ValueError):
                return 0.0

        def _as_int(payload: Dict[str, Any], key: str) -> int:
            raw = payload.get(key, 0)
            try:
                return int(raw)
            except (TypeError, ValueError):
                return 0

        metrics = PerformanceMetrics()
        metrics.total_return = _as_float(strategy_block, "profit_total")
        metrics.total_return_pct = _as_float(strategy_block, "profit_total_pct")
        metrics.win_rate = _as_float(strategy_block, "winrate")
        metrics.max_drawdown = _as_float(strategy_block, "max_drawdown_account") or _as_float(
            strategy_block, "max_drawdown"
        )
        metrics.max_drawdown_pct = _as_float(strategy_block, "max_relative_drawdown")
        metrics.sharpe_ratio = _as_float(strategy_block, "sharpe")
        metrics.sortino_ratio = _as_float(strategy_block, "sortino")
        metrics.calmar_ratio = _as_float(strategy_block, "calmar")
        metrics.profit_factor = _as_float(strategy_block, "profit_factor")
        metrics.total_trades = _as_int(strategy_block, "trades")
        metrics.winning_trades = _as_int(strategy_block, "wins")
        metrics.losing_trades = _as_int(strategy_block, "losses")
        metrics.avg_profit = _as_float(strategy_block, "profit_mean")
        metrics.avg_profit_pct = _as_float(strategy_block, "profit_mean_pct")
        metrics.avg_duration = _as_float(strategy_block, "avg_duration") or _as_float(
            strategy_block, "duration_avg"
        )
        metrics.calculate_derived_metrics()

        trades = self._parse_trade_records(trades_payload)

        strategy_meta = {}
        if isinstance(meta_data, dict):
            strategy_meta = meta_data.get(strategy_name)
            if strategy_meta is None:
                for key, value in meta_data.items():
                    if isinstance(key, str) and key.lower() == strategy_name.lower():
                        strategy_meta = value
                        break

        result_timestamp = None
        if isinstance(strategy_meta, dict):
            result_timestamp = self._parse_datetime_value(strategy_meta.get("backtest_end_ts"))
            if result_timestamp is None:
                result_timestamp = self._parse_datetime_value(strategy_meta.get("backtest_start_ts"))

        if result_timestamp is None:
            metadata_block = summary_data.get("metadata") or {}
            result_timestamp = self._parse_datetime_value(metadata_block.get("backtest_end_time"))

        if result_timestamp is None:
            result_timestamp = datetime.now()

        result = BacktestResult(
            strategy_name=strategy_name,
            config=config,
            metrics=metrics,
            trades=trades,
            timestamp=result_timestamp,
        )

        timestamp_override = result_timestamp.strftime("%Y%m%d_%H%M%S") if result_timestamp else None

        return result, timestamp_override

    def _parse_trade_records(self, trades_payload: List[Dict[str, Any]]) -> List[TradeRecord]:
        records: List[TradeRecord] = []
        if not isinstance(trades_payload, list):
            return records

        for trade in trades_payload:
            if not isinstance(trade, dict):
                continue

            timestamp = self._parse_datetime_value(
                trade.get("open_date")
                or trade.get("open_time")
                or trade.get("open_timestamp")
                or trade.get("open_date_utc")
            )
            if timestamp is None:
                timestamp = self._parse_datetime_value(trade.get("enter_time"))
            if timestamp is None:
                timestamp = datetime.now()

            side = trade.get("trade_direction") or ("short" if trade.get("isShort") else "long")
            if isinstance(side, str):
                side = side.lower()
            side_value = "sell" if side == "short" else "buy"

            price = trade.get("open_rate") or trade.get("enter_price") or trade.get("open_price") or 0.0
            amount = trade.get("stake_amount") or trade.get("amount") or trade.get("stake") or 0.0
            profit = trade.get("profit_abs") or trade.get("profit_amount") or trade.get("profit")
            profit_pct = trade.get("profit_pct")
            reason = trade.get("exit_reason") or trade.get("sell_reason") or ""

            try:
                price_val = float(price)
            except (TypeError, ValueError):
                price_val = 0.0

            try:
                amount_val = float(amount)
            except (TypeError, ValueError):
                amount_val = 0.0

            try:
                profit_val = float(profit) if profit is not None else None
            except (TypeError, ValueError):
                profit_val = None

            try:
                profit_pct_val = float(profit_pct) if profit_pct is not None else None
            except (TypeError, ValueError):
                profit_pct_val = None

            record = TradeRecord(
                pair=str(trade.get("pair", "")),
                side=side_value,
                timestamp=timestamp,
                price=price_val,
                amount=amount_val,
                profit=profit_val,
                profit_pct=profit_pct_val,
                reason=str(reason),
            )
            records.append(record)

        return records

    def _parse_datetime_value(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value)
            except (ValueError, OSError):
                return None
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            cleaned = cleaned.replace(" ", "T")
            if cleaned.endswith("Z"):
                cleaned = cleaned[:-1] + "+00:00"
            try:
                return datetime.fromisoformat(cleaned)
            except ValueError:
                for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"):
                    try:
                        return datetime.strptime(cleaned, fmt)
                    except ValueError:
                        continue
        return None
    
    def _run_freqtrade_backtest_with_logging(
        self,
        task_id: str,
        strategy_info: "StrategyInfo",
        config_file: Path,
        export_filename: Optional[Path] = None,
    ) -> str:
        """Run freqtrade backtest command with detailed logging"""
        from utils.data_models import StrategyInfo # For type hint
        from .scheduler_singleton import get_log_queue

        strategy_name = strategy_info.name
        strategy_path = strategy_info.file_path.parent
        log_queue = get_log_queue()

        try:
            # Build command
            cmd = [
                sys.executable, "-m", "freqtrade",
                "backtesting",
                "--config", str(config_file),
                "--strategy-path", str(strategy_path),
                "--export", "trades"
            ]

            if export_filename is not None:
                cmd.extend(["--export-filename", export_filename.as_posix()])

            ErrorHandler.log_info(f"Executing freqtrade command: {' '.join(cmd)}")

            # Print detailed command information for real execution
            if self.freqtrade_path != "mock_freqtrade":
                log_queue.put((task_id, f"🔥 REAL FREQTRADE EXECUTION:"))
                log_queue.put((task_id, f"📝 Command: {' '.join(cmd)}"))
                log_queue.put((task_id, f"🎯 Strategy: {strategy_name}"))
                log_queue.put((task_id, f"📂 Strategy Path: {strategy_path}"))
                log_queue.put((task_id, f"⚙️ Config: {config_file}"))
                if export_filename is not None:
                    log_queue.put((task_id, f"📦 Export Target: {export_filename}"))
                log_queue.put((task_id, f"🔧 Freqtrade path: {sys.executable} -m freqtrade"))
                log_queue.put((task_id, "=" * 80))

            # Execute command with real-time logging
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=Path.cwd()
            )

            # Capture output with real-time logging
            stdout_lines = []
            stderr_lines = []

            # Use select to handle real-time output properly
            import select

            # Set up polling for both stdout and stderr
            if hasattr(select, 'select') and sys.platform != 'win32':  # Unix-like systems only
                while True:
                    reads = [process.stdout, process.stderr]
                    readable, _, _ = select.select(reads, [], [], 0.1)

                    for stream in readable:
                        if stream == process.stdout:
                            line = process.stdout.readline()
                            if line:
                                line = line.strip()
                                if line:
                                    log_queue.put((task_id, f"📄 STDOUT: {line}"))
                                stdout_lines.append(line)
                        elif stream == process.stderr:
                            line = process.stderr.readline()
                            if line:
                                line = line.strip()
                                if line:
                                    log_queue.put((task_id, f"⚠️ STDERR: {line}"))
                                stderr_lines.append(line)

                    if process.poll() is not None:
                        break # Exit loop when process finishes
            else:
                # Windows fallback
                log_queue.put((task_id, "🔄 Reading freqtrade output (Windows mode)..."))
                import threading

                def reader_thread(pipe, line_list, prefix):
                    try:
                        for line in iter(pipe.readline, ''):
                            line = line.strip()
                            if line:
                                log_queue.put((task_id, f"{prefix}: {line}"))
                                line_list.append(line)
                    finally:
                        pipe.close()

                stdout_thread = threading.Thread(target=reader_thread, args=[process.stdout, stdout_lines, "📄 STDOUT"], daemon=True)
                stderr_thread = threading.Thread(target=reader_thread, args=[process.stderr, stderr_lines, "⚠️ STDERR"], daemon=True)
                stdout_thread.start()
                stderr_thread.start()
                stdout_thread.join()
                stderr_thread.join()

            process.wait()

            # Check return code
            if process.returncode == 0:
                ErrorHandler.log_info(f"Freqtrade backtest execution successful: {strategy_name}")
                log_queue.put((task_id, "✅ FREQTRADE EXECUTION COMPLETED SUCCESSFULLY"))
                return '\n'.join(stdout_lines)
            else:
                error_msg = f"Freqtrade backtest failed: {strategy_name} - {' '.join(stderr_lines)}"
                ErrorHandler.log_error(error_msg)
                log_queue.put((task_id, f"❌ FREQTRADE EXECUTION FAILED (Return code: {process.returncode})"))
                raise ExecutionError(error_msg)

        except subprocess.TimeoutExpired:
            raise ExecutionError("Backtest execution timeout")

        except Exception as e:
            raise ExecutionError(f"Failed to run freqtrade backtest: {str(e)}")
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            # NOTE: Do not delete temporary configuration files here to allow
            # subsequent subprocess-based validations to reuse the same config.
            # The test harness relies on the config file after execute_backtest().
            # If needed, a separate maintenance job can clean old files.

            # Clean up temporary result files
            for result_file in Path.cwd().glob("backtest_results_*.json"):
                if result_file.exists():
                    result_file.unlink()
            
            ErrorHandler.log_info("Temporary files cleaned up")
        
        except Exception as e:
            ErrorHandler.log_warning(f"Failed to clean up temporary files: {str(e)}")
    
    def execute_dry_run(self, strategy_name: str, config: BacktestConfig) -> bool:
        """
        Execute dry run
        
        Args:
            strategy_name: strategy name
            config: backtest configuration
            
        Returns:
            whether dry run started successfully
        """
        try:
            ErrorHandler.log_info(f"Starting dry run: {strategy_name}")
            
            # Create temporary configuration file
            config_file = self._create_temp_config(strategy_name, config)
            
            # Modify configuration for dry run
            with open(config_file, 'r', encoding='utf-8') as f:
                dry_run_config = json.load(f)
            
            dry_run_config.update({
                "dry_run": True,
                "db_url": f"sqlite:///dryrun_{strategy_name}.sqlite"
            })
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(dry_run_config, f, indent=2, ensure_ascii=False)
            
            # Build dry run command
            cmd = [
                sys.executable, "-m", "freqtrade",
                "trade",
                "--config", str(config_file),
                "--strategy", strategy_name
            ]
            
            # Print detailed command information for real execution
            if self.freqtrade_path != "mock_freqtrade":
                print(f"\n🚀 REAL DRY RUN EXECUTION:")
                print(f"📝 Command: {' '.join(cmd)}")
                print(f"🎯 Strategy: {strategy_name}")
                print(f"📂 Config: {config_file}")
                print(f"🗄️  Database: dryrun_{strategy_name}.sqlite")
                print(f"🔧 Freqtrade path: {self.freqtrade_path}")
                print("=" * 80)
            
            # Start dry run process (non-blocking)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path.cwd()
            )
            
            ErrorHandler.log_info(f"Dry run started: {strategy_name} (PID: {process.pid})")
            return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to start dry run: {strategy_name} - {str(e)}")
            return False
    
    def stop_dry_run(self, strategy_name: str) -> bool:
        """
        Stop dry run
        
        Args:
            strategy_name: strategy name
            
        Returns:
            whether dry run stopped successfully
        """
        try:
            # This is a simplified implementation
            # In a real scenario, you would need to track process IDs
            ErrorHandler.log_info(f"Stopping dry run: {strategy_name}")
            
            # Kill freqtrade processes (simplified approach)
            subprocess.run(["pkill", "-f", f"freqtrade.*{strategy_name}"], 
                         capture_output=True, text=True)
            
            return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to stop dry run: {strategy_name} - {str(e)}")
            return False
    
    def get_execution_status(self, strategy_name: str) -> ExecutionStatus:
        """
        Get execution status
        
        Args:
            strategy_name: strategy name
            
        Returns:
            execution status
        """
        try:
            # Check if freqtrade process is running for this strategy
            result = subprocess.run(
                ["pgrep", "-f", f"freqtrade.*{strategy_name}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return ExecutionStatus.RUNNING
            else:
                return ExecutionStatus.IDLE
        
        except Exception as e:
            ErrorHandler.log_warning(f"Failed to get execution status: {str(e)}")
            return ExecutionStatus.IDLE
    
    def validate_strategy(self, strategy_path: Path) -> bool:
        """
        Validate strategy file
        
        Args:
            strategy_path: strategy file path
            
        Returns:
            whether strategy is valid
        """
        try:
            # Basic validation - check if file exists and has .py extension
            if not strategy_path.exists():
                return False
            
            if strategy_path.suffix != '.py':
                return False
            
            # Try to read the file and check for basic strategy structure
            with open(strategy_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for required strategy components
            required_components = [
                'class',
                'populate_indicators',
                'populate_entry_trend',
                'populate_exit_trend'
            ]
            
            for component in required_components:
                if component not in content:
                    return False
            
            return True
        
        except Exception as e:
            ErrorHandler.log_warning(f"Strategy validation failed: {str(e)}")
            return False