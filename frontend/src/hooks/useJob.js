import { useQuery } from "@tanstack/react-query";
import { getJob } from "../api/client.js";

// poll tới khi done/error (plan trang 2). Ngừng poll khi xong.
export function useJob(hoSo) {
  return useQuery({
    queryKey: ["job", hoSo],
    queryFn: () => getJob(hoSo),
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      return s === "done" || s === "error" ? false : 800;
    },
  });
}
