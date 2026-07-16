import { useEffect, useRef, useState } from "react";
import styles from "./Select.module.css";

// Dropdown custom: nút + panel bay ra (fade + trượt), click ngoài/Esc đóng.
// options: [{ value, label }]. onChange(value).
export default function Select({ value, onChange, options, placeholder = "Chọn…", className = "" }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const current = options.find((o) => o.value === value);

  useEffect(() => {
    if (!open) return;
    function onDoc(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    function onKey(e) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function pick(v) {
    onChange(v);
    setOpen(false);
  }

  return (
    <div className={`${styles.wrap} ${className}`} ref={ref}>
      <button
        type="button"
        className={`${styles.trigger} ${open ? styles.triggerOpen : ""}`}
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className={styles.label}>{current?.label ?? placeholder}</span>
        <svg className={`${styles.chev} ${open ? styles.chevOpen : ""}`} viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      <ul className={`${styles.menu} ${open ? styles.menuOpen : ""}`} role="listbox">
        {options.map((o) => (
          <li
            key={o.value}
            role="option"
            aria-selected={o.value === value}
            className={`${styles.opt} ${o.value === value ? styles.optSel : ""}`}
            onClick={() => pick(o.value)}
          >
            {o.label}
            {o.value === value && <span className={styles.check}>✓</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
