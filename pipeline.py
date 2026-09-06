"""Face ID Pipeline: CLI face, reverse-image, and blockchain verification."""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SOCIAL_DOMAINS = (
    "instagram.com",
    "x.com",
    "twitter.com",
    "facebook.com",
    "linkedin.com",
)
DEFAULT_AMOY_RPC_URL = "https://rpc-amoy.polygon.technology"
AMOY_CHAIN_ID = 80002

logging.basicConfig(level=logging.INFO, format="%(message)s")
LOGGER = logging.getLogger(__name__)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def detect_and_encode(image_path: Path) -> list[float]:
    try:
        import face_recognition

        image = face_recognition.load_image_file(image_path)
        locations = face_recognition.face_locations(image)
        if not locations:
            raise ValueError("No face was detected in the image.")
        if len(locations) > 1:
            raise ValueError(
                f"Expected one face, but detected {len(locations)} faces."
            )
        encodings = face_recognition.face_encodings(image, known_face_locations=locations)
        if not encodings:
            raise ValueError("A face was detected, but it could not be encoded.")
        encoding = encodings[0]
        if len(encoding) != 128:
            raise ValueError(f"Expected a 128-d encoding, received {len(encoding)} values.")
        LOGGER.info("Face detected and encoded (128 dimensions).")
        return encoding.tolist()
    except Exception as exc:
        raise RuntimeError(f"Face detection failed: {exc}") from exc


def find_social_match(image_path: Path) -> str:
    try:
        import requests

        api_key = os.getenv("SERPAPI_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "SERPAPI_KEY is missing. Add your SerpApi key to .env."
            )
        with image_path.open("rb") as image_file:
            upload = requests.post(
                "https://serpapi.com/image",
                data={"api_key": api_key},
                files={"image": (image_path.name, image_file, "application/octet-stream")},
                timeout=30,
            )
        if not upload.ok:
            detail = upload.text[:300].replace("\n", " ")
            raise RuntimeError(
                f"SerpApi image upload returned HTTP {upload.status_code}: {detail}"
            )
        image_id = upload.json().get("image_id")
        if not image_id:
            raise RuntimeError("SerpApi did not return an image_id.")
        response = requests.get(
            "https://serpapi.com/search.json",
            params={
                "api_key": api_key,
                "engine": "google_lens",
                "image_id": image_id,
                "type": "all",
                "hl": "en",
            },
            timeout=45,
        )
        response.raise_for_status()
        results = response.json()
        if results.get("error"):
            raise RuntimeError(results["error"])
        candidates = results.get("exact_matches", []) + results.get("visual_matches", [])
        for match in candidates:
            url = match.get("link", "")
            if any(domain in url.lower() for domain in SOCIAL_DOMAINS):
                LOGGER.info("Reverse-image match found: %s", url)
                return url
        LOGGER.info(
            "No matching Instagram, X/Twitter, Facebook, or LinkedIn page was found. "
            "Exiting without fabricating a result."
        )
        raise LookupError("No supported social-media match found.")
    except LookupError:
        raise
    except Exception as exc:
        raise RuntimeError(f"SerpApi Google Lens reverse-image search failed: {exc}") from exc


def confirm_post(url: str) -> dict[str, str | int]:
    try:
        import requests

        fetched_at = utc_timestamp()
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "Face-ID-Pipeline/1.0"},
            allow_redirects=True,
        )
        result: dict[str, str | int] = {
            "url": response.url,
            "status_code": response.status_code,
            "fetched_at": fetched_at,
        }
        LOGGER.info(
            "Post confirmed: HTTP %s at %s",
            response.status_code,
            fetched_at,
        )
        return result
    except Exception as exc:
        raise RuntimeError(f"Matched URL could not be fetched: {exc}") from exc


def build_hashes(encoding: list[float], matched_url: str) -> tuple[dict[str, str], str]:
    encoding_bytes = ",".join(f"{value:.17g}" for value in encoding).encode("ascii")
    face_hash = hashlib.sha256(encoding_bytes).hexdigest()
    record = {
        "face_encoding_sha256": face_hash,
        "matched_url": matched_url,
        "timestamp": utc_timestamp(),
    }
    record_hash = hashlib.sha256(
        "|".join(f"{key}={record[key]}" for key in sorted(record)).encode("utf-8")
    ).hexdigest()
    return record, record_hash


def send_transaction(record_hash: str) -> str:
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        raise RuntimeError("PRIVATE_KEY is missing from the environment.")
    rpc_url = os.getenv("POLYGON_AMOY_RPC_URL", DEFAULT_AMOY_RPC_URL)
    try:
        from web3 import Web3

        web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
        if not web3.is_connected():
            raise RuntimeError(f"Could not connect to Polygon Amoy RPC: {rpc_url}")
        account = web3.eth.account.from_key(private_key)
        nonce = web3.eth.get_transaction_count(account.address, "pending")
        gas_price = web3.eth.gas_price
        transaction: dict[str, Any] = {
            "chainId": AMOY_CHAIN_ID,
            "nonce": nonce,
            "to": account.address,
            "value": 0,
            "gas": 100_000,
            "gasPrice": gas_price,
            "data": Web3.to_bytes(text=record_hash),
        }
        signed = account.sign_transaction(transaction)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hex = tx_hash.hex()
        LOGGER.info("Transaction sent: %s", tx_hex)
        return tx_hex
    except Exception as exc:
        raise RuntimeError(f"Polygon Amoy transaction failed: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image_path", type=Path, help="Path to an image containing one face")
    return parser.parse_args()


def validate_serpapi_key() -> None:
    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key or api_key == "replace_with_your_serpapi_key":
        raise RuntimeError(
            "SERPAPI_KEY is missing. Create a SerpApi account, copy your API key, "
            "and add SERPAPI_KEY=... to .env."
        )


def main() -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv()
        args = parse_args()
        if not args.image_path.is_file():
            LOGGER.error("Input image does not exist: %s", args.image_path)
            return 1
        validate_serpapi_key()

        encoding = detect_and_encode(args.image_path)
        matched_url = find_social_match(args.image_path)
        post = confirm_post(matched_url)
        record, record_hash = build_hashes(encoding, str(post["url"]))
        LOGGER.info("Record prepared: %s", record)
        tx_hash = send_transaction(record_hash)
        LOGGER.info("Polygonscan URL: https://amoy.polygonscan.com/tx/%s", tx_hash)
        return 0
    except LookupError:
        return 0
    except Exception as exc:
        LOGGER.error("Pipeline stopped gracefully: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
