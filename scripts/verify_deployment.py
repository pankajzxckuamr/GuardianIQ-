#!/usr/bin/env python3
"""
GuardianIQ Deployment Verification & Smoke Testing Tool
Validates that Database, Backend API, and Frontend web services are healthy and functional.
"""

import argparse
import json
import logging
import sys
import time
import urllib.request
import urllib.error

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("GuardianIQ-Deploy-Verify")


def http_get(url: str, timeout: int = 5):
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "GuardianIQ-Deployment-Verifier/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            body = response.read().decode("utf-8")
            return status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return None, str(e)


def verify_backend(api_base_url: str) -> bool:
    logger.info("--------------------------------------------------")
    logger.info(f"Checking Backend API: {api_base_url}")
    logger.info("--------------------------------------------------")

    all_passed = True

    # 1. API Health
    health_url = f"{api_base_url.rstrip('/')}/api/health"
    status, body = http_get(health_url)
    if status == 200:
        logger.info(f" /api/health -> Status 200 OK")
        try:
            data = json.loads(body)
            logger.info(f"   Response: {data.get('message', 'Healthy')}")
        except Exception:
            pass
    else:
        logger.error(f"❌ /api/health failed (Status {status}): {body}")
        all_passed = False

    # 2. Database Health via API
    db_health_url = f"{api_base_url.rstrip('/')}/api/health/db"
    status, body = http_get(db_health_url)
    if status == 200:
        logger.info(f" /api/health/db -> Status 200 OK (Database is alive)")
    else:
        logger.error(f"❌ /api/health/db failed (Status {status}): {body}")
        all_passed = False

    # 3. Version Info
    version_url = f"{api_base_url.rstrip('/')}/api/version"
    status, body = http_get(version_url)
    if status == 200:
        logger.info(f" /api/version -> Status 200 OK")
        try:
            data = json.loads(body)
            v_info = data.get("data", {})
            logger.info(f"   App: {v_info.get('app', 'GuardianIQ')}, Version: {v_info.get('version', 'unknown')}")
        except Exception:
            pass
    else:
        logger.warning(f"⚠️ /api/version returned status {status}")

    return all_passed


def verify_frontend(frontend_url: str) -> bool:
    logger.info("--------------------------------------------------")
    logger.info(f"Checking Frontend: {frontend_url}")
    logger.info("--------------------------------------------------")

    status, body = http_get(frontend_url)
    if status == 200:
        if "<title>" in body or "GuardianIQ" in body or "root" in body:
            logger.info(f" Frontend Root -> Status 200 OK (HTML bundle served)")
            return True
        else:
            logger.warning(f"⚠️ Frontend returned 200 but content did not match expected HTML bundle structure.")
            return True
    else:
        logger.error(f"❌ Frontend check failed (Status {status}): {body}")
        return False


def main():
    parser = argparse.ArgumentParser(description="GuardianIQ Deployment Verification Tool")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Backend API base URL (default: http://localhost:8000)")
    parser.add_argument("--frontend-url", default="http://localhost:5173", help="Frontend URL (default: http://localhost:5173)")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend validation")
    parser.add_argument("--skip-backend", action="store_true", help="Skip backend validation")
    args = parser.parse_args()

    logger.info("==================================================")
    logger.info("    GuardianIQ Deployment Verification Smoke Test  ")
    logger.info("==================================================")

    backend_ok = True
    frontend_ok = True

    if not args.skip_backend:
        backend_ok = verify_backend(args.api_url)

    if not args.skip_frontend:
        frontend_ok = verify_frontend(args.frontend_url)

    logger.info("==================================================")
    if backend_ok and frontend_ok:
        logger.info("🎉 All deployment verification checks PASSED!")
        sys.exit(0)
    else:
        logger.error("❌ Some deployment verification checks FAILED. Please review the log above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
