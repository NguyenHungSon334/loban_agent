# Deploy — Google Cloud VPS (Compute Engine) + Docker

Kiến trúc: 1 process uvicorn (worker asyncio in-process + SQLite + file `output/`).
Chạy Docker Compose sau Caddy (auto HTTPS). State lưu volume `loban_data` — bền qua
restart/redeploy.

## 1. Tạo VM (Compute Engine)

Console → Compute Engine → VM instances → Create, hoặc gcloud:

```bash
gcloud compute instances create loban \
  --machine-type=e2-small \                # 2 vCPU / 2GB — đủ cho MVP
  --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --tags=http-server,https-server \        # mở firewall 80/443 mặc định
  --zone=asia-southeast1-a                  # Singapore, gần VN
```

Nếu tạo bằng Console: tick **Allow HTTP** + **Allow HTTPS** ở mục Firewall.

Ghi lại **External IP** của VM.

## 2. Cài Docker trên VM

```bash
gcloud compute ssh loban --zone=asia-southeast1-a      # hoặc SSH nút trên Console

# trong VM:
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
exit                                                    # thoát rồi SSH lại để nhận group
```

## 3. Đưa code lên VM

```bash
# cách A — git (khuyến nghị)
git clone <repo-url> loban && cd loban

# cách B — scp từ máy Windows (PowerShell), nếu chưa có git remote
#   gcloud compute scp --recurse . loban:~/loban --zone=asia-southeast1-a
```

## 4. Cấu hình .env

```bash
cp .env.example .env
nano .env
```

- `LOBAN_GEMINI_API_KEY` = API key Gemini (bắt buộc).
- `DOMAIN` = tên miền (vd `loban.example.com`) nếu đã trỏ A record về External IP →
  Caddy tự cấp HTTPS. Chưa có tên miền → để trống, chạy HTTP qua IP.

## 5. Chạy

```bash
docker compose up -d --build
docker compose logs -f app        # xem log tiến trình xử lý hồ sơ
```

Mở `http://EXTERNAL_IP` (hoặc `https://DOMAIN`).

## 6. HTTPS (tên miền)

1. DNS: tạo bản ghi **A** `loban.example.com` → External IP của VM.
2. Đặt `DOMAIN=loban.example.com` trong `.env`.
3. `docker compose up -d`  → Caddy tự xin Let's Encrypt.

> External IP nên đặt **Static** (VPC → External IP → reserve) để không đổi khi restart VM.

## 7. Cập nhật phiên bản

```bash
git pull
docker compose up -d --build
```

## 8. Backup dữ liệu (SQLite + hồ sơ)

```bash
docker run --rm -v loban_loban_data:/data -v $PWD:/backup alpine \
  tar czf /backup/loban-backup-$(date +%F).tar.gz -C /data .
```

Khôi phục: giải nén ngược vào volume `loban_loban_data`.

## VM RAM nhỏ (e2-micro 1GB free tier)

`npm run build` lúc `docker compose up --build` có thể hết RAM (OOM). Tạo swap 2GB
trước khi build:

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab   # giữ swap sau reboot
```

Đặt `LOBAN_WEB_WORKER_CONCURRENCY=1` trong `.env`.

## Lưu ý quy mô

- **Không scale ngang** (queue in-memory + SQLite 1 file) → giữ **1 instance**.
  Cần nhiều hơn: đổi sang Redis/Postgres (không thuộc MVP).
- `LOBAN_WEB_WORKER_CONCURRENCY` khớp RAM: e2-small để **2**, e2-medium để 3–4.
- Chi phí Gemini theo số ảnh — bước `extract` là phần chậm/tốn, xem log `[ho_so] extract ...`.
