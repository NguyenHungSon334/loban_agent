import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useReport } from "../hooks/useReport.js";
import { confirmDim, deleteHoSo, downloadBundle, downloadFile, retryJob } from "../api/client.js";
import Badge from "../components/Badge.jsx";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import DimensionTable from "../components/DimensionTable.jsx";
import styles from "./Report.module.css";

// file: tải 1 file · bundle: zip nhiều trang cùng loại
const DOWNLOADS = [
  { key: "json", label: "Tải JSON", file: "analysis.json" },
  { key: "png", label: "Tải PNG (full)", bundle: "png" },
  { key: "pdf", label: "Tải PDF A4", file: "report.pdf" },
];

export default function Report() {
  const { hoSo } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useReport(hoSo);
  const [busyIndex, setBusyIndex] = useState(null);
  const [action, setAction] = useState(null); // 'retry' | 'delete'
  const [dl, setDl] = useState(null); // tên file đang tải
  const [err, setErr] = useState(null);

  async function onDownload(item) {
    setDl(item.key);
    setErr(null);
    try {
      if (item.bundle) await downloadBundle(hoSo, item.bundle);
      else await downloadFile(hoSo, item.file);
    } catch (e) {
      setErr(`Tải ${item.label} lỗi: ${e.message}`);
    } finally {
      setDl(null);
    }
  }

  async function onConfirm(index, valueMm) {
    setBusyIndex(index);
    setErr(null);
    try {
      const updated = await confirmDim(hoSo, index, valueMm);
      queryClient.setQueryData(["report", hoSo], updated);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusyIndex(null);
    }
  }

  async function onRetry() {
    setAction("retry");
    try {
      await retryJob(hoSo);
      navigate(`/analyze/${encodeURIComponent(hoSo)}`);
    } catch (e) {
      setErr(e.message);
      setAction(null);
    }
  }

  async function onDelete() {
    if (!window.confirm(`Xóa hồ sơ ${hoSo}? Không hoàn tác được.`)) return;
    setAction("delete");
    try {
      await deleteHoSo(hoSo);
      navigate("/ho-so");
    } catch (e) {
      setErr(e.message);
      setAction(null);
    }
  }

  if (isLoading) return <Center>Đang tải báo cáo…</Center>;
  if (error) return <Center>Lỗi tải báo cáo: {error.message}</Center>;
  if (!data) return null;

  const { profile, items = [], need_confirm = [], near_border = [], warnings = [] } = data;

  return (
    <section className={`container ${styles.page}`}>
      <div className={styles.head}>
        <h2>Báo cáo {profile.ho_so}</h2>
        <div className={styles.chips}>
          {profile.khach_hang && <Badge>{profile.khach_hang}</Badge>}
          {profile.dia_diem && <Badge>{profile.dia_diem}</Badge>}
          {profile.huong_cong && <Badge>Hướng: {profile.huong_cong}</Badge>}
          {profile.vat_lieu && <Badge>{profile.vat_lieu}</Badge>}
          <Badge tone="accent">data {data.data_version}</Badge>
        </div>
      </div>

      <div className={styles.actions}>
        {DOWNLOADS.map((item) => (
          <Button
            key={item.key}
            variant="secondary"
            onClick={() => onDownload(item)}
            disabled={dl !== null}
          >
            {dl === item.key ? "Đang tải…" : item.label}
          </Button>
        ))}
        <span className={styles.spacer} />
        <Button variant="secondary" onClick={onRetry} disabled={action !== null}>
          {action === "retry" ? "Đang chạy lại…" : "Thử lại"}
        </Button>
        <Button variant="secondary" onClick={onDelete} disabled={action !== null}>
          Xóa hồ sơ
        </Button>
      </div>

      {err && <p className={styles.err}>{err}</p>}

      <Card variant="product" className={styles.tableCard}>
        <DimensionTable items={items} onConfirm={onConfirm} busyIndex={busyIndex} />
      </Card>

      {(need_confirm.length > 0 || near_border.length > 0) && (
        <Card variant="feature" className={styles.callout}>
          {need_confirm.length > 0 && (
            <div>
              <strong>Cần xác nhận:</strong> {need_confirm.join(", ")}
            </div>
          )}
          {near_border.map((n, i) => (
            <div key={i} className={styles.warnLine}>
              ⚠ {n}
            </div>
          ))}
        </Card>
      )}

      {warnings.map((w, i) => (
        <p key={i} className={styles.warning}>
          {w}
        </p>
      ))}
    </section>
  );
}

function Center({ children }) {
  return (
    <section className="container" style={{ padding: "var(--space-section) 0" }}>
      <p>{children}</p>
    </section>
  );
}
