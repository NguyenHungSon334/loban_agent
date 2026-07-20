import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getRulers, getRules, putRules } from "../api/client.js";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import RulerStrip from "../components/RulerStrip.jsx";
import styles from "./Rulers.module.css";

const ORDER = ["38.8"];   // chỉ dùng thước 38.8
const PX_PER_MM = 6;            // px/mm cho track
const MAX_CYCLE = 388;
const COLORS = { "38.8": "#dc2626" };

export default function Rulers() {
  const { data, isLoading, error } = useQuery({ queryKey: ["rulers"], queryFn: getRulers });
  const [value, setValue] = useState(63);

  const spanMm = Math.max(value + MAX_CYCLE, 2 * MAX_CYCLE);

  return (
    <section className={`container ${styles.page}`}>
      <h2>Tra thước Lỗ Ban</h2>

      <div className={styles.inputRow}>
        <input
          type="number"
          className={styles.mm}
          value={value}
          onChange={(e) => setValue(Number(e.target.value) || 0)}
        />
        <span className={styles.mmLabel}>mm — nhập số cần tra</span>
      </div>
      <p className={styles.hint}>← Kéo/cuộn ngang để xem hết thước →</p>

      {isLoading && <p>Đang tải…</p>}
      {error && <p className={styles.err}>Lỗi tải thước: {error.message}</p>}

      {data &&
        ORDER.map((key) =>
          data.rulers[key] ? (
            <RulerStrip
              key={key}
              rulerKey={key}
              ruler={data.rulers[key]}
              value={value}
              pxPerMm={PX_PER_MM}
              spanMm={spanMm}
              color={COLORS[key] || "#f59e0b"}
            />
          ) : null,
        )}

      <RuleEditor />
    </section>
  );
}

// tên hạng mục -> key ascii (Gemini dùng key): bỏ dấu, thường hóa, non-alnum -> _
function slugify(s) {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[đĐ]/g, "d")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function RuleEditor() {
  const { data } = useQuery({ queryKey: ["rules"], queryFn: getRules });
  const [cfg, setCfg] = useState(null);
  const [saved, setSaved] = useState(false);
  const [err, setErr] = useState(null);
  const [newLabel, setNewLabel] = useState("");

  useEffect(() => {
    if (data) setCfg(structuredClone(data));
  }, [data]);

  if (!cfg) return null;

  const cats = cfg.categories || [];

  function addCat() {
    const label = newLabel.trim();
    if (!label) return;
    const key = slugify(label) || `hm_${Date.now()}`;
    if (cats.some((c) => c.key === key)) {
      setErr(`Hạng mục "${key}" đã tồn tại`);
      return;
    }
    setCfg({ ...cfg, categories: [...cats, { key, label }] });
    setNewLabel("");
    setErr(null);
    setSaved(false);
  }

  function deleteCat(key) {
    const categories = cats.filter((c) => c.key !== key);
    // giữ nguyên checklist trong cfg (cấu hình ở data file), chỉ bỏ nhánh hạng mục đã xóa
    const checklist = { ...(cfg.checklist || {}) };
    delete checklist[key];
    setCfg({ ...cfg, categories, checklist });
    setSaved(false);
  }

  async function save() {
    setErr(null);
    try {
      const res = await putRules(cfg);
      setCfg(res);
      setSaved(true);
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <Card variant="feature" className={styles.editor}>
      <h3>Danh sách hạng mục</h3>
      <p className={styles.note}>
        Thêm hoặc xóa hạng mục. Mọi hạng mục đều tra cung bằng{" "}
        <strong>thước 38,8cm</strong> — không có ngoại lệ.
      </p>
      <div className={styles.rows}>
        {cats.map((c) => (
          <label key={c.key} className={styles.ruleRow}>
            <span>
              {c.label}{" "}
              <button
                type="button"
                className={styles.remove}
                onClick={() => deleteCat(c.key)}
                title="Xóa hạng mục"
              >
                ×
              </button>
            </span>
          </label>
        ))}
      </div>

      <div className={styles.addRow}>
        <input
          className={styles.newCat}
          placeholder="Tên hạng mục mới…"
          value={newLabel}
          onChange={(e) => setNewLabel(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addCat()}
        />
        <Button variant="secondary" onClick={addCat}>+ Thêm hạng mục</Button>
      </div>

      <div className={styles.saveRow}>
        <Button onClick={save}>Lưu cấu hình</Button>
        {saved && <span className={styles.ok}>Đã lưu ✓</span>}
        {err && <span className={styles.err}>{err}</span>}
      </div>
    </Card>
  );
}
