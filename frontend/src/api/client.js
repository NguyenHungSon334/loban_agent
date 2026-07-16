// fetch bọc mỏng — không axios (ponytail). Endpoint plan W2.

async function json(res) {
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export function analyze(formData) {
  return fetch("/api/analyze", { method: "POST", body: formData }).then(json);
}

export function getJob(hoSo) {
  return fetch(`/api/jobs/${encodeURIComponent(hoSo)}`).then(json);
}

export function getReport(hoSo) {
  return fetch(`/api/report/${encodeURIComponent(hoSo)}`).then(json);
}

export function listHoSo(offset = 0, limit = 20) {
  return fetch(`/api/ho-so?offset=${offset}&limit=${limit}`).then(json);
}

export function getRulers() {
  return fetch("/api/rulers").then(json);
}

export function confirmDim(hoSo, index, valueMm = null) {
  return fetch(`/api/report/${encodeURIComponent(hoSo)}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ index, value_mm: valueMm }),
  }).then(json);
}

export function retryJob(hoSo) {
  return fetch(`/api/jobs/${encodeURIComponent(hoSo)}/retry`, {
    method: "POST",
  }).then(json);
}

export function deleteHoSo(hoSo) {
  return fetch(`/api/ho-so/${encodeURIComponent(hoSo)}`, {
    method: "DELETE",
  }).then(json);
}

export function getRules() {
  return fetch("/api/rules").then(json);
}

export function putRules(cfg) {
  return fetch("/api/rules", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cfg),
  }).then(json);
}

// Chat tư vấn Lỗ Ban. hoSo tùy chọn (hỏi trong hồ sơ). files: mảng File media.
export function sendChat(message, files = [], hoSo = null) {
  const fd = new FormData();
  fd.append("message", message);
  if (hoSo) fd.append("ho_so", hoSo);
  for (const f of files) fd.append("files", f);
  return fetch("/api/chat", { method: "POST", body: fd }).then(json);
}

export function fileUrl(hoSo, name) {
  return `/api/files/${encodeURIComponent(hoSo)}/${encodeURIComponent(name)}`;
}

// Lưu blob + cho chọn nơi lưu (Save As). File System Access API nếu có,
// fallback tải thẳng cho trình duyệt cũ.
async function saveBlob(blob, suggestedName) {
  if (window.showSaveFilePicker) {
    try {
      const handle = await window.showSaveFilePicker({ suggestedName });
      const writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
      return;
    } catch (e) {
      if (e.name === "AbortError") return; // người dùng hủy hộp thoại chọn path
      // lỗi khác -> rơi xuống fallback tải thẳng
    }
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = suggestedName;
  a.click();
  URL.revokeObjectURL(url);
}

// Tải 1 file (analysis.json, report.pdf...).
export async function downloadFile(hoSo, name) {
  const res = await fetch(fileUrl(hoSo, name));
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  await saveBlob(await res.blob(), name);
}

// Tải nhiều file cùng loại thành 1 zip (kind: "png" | "all"). Dùng cho PNG
// nhiều trang -> tải full.
export async function downloadBundle(hoSo, kind) {
  const res = await fetch(`/api/bundle/${encodeURIComponent(hoSo)}?kind=${kind}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  await saveBlob(await res.blob(), `${hoSo}_${kind}.zip`);
}
