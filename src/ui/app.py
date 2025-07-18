from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Tuple
import sys

# Ensure imports work when running this file directly with Streamlit or Python.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
import streamlit as st

from src.core.highlight import cells_to_highlight
from src.core.reconcile import reconcile
from src.io.loader import infer_engine
from src.io.writer import write_coloured
from src.llm import detector
from src.llm.schema import Detection


@st.cache_data
def _detect_cached(file_hash: str, content: bytes, name: str, key: str) -> Detection:
    """Run column detection with caching by file hash."""
    engine = infer_engine(name)
    df = pd.read_excel(BytesIO(content), engine=engine)
    return detector.detect_columns(df, api_key=key)


def _load_file(upload: st.runtime.uploaded_file_manager.UploadedFile) -> Tuple[pd.DataFrame, str, bytes]:
    """Save uploaded file to disk and read it into a DataFrame."""
    data = upload.getvalue()
    suffix = Path(upload.name).suffix
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        path = tmp.name
    engine = infer_engine(upload.name)
    df = pd.read_excel(BytesIO(data), engine=engine)
    return df, path, data


def _run_reconcile(
    left_file: st.runtime.uploaded_file_manager.UploadedFile,
    right_file: st.runtime.uploaded_file_manager.UploadedFile,
    api_key: str,
) -> Tuple[bool, str, str, str]:
    """Process two uploads and perform reconciliation."""
    df_left, path_left, bytes_left = _load_file(left_file)
    df_right, path_right, bytes_right = _load_file(right_file)

    det_left = _detect_cached(hashlib.md5(bytes_left).hexdigest(), bytes_left, left_file.name, api_key)
    det_right = _detect_cached(hashlib.md5(bytes_right).hexdigest(), bytes_right, right_file.name, api_key)

    matches, partials, unmatched = reconcile(df_left, df_right, det_left, det_right)

    left_cells = cells_to_highlight(matches, partials, unmatched, det_left, "left")
    right_cells = cells_to_highlight(matches, partials, unmatched, det_right, "right")

    out_left = write_coloured(df_left, left_cells, path_left)
    out_right = write_coloured(df_right, right_cells, path_right)

    success = not partials and not unmatched and all(m.diff == 0 for m in matches)
    report = f"Matches: {len(matches)}\nPartials: {len(partials)}\nUnmatched: {len(unmatched)}"

    return success, report, out_left, out_right


def main() -> None:
    """Streamlit entrypoint."""
    st.title("Balance Check")

    key = st.sidebar.text_input("OpenAI API Key", type="password")
    if key:
        st.session_state["openai_key"] = key

    left = st.file_uploader("Left workbook", type=["xls", "xlsx"], key="left")
    right = st.file_uploader("Right workbook", type=["xls", "xlsx"], key="right")

    if st.button("Reconcile", disabled=not (left and right)) and left and right:
        with st.spinner("Reconciling..."):
            success, report, out_left, out_right = _run_reconcile(
                left, right, st.session_state.get("openai_key", "")
            )
        if success:
            st.success("All rows matched across workbooks.")
        else:
            st.error(f"Differences found:\n{report}")
        with open(out_left, "rb") as f:
            st.download_button("Download left result", f, file_name=Path(out_left).name)
        with open(out_right, "rb") as f:
            st.download_button("Download right result", f, file_name=Path(out_right).name)
        st.text_area("Report", report, height=120)


if __name__ == "__main__":
    main()
