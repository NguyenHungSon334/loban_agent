import { useQuery } from "@tanstack/react-query";
import { getReport } from "../api/client.js";

export function useReport(hoSo, enabled = true) {
  return useQuery({
    queryKey: ["report", hoSo],
    queryFn: () => getReport(hoSo),
    enabled,
  });
}
