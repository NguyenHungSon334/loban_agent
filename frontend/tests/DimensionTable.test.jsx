import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import DimensionTable from "../src/components/DimensionTable.jsx";

const items = [
  {
    dimension: { label: "Rộng mộ", value_mm: 870, need_confirm: false },
    loban: { ruler: "38.8", cung: "Vượng", status: "tot", near_border: false },
    suggestion: { note: "đang đạt" },
    usable: true,
  },
  {
    dimension: { label: "Lọt lòng cổng", value_mm: 610, need_confirm: true },
    loban: { ruler: "52.2", cung: "Hiểm Họa", status: "chua_phu_hop", near_border: false },
    suggestion: { lower_mm: 522, lower_cung: "Quý Nhân", delta_lower: 88, upper_mm: null },
    usable: true,
  },
  {
    dimension: { label: "Rộng lối đi", value_mm: 590, need_confirm: false },
    loban: { ruler: "42.9", cung: "Nghĩa", status: "tot", near_border: true },
    suggestion: null,
    usable: true,
  },
];

describe("DimensionTable", () => {
  test("hiện badge trạng thái đúng theo status", () => {
    render(<DimensionTable items={items} />);
    expect(screen.getByText(/Vượng · Tốt/)).toBeInTheDocument();
    expect(screen.getByText(/Hiểm Họa · Chưa phù hợp/)).toBeInTheDocument();
  });

  test("near_border -> badge Sát biên", () => {
    render(<DimensionTable items={items} />);
    expect(screen.getByText("Sát biên")).toBeInTheDocument();
  });

  test("đề xuất hạ hiện mm + cung + delta", () => {
    render(<DimensionTable items={items} />);
    expect(screen.getByText(/522 mm/)).toBeInTheDocument();
    expect(screen.getByText(/Quý Nhân, Δ88/)).toBeInTheDocument();
  });

  test("cần xác nhận đánh dấu ở nhãn", () => {
    render(<DimensionTable items={items} />);
    expect(screen.getByText(/cần xác nhận/)).toBeInTheDocument();
  });
});
