import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, test } from "vitest";
import NewAnalysis from "../src/pages/NewAnalysis.jsx";

function setup() {
  return render(
    <MemoryRouter>
      <NewAnalysis />
    </MemoryRouter>,
  );
}

describe("NewAnalysis form", () => {
  test("báo lỗi khi thiếu mã hồ sơ", async () => {
    setup();
    fireEvent.click(screen.getByRole("button", { name: "Phân tích" }));
    expect(await screen.findByText("Bắt buộc nhập mã hồ sơ")).toBeInTheDocument();
  });

  test("báo lỗi khi có mã nhưng chưa chọn file", async () => {
    setup();
    fireEvent.change(screen.getByPlaceholderText("HS01"), {
      target: { value: "HS01" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Phân tích" }));
    expect(await screen.findByText(/Chọn ít nhất 1 file/)).toBeInTheDocument();
  });
});
