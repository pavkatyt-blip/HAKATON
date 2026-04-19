import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import io
import json
import logging
import shutil
import traceback
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

from pipeline import process_audio

# ----------------------------------
# LOGGING
# ----------------------------------

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

# ---------------------------------
# APP
# ---------------------------------

app = FastAPI(title="Audio Anonymizer API")

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_INPUT_DIR = BASE_DIR / "tmp" / "input"
TMP_OUTPUT_DIR = BASE_DIR / "tmp" / "output"

TMP_INPUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def add_log(logs: list[dict], level: str, stage: str, message: str):
    logs.append(
        {
            "time": utc_now_iso(),
            "level": level,
            "stage": stage,
            "message": message,
        }
    )


@app.get("/health")
def health():
    logger.info("Health check")
    return {"status": "ok"}


@app.post("/anonymize")
async def anonymize_audio(
    file: UploadFile = File(...),
):
    logs: list[dict] = []
    request_id = str(uuid.uuid4())
    language = "ru"
    
    add_log(logs, "info", "request", "request received")
    logger.info(f"[{request_id}] Request received")

    if not file.filename:
        add_log(logs, "error", "request", "filename missing")
        logger.warning(f"[{request_id}] Empty filename")
        raise HTTPException(status_code=400, detail="Filename missing")

    ext = Path(file.filename).suffix.lower()
    if not ext:
        ext = ".bin"

    input_filename = f"{request_id}_{uuid.uuid4().hex}{ext}"
    input_path = TMP_INPUT_DIR / input_filename

    try:
        # save input
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = input_path.stat().st_size
        logger.info(f"[{request_id}] File saved: {file.filename} ({round(file_size / 1024, 2)} KB)")
        add_log(logs, "info", "upload", "input file saved")

        # processing
        logger.info(f"[{request_id}] Start processing")
        add_log(logs, "info", "pipeline", "processing started")

        result = process_audio(
            str(input_path),
            request_id=request_id,
            language_hint=language,
        )

        logger.info(f"[{request_id}] Pipeline finished")
        add_log(logs, "info", "stt", "transcription completed")
        add_log(logs, "info", "redaction", f"detected {len(result['pii_spans'])} pii spans")

        output_path = Path(result["output_path"])
        if not output_path.exists():
            logger.error(f"[{request_id}] Output file not found")
            add_log(logs, "error", "redaction", "redacted audio file was not created")
            raise HTTPException(status_code=500, detail="Redacted file not created")

        result_payload = {
            "request_id": result["request_id"],
            "transcript": result["transcript"],
            "redacted_text": result["redacted_text"],
            "pii_spans": result["pii_spans"],
            "logs": logs,
        }

        logger.info(f"[{request_id}] Building ZIP")
        add_log(logs, "info", "response", "building zip response")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(output_path, arcname="redacted.wav")
            zf.writestr(
                "result.json",
                json.dumps(result_payload, ensure_ascii=False, indent=2).encode("utf-8"),
            )

        zip_buffer.seek(0)

        logger.info(f"[{request_id}] Response sent")
        add_log(logs, "info", "response", "response prepared")

        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{request_id}_result.zip"'
            },
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[{request_id}] ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        add_log(logs, "error", "pipeline", f"internal error: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}",
        )

    finally:
        try:
            file.file.close()
        except Exception:
            pass
