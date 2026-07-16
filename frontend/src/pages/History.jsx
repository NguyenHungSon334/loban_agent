import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { deleteHoSo, listHoSo } from "../api/client.js";
import Badge from "../components/Badge.jsx";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import Select from "../components/Select.jsx";
import styles from "./History.module.css";

const LIMIT = 20;
const STATUS = {
  done: ["success", "Hoàn tất"],
  error: ["error", "Lỗi"],
};
const STATUS_OPTS = [
  { value: "", label: "Tất cả trạng thái" },
  { value: "done", label: "Hoàn tất" },
  { value: "error", label: "Lỗi" },
  { value: "processing", label: "Đang xử lý" },
];
const SORT_OPTS = [
  { value: "desc", label: "Mới nhất trước" },
  { value: "asc", label: "Cũ nhất trước" },
];

function statusBadge(s) {
  const [tone, label] = STATUS[s] || ["warning", "Đang xử lý"];
  return <Badge tone={tone}>{label}</Badge>;
}

function target(j) {
  return j.status === "done" ? `/report/${j.ho_so}` : `/analyze/${j.ho_so}`;
}

export default function History() {
  const [page, setPage] = useState(0);
  const [q, setQ] = useState("");
  const [qDebounced, setQDebounced] = useState("");
  const [status, setStatus] = useState("");
  const [sort, setSort] = useState("desc");
  const queryClient = useQueryClient();

  // debounce ô search 300ms + reset về trang đầu khi đổi filter
  useEffect(() => {
    const t = setTimeout(() => setQDebounced(q.trim()), 300);
    return () => clearTimeout(t);
  }, [q]);
  useEffect(() => setPage(0), [qDebounced, status, sort]);

  const { data = [], isLoading, error } = useQuery({
    queryKey: ["ho-so", page, qDebounced, status, sort],
    queryFn: () => listHoSo(page * LIMIT, LIMIT, { q: qDebounced, status, sort }),
    keepPreviousData: true,
  });

  async function onDelete(e, hoSo) {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm(`Xóa hồ sơ ${hoSo}?`)) return;
    await deleteHoSo(hoSo);
    queryClient.invalidateQueries({ queryKey: ["ho-so"] });
  }

  return (
    <section className={`container ${styles.page}`}>
      <h2>Hồ sơ đã phân tích</h2>

      <div className={styles.filters}>
        <input
          className={styles.search}
          type="search"
          placeholder="Tìm mã hồ sơ / khách hàng / địa điểm…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <Select value={status} onChange={setStatus} options={STATUS_OPTS} />
        <Select value={sort} onChange={setSort} options={SORT_OPTS} />
      </div>

      {isLoading && <p>Đang tải…</p>}
      {error && <p className={styles.err}>Lỗi tải danh sách: {error.message}</p>}
      {!isLoading && !error && data.length === 0 && (
        <p className={styles.empty}>
          {qDebounced || status ? (
            "Không có hồ sơ khớp bộ lọc."
          ) : (
            <>
              Chưa có hồ sơ nào. <Link to="/">Tạo phân tích mới</Link>.
            </>
          )}
        </p>
      )}

      <div className={styles.grid}>
        {data.map((j) => (
          <Link key={j.ho_so} to={target(j)} className={styles.link}>
            <Card variant="feature" className={styles.card}>
              <div className={styles.top}>
                <h3 className={styles.code}>{j.ho_so}</h3>
                <div className={styles.topRight}>
                  {statusBadge(j.status)}
                  <button
                    type="button"
                    className={styles.del}
                    title="Xóa hồ sơ"
                    onClick={(e) => onDelete(e, j.ho_so)}
                  >
                    ×
                  </button>
                </div>
              </div>
              <div className={styles.meta}>
                {j.khach_hang && <span>{j.khach_hang}</span>}
                {j.dia_diem && <span>{j.dia_diem}</span>}
                {j.n_dim != null && <span>{j.n_dim} kích thước</span>}
              </div>
              <time className={styles.date}>
                {new Date(j.created_at).toLocaleString("vi-VN")}
              </time>
            </Card>
          </Link>
        ))}
      </div>

      {(page > 0 || data.length === LIMIT) && (
        <div className={styles.pager}>
          <Button
            variant="secondary"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
          >
            ← Trước
          </Button>
          <span className={styles.pageNum}>Trang {page + 1}</span>
          <Button
            variant="secondary"
            disabled={data.length < LIMIT}
            onClick={() => setPage((p) => p + 1)}
          >
            Sau →
          </Button>
        </div>
      )}
    </section>
  );
}
