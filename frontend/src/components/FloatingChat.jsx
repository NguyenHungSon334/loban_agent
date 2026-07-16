import { useState } from "react";
import ChatPanel from "./ChatPanel.jsx";
import styles from "./FloatingChat.module.css";

// Bong bóng chat nổi góc phải. Ấn -> cửa sổ chat bay ra (scale + fade).
export default function FloatingChat({ hoSo, placeholder, autoAsk, onReply }) {
  const [open, setOpen] = useState(Boolean(autoAsk)); // có câu hỏi kèm -> mở sẵn

  return (
    <div className={styles.root}>
      <div className={`${styles.window} ${open ? styles.open : ""}`} role="dialog" aria-hidden={!open}>
        <div className={styles.head}>
          <span>Trợ lý Lỗ Ban · {hoSo}</span>
          <button className={styles.close} onClick={() => setOpen(false)} aria-label="Đóng">
            ×
          </button>
        </div>
        <div className={styles.body}>
          <ChatPanel hoSo={hoSo} placeholder={placeholder} autoAsk={autoAsk} onReply={onReply} />
        </div>
      </div>

      <button
        className={`${styles.fab} ${open ? styles.fabHidden : ""}`}
        onClick={() => setOpen(true)}
        aria-label="Mở chat"
        title="Hỏi AI về hồ sơ"
      >
        💬
      </button>
    </div>
  );
}
