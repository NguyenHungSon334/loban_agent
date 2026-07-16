import { useEffect, useRef, useState } from "react";
import { sendChat } from "../api/client.js";
import Button from "./Button.jsx";
import styles from "./ChatPanel.module.css";

// Chat tư vấn Lỗ Ban. hoSo tùy chọn -> hỏi trong ngữ cảnh hồ sơ đó.
// autoAsk: câu hỏi tự gửi 1 lần khi mở (câu hỏi kèm lúc submit hồ sơ).
export default function ChatPanel({ hoSo = null, placeholder, autoAsk = null, onReply = null }) {
  const [msgs, setMsgs] = useState([]); // {role:'user'|'bot', text, imgs?:string[]}
  const [text, setText] = useState("");
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [err, setErr] = useState(null);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef(null);

  function addFiles(list) {
    const ok = [...list].filter(
      (f) => f.type.startsWith("image/") || f.type === "application/pdf"
    );
    if (ok.length) setFiles((f) => [...f, ...ok]);
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  }

  async function ask(q, sending) {
    q = q.trim();
    if (!q && !sending.length) return;
    setErr(null);
    setBusy(true);
    const atts = sending.map((f) => ({
      name: f.name,
      isImg: f.type.startsWith("image/"),
      src: URL.createObjectURL(f),
    }));
    setMsgs((m) => [...m, { role: "user", text: q, atts }]);
    try {
      const { reply, updated } = await sendChat(q, sending, hoSo);
      setMsgs((m) => [...m, { role: "bot", text: reply, updated }]);
      // chỉ refetch báo cáo khi chat THỰC SỰ sửa số đo (backend báo updated)
      if (updated) {
        setUpdating(true);
        await onReply?.();          // trang cha refetch -> UI cập nhật
        setUpdating(false);
      }
    } catch (e2) {
      setErr(e2.message);
    } finally {
      setBusy(false);
    }
  }

  function onSend(e) {
    e?.preventDefault();
    const q = text.trim();
    if (!q && !files.length) return;
    const sending = files;
    setText("");
    setFiles([]);
    ask(q, sending);
  }

  // câu hỏi kèm hồ sơ -> tự gửi 1 lần
  const askedAuto = useRef(false);
  useEffect(() => {
    if (autoAsk && !askedAuto.current) {
      askedAuto.current = true;
      ask(autoAsk, []);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoAsk]);

  function onKey(e) {
    if (e.key === "Enter" && !e.shiftKey) onSend(e);
  }

  return (
    <div className={styles.panel}>
      <div
        className={`${styles.log} ${dragging ? styles.dragging : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        {msgs.length === 0 && (
          <p className={styles.hint}>
            {placeholder ||
              'Ví dụ: "Mộ rộng 87 dài 1m27 thuộc cung nào?"'}
            <br />
            <button type="button" className={styles.hintLink} onClick={() => fileRef.current?.click()}>
              Kéo thả hoặc bấm chọn ảnh / PDF bản vẽ
            </button>
          </p>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "user" ? styles.user : styles.bot}>
            {m.atts?.map((a, j) =>
              a.isImg ? (
                <img key={j} src={a.src} alt="" className={styles.thumb} />
              ) : (
                <span key={j} className={styles.chip}>📄 {a.name}</span>
              )
            )}
            {m.text && <div className={styles.bubble}>{m.text}</div>}
            {m.updated && <div className={styles.updated}>✓ Đã cập nhật hồ sơ</div>}
          </div>
        ))}
        {busy && (
          <div className={styles.bot}>
            <div className={`${styles.bubble} ${styles.typing}`} aria-label="Đang xử lý">
              <span /><span /><span />
            </div>
          </div>
        )}
        {updating && (
          <div className={styles.updateBar}>
            <span className={styles.spinner} /> Đang cập nhật báo cáo…
          </div>
        )}
      </div>

      {err && <p className={styles.err}>{err}</p>}

      {files.length > 0 && (
        <div className={styles.attachRow}>
          {files.map((f, i) => (
            <span key={i} className={styles.chip}>
              {f.name}
              <button type="button" onClick={() => setFiles(files.filter((_, k) => k !== i))}>
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <form className={styles.composer} onSubmit={onSend}>
        <button
          type="button"
          className={styles.attach}
          onClick={() => fileRef.current?.click()}
          title="Đính ảnh"
        >
          +
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="image/*,.pdf"
          multiple
          hidden
          onChange={(e) => addFiles(e.target.files)}
        />
        <textarea
          className={styles.input}
          rows={1}
          value={text}
          placeholder="Nhập câu hỏi… (Enter gửi, Shift+Enter xuống dòng)"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKey}
        />
        <Button type="submit" disabled={busy}>
          Gửi
        </Button>
      </form>
    </div>
  );
}
