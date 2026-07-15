import styles from "./RulerStrip.module.css";

// Vẽ 1 thước: cung lớn + cung nhỏ (đỏ=tốt, đen=xấu) + vạch cm + marker tại value.
export default function RulerStrip({ rulerKey, ruler, value }) {
  const cycle = ruler.cycle_mm;
  const pos = ((value % cycle) + cycle) % cycle;
  const markerPct = (pos / cycle) * 100;

  // cung hiện tại + cung nhỏ
  const big = ruler.cung.find((c) => pos >= c.start_mm && pos < c.end_mm) || ruler.cung[0];
  const step = ruler.sub_step_mm || (big.end_mm - big.start_mm) / (big.sub?.length || 1);
  const subIdx = Math.min(
    (big.sub?.length || 1) - 1,
    Math.floor((pos - big.start_mm) / step),
  );
  const subName = big.sub?.[subIdx];

  const cmCount = Math.floor(cycle / 10);
  const ticks = Array.from({ length: cmCount + 1 }, (_, i) => i);

  // track rộng theo tổng số cung nhỏ để chữ đủ chỗ (cuộn ngang như wonder.vn)
  const totalSub = ruler.cung.reduce((n, c) => n + (c.sub?.length || 1), 0);
  const minWidth = Math.max(900, totalSub * 74);

  return (
    <div className={styles.strip}>
      <div className={styles.head}>
        <strong>Thước Lỗ Ban {rulerKey}cm</strong>: {ruler.usage}
      </div>
      <div className={styles.scroll}>
        <div className={styles.track} style={{ minWidth }}>
          <div className={styles.ticks}>
            {ticks.map((i) => (
              <span
                key={i}
                className={styles.tick}
                style={{ left: `${((i * 10) / cycle) * 100}%` }}
              >
                {i} cm
              </span>
            ))}
          </div>
          <div className={styles.cungRow}>
            {ruler.cung.map((c, i) => (
              <div
                key={i}
                className={`${styles.bigCung} ${c.good ? styles.good : styles.bad}`}
              >
                <div className={styles.bigName}>{c.name}</div>
                <div className={styles.subRow}>
                  {(c.sub || []).map((s, j) => (
                    <div key={j} className={styles.subCell}>
                      {s}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className={styles.marker} style={{ left: `${markerPct}%` }} />
        </div>
      </div>
      <div className={styles.result}>
        {value} mm →{" "}
        <span className={big.good ? styles.goodText : styles.badText}>
          {big.name}
          {subName ? ` › ${subName}` : ""} · {big.good ? "Tốt" : "Xấu"}
        </span>
      </div>
    </div>
  );
}
