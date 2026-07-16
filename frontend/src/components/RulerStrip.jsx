import { useEffect, useRef } from "react";
import styles from "./RulerStrip.module.css";

// 1 thước ĐỘC LẬP: track lặp theo chu kỳ riêng, marker tại value*px (đúng vị trí số).
// Tự cuộn để đưa marker vào giữa khi đổi số. Mỗi thước 1 màu chỉ báo riêng.
export default function RulerStrip({ rulerKey, ruler, value, pxPerMm, spanMm, color }) {
  const cycle = ruler.cycle_mm;
  const repeats = Math.ceil(spanMm / cycle);
  const trackW = repeats * cycle * pxPerMm;
  const markerX = value * pxPerMm;
  const scrollRef = useRef(null);

  // Đổi số -> tự trượt đưa marker của THƯỚC NÀY vào giữa khung.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ left: Math.max(0, markerX - el.clientWidth / 2), behavior: "smooth" });
  }, [markerX]);

  // cung/cung nhỏ hiện tại (theo vị trí trong 1 chu kỳ)
  const pos = ((value % cycle) + cycle) % cycle;
  const big = ruler.cung.find((c) => pos >= c.start_mm && pos < c.end_mm) || ruler.cung[0];
  const step = ruler.sub_step_mm || (big.end_mm - big.start_mm) / (big.sub?.length || 1);
  const subIdx = Math.min((big.sub?.length || 1) - 1, Math.floor((pos - big.start_mm) / step));
  const subName = big.sub?.[subIdx];

  const cmCount = Math.floor(spanMm / 10);
  const ticks = Array.from({ length: cmCount + 1 }, (_, i) => i);
  const cells = Array.from({ length: repeats }, (_, r) => r);

  return (
    <div className={styles.strip}>
      <div className={styles.head}>
        <strong>Thước Lỗ Ban {rulerKey}cm</strong>: {ruler.usage}
      </div>
      <div className={styles.scroll} ref={scrollRef}>
        <div className={styles.track} style={{ width: trackW }}>
          <div className={styles.ticks}>
            {ticks.map((i) => (
              <span key={i} className={styles.tick} style={{ left: i * 10 * pxPerMm }}>
                {i} cm
              </span>
            ))}
          </div>
          <div className={styles.cungRow} style={{ width: trackW }}>
            {cells.map((r) =>
              ruler.cung.map((c, i) => (
                <div
                  key={`${r}-${i}`}
                  className={`${styles.bigCung} ${c.good ? styles.good : styles.bad}`}
                >
                  <div className={styles.bigName}>{c.name}</div>
                  <div className={styles.subRow}>
                    {(c.sub || []).map((s, j) => (
                      <div key={j} className={styles.subCell}>{s}</div>
                    ))}
                  </div>
                </div>
              )),
            )}
          </div>
          <div
            className={styles.marker}
            style={{
              left: markerX,
              position: "absolute",
              top: 0,
              bottom: 0,
              width: 3,
              background: color,
              zIndex: 5,
              pointerEvents: "none",
            }}
          >
            <span className={styles.markerTag} style={{ background: color }}>
              {value}mm
            </span>
          </div>
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
