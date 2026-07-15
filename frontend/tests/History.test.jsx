import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, test, vi } from "vitest";

vi.mock("../src/api/client.js", () => ({
  listHoSo: vi.fn(() =>
    Promise.resolve([
      {
        ho_so: "HS01",
        status: "done",
        khach_hang: "Ông A",
        dia_diem: "Thanh Hóa",
        n_dim: 4,
        created_at: "2026-07-15T09:00:00Z",
      },
    ]),
  ),
}));

import History from "../src/pages/History.jsx";

function setup() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <History />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("History", () => {
  test("render hồ sơ + link tới báo cáo khi done", async () => {
    setup();
    expect(await screen.findByText("HS01")).toBeInTheDocument();
    expect(screen.getByText("Hoàn tất")).toBeInTheDocument();
    expect(screen.getByText("Ông A")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /HS01/ })).toHaveAttribute(
      "href",
      "/report/HS01",
    );
  });
});
