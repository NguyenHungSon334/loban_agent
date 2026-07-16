import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useJob } from "../hooks/useJob.js";
import { retryJob } from "../api/client.js";
import Card from "../components/Card.jsx";
import Button from "../components/Button.jsx";
import styles from "./Analyzing.module.css";

const STEPS = [
  ["queued", "Xếp hàng"],
  ["extract", "Bóc tách kích thước (AI đọc bản vẽ)"],
  ["classify", "Tra cung Lỗ Ban + đề xuất"],
  ["render", "Xuất JSON / PNG / PDF"],
];

export default function Analyzing() {
  const { hoSo } = useParams();
  const { data, error } = useJob(hoSo);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [retrying, setRetrying] = useState(false);
  const [retryErr, setRetryErr] = useState(null);
  const status = data?.status;

  useEffect(() => {
    if (status === "done") {
      navigate(`/report/${encodeURIComponent(hoSo)}`, { replace: true });
    }
  }, [status, hoSo, navigate]);

  async function onRetry() {
    setRetrying(true);
    setRetryErr(null);
    try {
      await retryJob(hoSo);                        // đặt lại status=queued phía server
      await queryClient.invalidateQueries({ queryKey: ["job", hoSo] });  // bật lại poll
    } catch (e) {
      setRetryErr(e.message);
    } finally {
      setRetrying(false);
    }
  }

  const activeIdx = STEPS.findIndex(([s]) => s === status);

  return (
    <section className={`container ${styles.page}`}>
      <h2>Đang xử lý hồ sơ {hoSo}</h2>

      {error && <p className={styles.err}>Lỗi tải trạng thái: {error.message}</p>}

      {status === "error" ? (
        <Card variant="product" className={styles.errCard}>
          <h3>Xử lý thất bại</h3>
          <p>{data.error || "Lỗi không xác định."}</p>
          {retryErr && <p className={styles.err}>{retryErr}</p>}
          <div className={styles.errActions}>
            <Button onClick={onRetry} disabled={retrying}>
              {retrying ? "Đang chạy lại…" : "Thử lại"}
            </Button>
            <Button variant="secondary" as="a" href="/">
              Về trang chính
            </Button>
          </div>
        </Card>
      ) : (
        <Card variant="feature" className={styles.steps}>
          {STEPS.map(([s, label], i) => {
            const done = activeIdx > i;
            const active = activeIdx === i || (activeIdx < 0 && i === 0);
            return (
              <div
                key={s}
                className={`${styles.step} ${done ? styles.done : ""} ${
                  active ? styles.active : ""
                }`}
              >
                <span className={styles.dot} />
                {label}
              </div>
            );
          })}
        </Card>
      )}
    </section>
  );
}
