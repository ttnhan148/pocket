# Single-Deploy Deployment Guide — Pocket Platform

Tài liệu này hướng dẫn cách build, chạy và triển khai nền tảng Pocket dưới dạng **Single-Deploy** (nguyên khối chạy trên một Process duy nhất).

## Kiến trúc Single-Deploy
Hệ thống kết hợp Next.js UI tĩnh trực tiếp vào FastAPI:
1. **Next.js Static Export:** Frontend Next.js được compile thành các file HTML/JS/CSS tĩnh (thư mục `out/`).
2. **FastAPI Static Hosting:** FastAPI mount thư mục tĩnh này và xử lý Client-side routing, tự động trả về `index.html` cho các subpath không khớp với API.
3. **SQLite local DB:** Lưu trữ dữ liệu trực tiếp trên file database cục bộ.

---

## Cách 1: Chạy trực tiếp từ mã nguồn (Local Run)

### Yêu cầu hệ thống
- **Bun** (v1.x trở lên) hoặc **Node.js**
- **Python** (v3.10 trở lên)

### Bước 1: Build và đóng gói Frontend
Chạy script tự động ở thư mục gốc của dự án để build frontend Next.js và copy static resources sang backend:
```bash
python build_single_deploy.py
```

### Bước 2: Chạy Backend FastAPI
Di chuyển vào thư mục backend, kích hoạt môi trường ảo và chạy server Uvicorn:
```bash
cd backend
.venv\Scripts\activate  # Trên Windows
# source .venv/bin/activate  # Trên Linux/macOS

uvicorn app.main:app --port 8000
```

Mở trình duyệt truy cập `http://localhost:8000` để sử dụng toàn bộ ứng dụng (cả UI lẫn API)!

---

## Cách 2: Triển khai bằng Docker (Recommended)

Đóng gói hoàn chỉnh ứng dụng vào một Docker image duy nhất giúp chạy Pocket trên bất kỳ máy chủ nào mà không cần cài đặt Python/Node.js/Bun.

### Bước 1: Build Docker Image
Chạy lệnh sau tại thư mục gốc của dự án:
```bash
docker build -t pocket-platform .
```

### Bước 2: Khởi chạy Container với Persistent Storage
SQLite database cần lưu trữ persistent để không bị mất dữ liệu khi restart container. Sử dụng volume mount cho thư mục `/app/data/`:
```bash
docker run -d \
  -p 8000:8000 \
  -v pocket_data:/app/data \
  --name pocket-app \
  pocket-platform
```

Ứng dụng sẽ hoạt động tại địa chỉ: `http://localhost:8000`.

---

## Hướng dẫn Phát triển (Development Workflow)
Trong quá trình phát triển tính năng, để có phản hồi (hot reload) nhanh nhất từ UI, bạn nên chạy 2 server song song:
1. **Frontend dev server:** `bun run dev` (chạy tại port 3000)
2. **Backend API server:** `uvicorn app.main:app --reload` (chạy tại port 8000)
Sau khi hoàn tất tính năng, chạy `python build_single_deploy.py` để đóng gói lại phiên bản Single-Deploy và kiểm thử tự động với bộ test `pytest` & `playwright`.
