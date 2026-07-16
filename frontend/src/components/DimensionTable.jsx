import { useState } from "react";
import CungBadge from "./CungBadge.jsx";
import styles from "./DimensionTable.module.css";

function mm(v) {
  if (v == null) return "—";
  return Number.isInteger(v) ? `${v}` : v.toFixed(1);
}

function Suggest({ s }) {
  if (!s || (s.lower_mm == null && s.upper_mm == null)) {
    return <span className={styles.dim}>{s?.note || "—"}</span>;
  }
  return (
    <div className={styles.suggest}>
      {s.lower_mm != null && (
        <span>
          ↓ {mm(s.lower_mm)} mm <em>({s.lower_cung}, Δ{mm(s.delta_lower)})</em>
        </span>
      )}
      {s.upper_mm != null && (
        <span>
          ↑ {mm(s.upper_mm)} mm <em>({s.upper_cung}, Δ{mm(s.delta_upper)})</em>
        </span>
      )}
      {s.note && <span className={styles.dim}>{s.note}</span>}
    </div>
  );
}

function ConfirmControl({ item, index, onConfirm, busy }) {
  const [val, setVal] = useState(
    item.dimension.value_mm != null ? String(item.dimension.value_mm) : "",
  );
  return (
    <div className={styles.confirmBox}>
      <input
        type="number"
        className={styles.confirmInput}
        value={val}
        onChange={(e) => setVal(e.target.value)}
        placeholder="mm"
      />
      <button
        type="button"
        className={styles.confirmBtn}
        disabled={busy || val === ""}
        onClick={() => onConfirm(index, Number(val))}
      >
        Xác nhận
      </button>
    </div>
  );
}

// onConfirm(index, valueMm) — nếu truyền, dòng "cần xác nhận" hiện ô nhập + nút.
// excluded (Set) + onToggleExclude(index) — nếu truyền, hiện cột "Xuất" tick chọn
// item nào ĐƯỢC xuất ra PNG/PDF (bỏ tick = loại khỏi bản in).
export default function DimensionTable({ items = [], onConfirm, busyIndex, excluded, onToggleExclude }) {
  const showExport = typeof onToggleExclude === "function";
  return (
    <div className={styles.wrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            {showExport && <th title="Tick = xuất ra PNG/PDF">Xuất</th>}
            <th>Kích thước</th>
            <th>Giá trị</th>
            <th>Thước</th>
            <th>Cung / Trạng thái</th>
            <th>Đề xuất</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it, i) => (
            <tr key={i} className={it.usable ? "" : styles.unusable}>
              {showExport && (
                <td className={styles.exportCell}>
                  <input
                    type="checkbox"
                    checked={!excluded?.has(i)}
                    onChange={() => onToggleExclude(i)}
                    aria-label="Xuất dòng này"
                  />
                </td>
              )}
              <td>
                {it.dimension.label}
                {it.dimension.need_confirm && (
                  <>
                    <span className={styles.confirm}> · cần xác nhận</span>
                    {onConfirm && (
                      <ConfirmControl
                        item={it}
                        index={i}
                        onConfirm={onConfirm}
                        busy={busyIndex === i}
                      />
                    )}
                  </>
                )}
              </td>
              <td>{mm(it.dimension.value_mm)} mm</td>
              <td>{it.loban.ruler ? `${it.loban.ruler} cm` : "—"}</td>
              <td>
                <CungBadge loban={it.loban} />
              </td>
              <td>
                <Suggest s={it.suggestion} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
