"""Deployment entry point: validate local prerequisites before importing runtime."""

from core.startup_preflight import run_preflight


def main() -> int:
    report = run_preflight()
    if not report.ok:
        print(report.safe_summary())
        return 1
    from AdelSmartBot import run_application
    return run_application(preflight_report=report)


if __name__ == "__main__":
    raise SystemExit(main())
