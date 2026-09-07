# Face ID Pipeline

## Project Overview

Face ID Pipeline is a simple CLI project that:

1. Accepts an image path.
2. Detects and encodes one face.
3. Performs a genuine SerpApi Google Lens reverse-image search.
4. Finds matching pages on supported social platforms.
5. Confirms each matched URL is live.
6. Creates SHA256 hashes for the face encoding and verification record.
7. Sends the record hash to Polygon Amoy when a funded test wallet is available.

No website or hosting is required.

## Project Files

- `pipeline.py`: Complete reusable pipeline.
- `requirements.txt`: Python dependencies.
- `.env.example`: Environment-variable template.
- `.gitignore`: Protects secrets and temporary files.
- `README.md`: Setup, run instructions, blockchain details, and limitations.
- `PROJECT_GUIDE.md`: This project and video-submission guide.

## Technologies Used

- **Python**: Main programming language.
- **face_recognition**: Face detection and 128-dimensional encoding.
- **SerpApi Google Lens**: Genuine reverse-image search.
- **requests**: URL confirmation and API requests.
- **hashlib**: SHA256 hashing.
- **web3.py**: Polygon Amoy connection and raw transactions.
- **python-dotenv**: Loads `.env` configuration.
- **Polygon Amoy**: EVM testnet for the blockchain record.

## Setup in VS Code

1. Open `E:\Face_ID_Pipeline` in VS Code.
2. Select **Terminal > New Terminal**.
3. Create the virtual environment:

   ```powershell
   python -m venv .venv
   ```

4. Select the environment:
   - Press `Ctrl+Shift+P`.
   - Select **Python: Select Interpreter**.
   - Choose `.venv\Scripts\python.exe`.

5. Install the dependencies:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m pip install --no-deps face-recognition==1.3.0
   ```

   The final command prevents Windows from trying to compile `dlib` from
   source.

6. Create `.env`:

   ```powershell
   Copy-Item .env.example .env
   ```

7. Edit `.env` and add your real SerpApi key:

   ```env
   SERPAPI_KEY=your_serpapi_key
   ```

   Keep `.env` private. Never show it in a recording.

8. Put an image containing one clear face in the `images` folder.

## Run the Pipeline

Run this command from the VS Code terminal:

```powershell
.\.venv\Scripts\python.exe pipeline.py "images\Billie_Eilish.jpg"
```

Replace the filename for another image.

## What Happens

### 1. Face detection

The script detects exactly one face and creates a 128-value face encoding.

### 2. Reverse-image search

The image is uploaded temporarily to SerpApi. Google Lens searches for genuine
matching pages. The script filters results for Instagram, X/Twitter, Facebook,
and LinkedIn, then displays and confirms every supported match it finds.

No URL is hardcoded or fabricated.

### 3. URL confirmation

The selected URL is fetched with `requests`. The script records its final URL,
HTTP status code, and timestamp.

### 4. Hash creation

The script creates a record containing:

```python
{
    "face_encoding_sha256": "...",
    "matched_url": "...",
    "timestamp": "..."
}
```

The complete record is then hashed with SHA256.

### 5. Blockchain stage

If a real Polygon Amoy private key and test POL are available, `web3.py`
signs and sends a raw transaction containing the record hash.

The final output is:

```text
Polygonscan URL: https://amoy.polygonscan.com/tx/0x...
```

## Dry-Run Mode

If no private key is configured or the wallet has no Amoy test POL, the
pipeline does not fail or invent a transaction. It prints the prepared hash
and reports:

```text
Pipeline completed in dry-run mode.
```

This demonstrates all free stages honestly. It does not claim that a
blockchain transaction was submitted.

## Simple Video Guide

Show these items:

1. The `Face_ID_Pipeline` project folder.
2. `pipeline.py` and its separate stage functions.
3. `requirements.txt`.
4. `.env.example`, with real secrets hidden.
5. An image in the `images` folder.
6. The VS Code terminal command:

   ```powershell
   .\.venv\Scripts\python.exe pipeline.py "images\Billie_Eilish.jpg"
   ```

Explain the terminal output:

- Face detected and encoded.
- Reverse-image match found.
- Post confirmed.
- Record prepared.
- Transaction sent and Polygonscan URL, or dry-run message if test POL is
  unavailable.

## Code Reusability Explanation

Each stage is implemented as one small function with one responsibility:

- `detect_and_encode`
- `find_social_matches`
- `confirm_post`
- `build_hashes`
- `send_transaction`

This avoids duplicated logic and keeps the pipeline short and easy to explain.

## Limitations

- Google Lens may not find private or non-indexed images.
- SerpApi has usage quotas and rate limits.
- Uploaded image IDs expire.
- Face encoding shows visual similarity, not legal identity.
- Exactly one face must be detectable.
- Polygon Amoy test POL is required for a real transaction; dry-run mode is
  available when free test POL cannot be obtained.
