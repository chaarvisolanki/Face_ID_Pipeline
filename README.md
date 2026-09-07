# Face ID Pipeline

A CLI-only hackathon pipeline that detects a face, creates a 128-dimensional
face encoding, performs a genuine SerpApi Google Lens reverse-image search
reverse-image search, confirms the matching social post is live, and anchors a
hash of the verification record on-chain. No website or hosting is required.

## Project files

- `pipeline.py` contains the complete reusable pipeline.
- `requirements.txt` lists the Python packages.
- `.env.example` documents the required environment variables.
- `README.md` explains setup, execution, the blockchain, and limitations.

## Setup

1. Install **64-bit Python 3.11** on Windows. The prebuilt dlib wheel used
   here targets CPython 3.11 on Windows.
2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the dependencies. On Windows, install the prebuilt dlib wheel
   first. This avoids the `Failed to build dlib` error:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   pip install --no-deps face-recognition==1.3.0
   ```

   Do not run `pip install face-recognition` without `--no-deps`: its normal
   dependency resolution tries to compile `dlib` from source. The project
   uses the compatible `dlib-bin` wheel listed in `requirements.txt`.

4. Create a SerpApi account, copy the API key, and copy `.env.example` to
   `.env`.
5. Set `SERPAPI_KEY` and `PRIVATE_KEY` to a wallet key funded with Polygon Amoy
   test MATIC.

## Running in VS Code

1. Open `E:\Face_ID_Pipeline` in VS Code.
2. Choose **Terminal > New Terminal**.
3. Create the virtual environment:

   ```powershell
   python -m venv .venv
   ```

4. Press `Ctrl+Shift+P`, choose **Python: Select Interpreter**, and select
   `.venv\Scripts\python.exe`.
5. Install dependencies:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m pip install --no-deps face-recognition==1.3.0
   ```

   This direct-Python method works even when PowerShell blocks
   `Activate.ps1`.
6. Create `.env` from `.env.example` and add your real `SERPAPI_KEY` and
   Polygon Amoy test-wallet `PRIVATE_KEY`. Never show these secrets.
7. Put an image containing one face in the `images` folder.

## Run

```powershell
.\.venv\Scripts\python.exe pipeline.py "images\face-image.jpg"
```

The script prints each completed stage and ends with a Polygonscan link when
the transaction is accepted.

Example:

```powershell
.\.venv\Scripts\python.exe pipeline.py "images\Billie_Eilish.jpg"
```

If no Polygon Amoy test POL or private key is available, the script completes
in dry-run mode. It prints the prepared SHA256 hash and clearly reports that
no blockchain transaction was submitted. This keeps the demonstration honest:
the hash is never presented as a transaction.

## Pipeline stages

1. Load and validate the input image.
2. Detect exactly one face and create its 128-value encoding.
3. Upload the image to SerpApi's image endpoint and use Google Lens to find
   matching pages on supported social platforms. For Instagram, only a matching
   post (`/p/...`) or profile (`/<account>/`) is accepted. Reels, videos,
   stories, and utility pages are excluded before they are displayed or fetched.
   No result is hardcoded.
4. Fetch each match and record its final URL, HTTP status, and fetch time.
5. Hash the face encoding and the complete verification record with SHA256.
6. Sign and send a raw Polygon Amoy transaction with the record hash in its
   `data` field.
7. Print the transaction hash and Polygonscan URL.

## Submission video guide

Show the project folder, `.env` setup with secrets hidden, and the single
command used to run `pipeline.py`. Explain that the input is one image
containing one face. During the recording, point out the terminal messages for
face encoding, genuine reverse-image matching, post confirmation, and the
transaction. Finish by opening the printed Amoy Polygonscan URL.

The most useful code to show is the `detect_and_encode`,
`find_social_matches`, `confirm_post`, `build_hashes`, and `send_transaction`
functions. Explain that each stage is a small reusable function, and that the
same timestamp, hashing, and error-handling helpers are reused instead of
duplicating logic.

## Blockchain and testnet

The pipeline uses the **Polygon Amoy testnet** (chain ID `80002`). Amoy is
Polygon's current public test network, has low-cost test transactions, and
provides a production-like EVM environment without spending real funds.

## Known Limitations

- Google Lens cannot find images that are not indexed or discoverable,
  so reverse-search accuracy varies for private, new, or uncommon images.
- SerpApi has plan quotas and API rate limits; the uploaded image ID expires
  after a short period.
- Face encoding identifies visual similarity, not legal identity, and the
  pipeline intentionally requires exactly one detectable face.
