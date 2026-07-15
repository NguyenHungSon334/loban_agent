import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getRulers, getRules, putRules } from "../api/client.js";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import RulerStrip from "../components/RulerStrip.jsx";
import styles from "./Rulers.module.css";

const ORDER = ["52.2", "42.9", "38.8"];
const CATS = [
  ["mo", "Mộ"],
  ["cong", "Cổng / rào / cuốn thư"],
  ["loi_di", "Lối đi / bậc tam cấp"],
  ["khoang_cach", "Khoảng cách"],
  ["lang_tho", "Lăng thờ"],
  ["mat_bang", "Mặt bằng khu"],
];

export default function Rulers() {
  const { data, isLoading, error } = useQuery({ queryKey: ["rulers"], queryFn: getRulers });
  const [value, setValue] = useState(63);

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
            <RulerStrip key={key} rulerKey={key} ruler={data.rulers[key]} value={value} />
          ) : null,
        )}

      <RuleEditor />
    </section>
  );
}

function RuleEditor() {
  const { data } = useQuery({ queryKey: ["rules"], queryFn: getRules });
  const [cfg, setCfg] = useState(null);
  const [saved, setSaved] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (data) setCfg(structuredClone(data));
  }, [data]);

  if (!cfg) return null;

  function setCat(cat, ruler) {
    const map = { ...cfg.category_ruler };
    if (ruler === "") delete map[cat];
    else map[cat] = ruler;
    setCfg({ ...cfg, category_ruler: map });
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
      <h3>Cấu hình thước theo hạng mục</h3>
      <p className={styles.note}>
        Gán thước cho từng hạng mục. "Mặc định" = thước {cfg.default_ruler}cm. Riêng
        kích thước đo <strong>thông thủy</strong> (khe đi lọt giữa 2 cột cổng) luôn dùng{" "}
        {cfg.thong_thuy_ruler}cm.
      </p>
      <div className={styles.rows}>
        {CATS.map(([cat, label]) => (
          <label key={cat} className={styles.ruleRow}>
            <span>{label}</span>
            <select
              className={styles.select}
              value={cfg.category_ruler[cat] || ""}
              onChange={(e) => setCat(cat, e.target.value)}
            >
              <option value="">Mặc định ({cfg.default_ruler}cm)</option>
              <option value="38.8">38.8cm (âm phần)</option>
              <option value="42.9">42.9cm (dương trạch)</option>
              <option value="52.2">52.2cm (thông thủy)</option>
            </select>
          </label>
        ))}
      </div>
      <div className={styles.saveRow}>
        <Button onClick={save}>Lưu cấu hình</Button>
        {saved && <span className={styles.ok}>Đã lưu ✓</span>}
        {err && <span className={styles.err}>{err}</span>}
      </div>
    </Card>
  );
}
