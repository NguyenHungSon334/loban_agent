import Badge from "./Badge.jsx";

const STATUS = {
  tot: ["success", "Tốt"],
  chua_phu_hop: ["error", "Chưa phù hợp"],
  khong_ap_dung: ["default", "Không áp dụng"],
};

// hiện cung + trạng thái tốt/xấu; cờ near_border = rủi ro lệch cung khi thi công.
export default function CungBadge({ loban }) {
  const [tone, label] = STATUS[loban.status] || STATUS.khong_ap_dung;
  const cung = loban.cung
    ? loban.cung_nho
      ? `${loban.cung} › ${loban.cung_nho} · ${label}`
      : `${loban.cung} · ${label}`
    : label;
  const cross = loban.cross;
  return (
    <span style={{ display: "inline-flex", gap: 6, flexWrap: "wrap" }}>
      <Badge tone={tone}>{cung}</Badge>
      {loban.near_border && <Badge tone="orange">Sát biên</Badge>}
      {cross && cross.cung && (
        <Badge tone={cross.cung_good ? "success" : "error"}>
          {cross.ruler}: {cross.cung} {cross.cung_good ? "✓" : "△"}
        </Badge>
      )}
    </span>
  );
}
