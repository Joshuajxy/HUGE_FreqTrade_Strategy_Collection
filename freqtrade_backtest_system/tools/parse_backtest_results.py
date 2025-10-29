"""Utility script to parse Freqtrade backtest exports or run directories.

This script is intended to be executed manually inside the project's virtual
environment.  It reads one of the following sources:

1. A Freqtrade `backtest-result-*.zip` export file
2. A directory produced by this application (e.g. `run_<timestamp>`)

For each strategy found, the script extracts performance metrics and (optionally)
trade records, then writes a consolidated JSON report for verification.

Usage examples
--------------

Parse a Freqtrade export zip and write summary next to the archive::

    python tools/parse_backtest_results.py --source user_data/backtest_results/backtest-result-2025-10-28_23-13-32.zip

Parse a specific run directory, include full trade logs, and send the output to
`report.json`::

    python tools/parse_backtest_results.py \
        --source user_data/backtest_results/run_20251028_231318 \
        --output report.json \
        --include-trades

Optional arguments allow filtering by strategy name and limiting the number of
trades retained per strategy.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

SOURCE_TYPES = {"freqtrade_export", "run_directory"}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse Freqtrade export archives or run directories and dump metrics to JSON."
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Path to a backtest export zip, an extracted export directory, or a run_<timestamp> directory.",
    )
    parser.add_argument(
        "--output",
        help="Destination JSON file. Defaults to <source>_parsed.json or, for directories, <basename>_parsed.json.",
    )
    parser.add_argument(
        "--strategies",
        nargs="*",
        help="Optional list of strategy names to include. Case-insensitive; defaults to all strategies present.",
    )
    parser.add_argument(
        "--include-trades",
        action="store_true",
        help="Include (normalized) trade records in the output. By default only trade counts are reported.",
    )
    parser.add_argument(
        "--limit-trades",
        type=int,
        default=None,
        help="If provided, truncate the trades list (per strategy) to this many entries. Ignored unless --include-trades is set.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    source_path = Path(args.source).expanduser().resolve()

    if not source_path.exists():
        print(f"❌ Source not found: {source_path}", file=sys.stderr)
        return 1

    strategy_filter = {name.lower() for name in args.strategies} if args.strategies else None

    try:
        if source_path.is_file():
            parsed_results = [parse_export_zip(source_path, strategy_filter, args.include_trades, args.limit_trades)]
        else:
            parsed_results = parse_directory_source(
                source_path, strategy_filter, args.include_trades, args.limit_trades
            )
    except Exception as exc:  # pylint: disable=broad-except
        print(f"❌ Failed to parse source: {exc}", file=sys.stderr)
        return 1

    if not parsed_results:
        print("⚠️ No backtest results were parsed from the provided source.", file=sys.stderr)
        return 2

    timestamp = datetime.now().isoformat()
    report = {
        "generated_at": timestamp,
        "source": str(source_path),
        "result_sets": parsed_results,
    }

    output_path = determine_output_path(source_path, args.output)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"✅ Parsed {len(parsed_results)} result set(s). Summary written to: {output_path}")
    return 0


def determine_output_path(source_path: Path, explicit_output: Optional[str]) -> Path:
    if explicit_output:
        return Path(explicit_output).expanduser().resolve()

    if source_path.is_file():
        default_name = f"{source_path.stem}_parsed.json"
        return source_path.with_name(default_name)

    default_name = f"{source_path.name}_parsed.json"
    return source_path / default_name


# ---------------------------------------------------------------------------
# Directory parsing
# ---------------------------------------------------------------------------

def parse_directory_source(
    directory: Path,
    strategy_filter: Optional[Iterable[str]],
    include_trades: bool,
    limit_trades: Optional[int],
) -> List[Dict[str, Any]]:
    """Parse a directory that may contain run outputs or exported archives."""
    results: List[Dict[str, Any]] = []

    run_dir = locate_run_directory(directory)
    if run_dir is not None:
        results.append(
            parse_run_directory(run_dir, strategy_filter, include_trades, limit_trades)
        )

    export_archives = sorted(p for p in directory.glob("backtest-result-*.zip")) if directory.is_dir() else []
    for archive in export_archives:
        results.append(parse_export_zip(archive, strategy_filter, include_trades, limit_trades))

    # As a fallback, treat the directory itself as an extracted export if summary JSON exists.
    summary_candidates = list(directory.glob("backtest-result-*.json"))
    if summary_candidates:
        results.append(
            parse_extracted_export(directory, summary_candidates, strategy_filter, include_trades, limit_trades)
        )

    # Filter out empty result sets
    results = [result for result in results if result.get("strategies")]
    return results


def locate_run_directory(directory: Path) -> Optional[Path]:
    """Return the directory representing a run (contains run_metadata.json), if any."""
    if directory.is_dir():
        metadata_path = directory / "run_metadata.json"
        if metadata_path.exists():
            return directory

    parent_candidate = directory.parent
    if parent_candidate and parent_candidate.is_dir():
        metadata_path = parent_candidate / "run_metadata.json"
        if metadata_path.exists() and directory.name == "results":
            return parent_candidate

    return None


def parse_run_directory(
    run_dir: Path,
    strategy_filter: Optional[Iterable[str]],
    include_trades: bool,
    limit_trades: Optional[int],
) -> Dict[str, Any]:
    metadata = read_json_if_exists(run_dir / "run_metadata.json")
    strategies: Dict[str, Any] = {}

    results_dir = run_dir / "results"
    result_files = sorted(
        p
        for p in results_dir.glob("*.json")
        if p.name != "run_metadata.json" and not p.name.endswith(".meta.json")
    ) if results_dir.exists() else []

    filter_set = {name.lower() for name in strategy_filter} if strategy_filter else None

    for file_path in result_files:
        if "freqtrade_export" in file_path.parts:
            continue
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"⚠️ Skipping unreadable result file {file_path.name}: {exc}", file=sys.stderr)
            continue

        strategy_name = payload.get("strategy_name") or file_path.stem.split("_")[0]
        if filter_set and strategy_name.lower() not in filter_set:
            continue

        trades: List[Dict[str, Any]] = payload.get("trades", []) or []
        strategy_entry: Dict[str, Any] = {
            "metrics": payload.get("metrics", {}),
            "trade_count": len(trades),
            "timestamp": payload.get("timestamp"),
            "execution_time": payload.get("execution_time"),
            "status": payload.get("status"),
            "source_file": str(file_path.relative_to(run_dir)) if file_path.is_relative_to(run_dir) else str(file_path),
        }

        attach_trades(strategy_entry, trades, include_trades, limit_trades)
        strategies[strategy_name] = strategy_entry

    return {
        "type": "run_directory",
        "source": str(run_dir),
        "metadata": metadata,
        "strategies": strategies,
    }


# ---------------------------------------------------------------------------
# Export parsing
# ---------------------------------------------------------------------------

def parse_export_zip(
    archive_path: Path,
    strategy_filter: Optional[Iterable[str]],
    include_trades: bool,
    limit_trades: Optional[int],
) -> Dict[str, Any]:
    with zipfile.ZipFile(archive_path, "r") as archive:
        summary_name = find_summary_member(archive)
        if summary_name is None:
            raise ValueError(f"No backtest-result summary JSON found in archive {archive_path.name}")

        summary_data = json.loads(archive.read(summary_name).decode("utf-8"))
        strategies = parse_summary_payload(
            summary_data,
            archive,
            strategy_filter,
            include_trades,
            limit_trades,
        )

    metadata = read_json_if_exists(archive_path.with_suffix(".meta.json"))

    return {
        "type": "freqtrade_export",
        "source": str(archive_path),
        "metadata": metadata,
        "strategies": strategies,
    }


def parse_extracted_export(
    directory: Path,
    summary_files: List[Path],
    strategy_filter: Optional[Iterable[str]],
    include_trades: bool,
    limit_trades: Optional[int],
) -> Dict[str, Any]:
    summary_files = sorted(summary_files, key=lambda p: p.stat().st_mtime, reverse=True)
    summary_path = summary_files[0]
    summary_data = json.loads(summary_path.read_text(encoding="utf-8"))

    trades_dir = directory / "trades"
    trade_files = list(trades_dir.glob("**/*.json")) if trades_dir.exists() else []
    trades_lookup = {file_path: json.loads(file_path.read_text(encoding="utf-8")) for file_path in trade_files}

    strategies = parse_summary_payload(
        summary_data,
        trades_lookup,
        strategy_filter,
        include_trades,
        limit_trades,
    )

    metadata = read_json_if_exists(summary_path.with_suffix(".meta.json")) or read_json_if_exists(
        directory / f"{summary_path.stem}.meta.json"
    )

    return {
        "type": "freqtrade_export",
        "source": str(directory),
        "metadata": metadata,
        "strategies": strategies,
    }


def find_summary_member(archive: zipfile.ZipFile) -> Optional[str]:
    for member in archive.namelist():
        name = Path(member)
        if name.suffix == ".json" and "backtest-result" in name.stem and "/" not in member.strip("/").split("/")[-1]:
            return member
    return None


def parse_summary_payload(
    summary_data: Dict[str, Any],
    trade_source: Any,
    strategy_filter: Optional[Iterable[str]],
    include_trades: bool,
    limit_trades: Optional[int],
) -> Dict[str, Any]:
    strategies_section = summary_data.get("strategy") or summary_data.get("strategies") or {}
    if not isinstance(strategies_section, dict):
        raise ValueError("Unexpected summary JSON format: missing 'strategy' section")

    filter_set = {name.lower() for name in strategy_filter} if strategy_filter else None
    results: Dict[str, Any] = {}

    for strategy_name, payload in strategies_section.items():
        if filter_set and strategy_name.lower() not in filter_set:
            continue

        metrics = extract_metrics(payload)
        trades = gather_trades(trade_source, strategy_name)
        strategy_entry: Dict[str, Any] = {
            "metrics": metrics,
            "trade_count": len(trades),
            "timestamp": infer_result_timestamp(summary_data, payload),
            "raw_summary": payload,
        }

        attach_trades(strategy_entry, trades, include_trades, limit_trades)
        results[strategy_name] = strategy_entry

    return results


def extract_metrics(strategy_block: Dict[str, Any]) -> Dict[str, Any]:
    def as_float(keys: Iterable[str], default: float = 0.0) -> float:
        for key in keys:
            if key in strategy_block and strategy_block[key] not in (None, ""):
                try:
                    value = strategy_block[key]
                    if isinstance(value, str):
                        value = value.replace("%", "").replace(",", "")
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return default

    def as_int(keys: Iterable[str], default: int = 0) -> int:
        for key in keys:
            if key in strategy_block and strategy_block[key] not in (None, ""):
                try:
                    return int(strategy_block[key])
                except (ValueError, TypeError):
                    try:
                        return int(float(strategy_block[key]))
                    except (ValueError, TypeError):
                        continue
        return default

    metrics = {
        "total_return": as_float(["profit_total", "profit_total_abs", "profit_abs"]),
        "total_return_pct": as_float(["profit_total_pct", "profit_pct", "total_profit_pct"]),
        "win_rate": as_float(["winrate", "win_rate", "winning_pct"]),
        "max_drawdown": as_float(["max_drawdown_account", "max_drawdown"]),
        "max_drawdown_pct": as_float(["max_relative_drawdown", "max_drawdown_pct"]),
        "sharpe_ratio": as_float(["sharpe", "sharpe_ratio"]),
        "sortino_ratio": as_float(["sortino", "sortino_ratio"]),
        "calmar_ratio": as_float(["calmar", "calmar_ratio"]),
        "profit_factor": as_float(["profit_factor"]),
        "total_trades": as_int(["trades", "total_trades"]),
        "winning_trades": as_int(["wins", "winning_trades"]),
        "losing_trades": as_int(["losses", "losing_trades"]),
        "avg_profit": as_float(["profit_mean", "avg_profit"]),
        "avg_profit_pct": as_float(["profit_mean_pct", "avg_profit_pct"]),
        "avg_duration": as_float(["avg_duration", "duration_avg", "avg_trade_duration"]),
    }

    if metrics["win_rate"] == 0.0 and metrics["total_trades"] > 0:
        metrics["win_rate"] = round(
            100.0 * metrics["winning_trades"] / metrics["total_trades"],
            4,
        )

    if metrics["calmar_ratio"] == 0.0 and metrics["max_drawdown"]:
        calmar = metrics["total_return"] / abs(metrics["max_drawdown"])
        metrics["calmar_ratio"] = round(calmar, 6)

    return metrics


def gather_trades(trade_source: Any, strategy_name: str) -> List[Dict[str, Any]]:
    """Collect trade records for a strategy from a ZipFile or extracted files."""
    if isinstance(trade_source, zipfile.ZipFile):
        return gather_trades_from_archive(trade_source, strategy_name)
    if isinstance(trade_source, dict):  # extracted files mapping
        return gather_trades_from_mapping(trade_source, strategy_name)
    return []


def gather_trades_from_archive(archive: zipfile.ZipFile, strategy_name: str) -> List[Dict[str, Any]]:
    matched: List[Dict[str, Any]] = []
    target = strategy_name.lower()

    for member in archive.namelist():
        path = Path(member)
        if path.suffix != ".json":
            continue
        if "backtest-result" in path.stem:
            continue
        if target not in path.stem.lower():
            continue

        try:
            data = json.loads(archive.read(member).decode("utf-8"))
        except json.JSONDecodeError:
            continue
        matched.extend(extract_trades_from_payload(data))

    return matched


def gather_trades_from_mapping(
    trades_lookup: Dict[Path, Any], strategy_name: str
) -> List[Dict[str, Any]]:
    matched: List[Dict[str, Any]] = []
    target = strategy_name.lower()

    for path, payload in trades_lookup.items():
        if path.suffix != ".json":
            continue
        if target not in path.stem.lower():
            continue
        matched.extend(extract_trades_from_payload(payload))

    return matched


def extract_trades_from_payload(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("trades", "data", "results"):
            if isinstance(payload.get(key), list):
                return normalize_trades(payload[key])
        return []
    if isinstance(payload, list):
        return normalize_trades(payload)
    return []


def normalize_trades(trades: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for trade in trades:
        if not isinstance(trade, dict):
            continue
        normalized.append(
            {
                "pair": trade.get("pair"),
                "open_time": trade.get("open_date") or trade.get("enter_time") or trade.get("open_timestamp"),
                "close_time": trade.get("close_date") or trade.get("exit_time") or trade.get("close_timestamp"),
                "trade_direction": trade.get("trade_direction"),
                "stake_amount": trade.get("stake_amount") or trade.get("amount") or trade.get("stake"),
                "profit_abs": trade.get("profit_abs") or trade.get("profit_amount") or trade.get("profit"),
                "profit_pct": trade.get("profit_pct"),
                "exit_reason": trade.get("exit_reason") or trade.get("sell_reason"),
            }
        )
    return normalized


def attach_trades(
    strategy_entry: Dict[str, Any],
    trades: List[Dict[str, Any]],
    include_trades: bool,
    limit_trades: Optional[int],
) -> None:
    if not trades:
        return

    if include_trades:
        strategy_entry["trades"] = trades[:limit_trades] if limit_trades else trades
    elif limit_trades:
        strategy_entry["trades_preview"] = trades[:limit_trades]


def infer_result_timestamp(summary_data: Dict[str, Any], strategy_payload: Dict[str, Any]) -> Optional[str]:
    # Strategy-specific metadata might include start/end timestamps
    for key in ("backtest_end_ts", "backtest_end_time", "end_at"):
        if key in strategy_payload:
            ts = parse_timestamp(strategy_payload[key])
            if ts:
                return ts

    metadata = summary_data.get("metadata") or {}
    for key in ("backtest_end_time", "backtest_end_ts", "backtest_start_time"):
        if key in metadata:
            ts = parse_timestamp(metadata[key])
            if ts:
                return ts

    return None


def parse_timestamp(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value)).isoformat()
        except (ValueError, OSError):
            return None
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        candidate = candidate.replace(" ", "T")
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(candidate, fmt).isoformat()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(candidate).isoformat()
        except ValueError:
            return None
    if isinstance(value, datetime):
        return value.isoformat()
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_json_if_exists(path: Path) -> Optional[Dict[str, Any]]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


if __name__ == "__main__":
    raise SystemExit(main())
