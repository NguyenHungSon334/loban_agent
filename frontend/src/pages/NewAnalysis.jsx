import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { analyze } from "../api/client.js";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import TextInput from "../components/TextInput.jsx";
import styles from "./NewAnalysis.module.css";

const FLAG_LABELS = { png: "Xuất PNG", pdf: "Xuất PDF A4" };

export default function NewAnalysis() {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [files, setFiles] = useState([]);
  const [flags, setFlags] = useState({ png: true, pdf: true });
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  function toggle(k) {
    setFlags((f) => ({ ...f, [k]: !f[k] }));
  }

  async function onSubmit(v) {
    if (!files.length && !v.cau_hoi?.trim()) {
      setErr("Chọn file bản vẽ, hoặc nhập số đo / câu hỏi cho Agent.");
      return;
    }
    setBusy(true);
    setErr(null);
    const fd = new FormData();
    fd.append("ho_so", v.ho_so);
    for (const k of ["khach_hang", "dia_diem", "huong_cong", "vat_lieu", "note", "cau_hoi"]) {
      if (v[k]) fd.append(k, v[k]);
    }
    for (const k of ["png", "pdf"]) fd.append(k, flags[k]);
    for (const f of files) fd.append("files", f);
    try {
      const r = await analyze(fd);
      navigate(`/analyze/${encodeURIComponent(r.ho_so)}`);
    } catch (e) {
      setErr(e.message);
      setBusy(false);
    }
  }

  return (
    <section className={`container ${styles.page}`}>
      <h1 className={styles.title}>Đối chiếu kích thước bản vẽ theo thước Lỗ Ban</h1>
      <p className={styles.lede}>
        Tải bản vẽ khu lăng mộ — hệ thống bóc tách kích thước, tra cung và đề xuất số đẹp.
      </p>

      <Card variant="feature" className={styles.card}>
        <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
          <label className={styles.drop}>
            <input
              type="file"
              multiple
              accept="image/*,.pdf"
              onChange={(e) => setFiles([...e.target.files])}
              className={styles.file}
            />
            <svg className={styles.dropIcon} viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="M7 18a4 4 0 0 1-.5-7.97 5.5 5.5 0 0 1 10.66-1.2A3.75 3.75 0 0 1 17.5 18H7Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
              <path
                d="M12 10v6m0-6 -2.2 2.2M12 10l2.2 2.2"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span className={styles.dropTitle}>
              {files.length
                ? `${files.length} file đã chọn: ${files.map((f) => f.name).join(", ")}`
                : "Kéo thả hoặc bấm chọn bản vẽ (Ảnh / PDF)"}
            </span>
            {!files.length && (
              <span className={styles.dropSub}>
                Hệ thống AI tự động đọc, tách kích thước và tra cung Lỗ Ban
              </span>
            )}
          </label>

          <TextInput
            label="Câu hỏi cho Agent"
            placeholder='Ví dụ: "Mộ rộng 87, dài 1m27 thuộc cung nào?" — nhập số đo để phân tích không cần ảnh'
            multiline
            {...register("cau_hoi")}
          />

          <div className={styles.grid}>
            <TextInput
              label="Mã hồ sơ *"
              placeholder="HS01"
              error={errors.ho_so?.message}
              {...register("ho_so", { required: "Bắt buộc nhập mã hồ sơ" })}
            />
            <TextInput label="Khách hàng" {...register("khach_hang")} />
            <TextInput label="Địa điểm" {...register("dia_diem")} />
            <TextInput label="Hướng cổng" {...register("huong_cong")} />
            <TextInput label="Vật liệu" {...register("vat_lieu")} />
          </div>

          <TextInput
            label="Ghi chú / thông số nhân viên nhập"
            multiline
            {...register("note")}
          />

          <div className={styles.flags}>
            {Object.keys(FLAG_LABELS).map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => toggle(k)}
                className={`${styles.pill} ${flags[k] ? styles.pillOn : ""}`}
              >
                {FLAG_LABELS[k]}
              </button>
            ))}
          </div>

          {err && <p className={styles.err}>{err}</p>}

          <Button type="submit" disabled={busy}>
            {busy ? "Đang gửi…" : "Phân tích"}
          </Button>
        </form>
      </Card>
    </section>
  );
}
