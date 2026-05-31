# Chia sẻ Kiến thức Cơ Điện Tử

Ứng dụng Flask đơn giản để chia sẻ tài liệu về Điện công nghiệp, Cơ khí, Robot và Phần mềm.

Yêu cầu:
- Python 3.8+

Cài đặt và chạy:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python web.py
```

Truy cập http://localhost:5000

Admin

Set mật khẩu admin bằng biến môi trường `ADMIN_PASSWORD`. Mặc định là `admin` (chỉ dùng cho phát triển).

```powershell
$env:ADMIN_PASSWORD = 'your-secret'
python web.py
```

DB: file SQLite `data.db` sẽ được tự động tạo lần chạy đầu.

Deploy nhanh (gợi ý)

1) Deploy lên Render (khuyến nghị cho app Flask nhỏ):
	- Push project lên GitHub.
	- Tạo Web Service mới trên Render, chọn GitHub repo, branch, và `Python` as environment.
	- Build command: `pip install -r requirements.txt`
	- Start command: `gunicorn web:app`

2) Deploy bằng Docker (bất kỳ host hỗ trợ Docker):
	- Build image:

```powershell
docker build -t chia-se-codelectro:latest .
```

	- Chạy container:

```powershell
docker run -p 5000:5000 -e ADMIN_PASSWORD=your-secret chia-se-codelectro:latest
```

3) Lưu ý bảo mật:
	- Thiết lập `ADMIN_PASSWORD` trong biến môi trường trên host (không commit mật khẩu vào Git).
	- Đối với production, dùng HTTPS (letsencrypt) và migrate DB nếu cần. SQLite phù hợp cho prototyping; với môi trường production cân nhắc Postgres.
