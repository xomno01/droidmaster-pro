# ⚡ DroidMaster Pro — Universal Android Control Center

<p align="center">
  <img src="app_icon.ico" width="100" height="100" alt="DroidMaster Pro Logo" />
  <br>
  <strong>Modern, Ultra-Lightweight Android Control & 60FPS Hardware Screen Mirroring Hub</strong>
  <br>
  <em>Tối ưu hóa phần cứng • Không độ trễ • Giao diện Bento Grid 2026 • Điều khiển mọi máy Android</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white" />
  <img src="https://img.shields.io/badge/Mirror-Scrcpy%204.1-FF6B6B?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" />
</p>

---

## 🌟 Giới Thiệu / Overview

**DroidMaster Pro** là phần mềm máy tính (Native Desktop App) chuyên nghiệp, siêu nhẹ, hỗ trợ nhận diện và điều khiển **tất cả mọi dòng điện thoại Android** thông qua giao thức ADB và bộ mã hóa phần cứng Scrcpy. 

Phần mềm được thiết kế theo xu hướng thẩm mỹ **Bento Grid & Dark Obsidian 2026** (lấy cảm hứng từ Linear, Raycast và macOS), mang lại trải nghiệm làm việc trực quan, thoáng đãng và cực kỳ mượt mà.

---

## ✨ Tính Năng Nổi Bật / Key Features

### 1. 🖥️ Chiếu Màn Hình 60FPS Siêu Nhẹ (Scrcpy Pro Hub)
* **Tốc độ 60 FPS, độ trễ ~0ms:** Giải mã trực tiếp bằng GPU phần cứng, chiếm **< 1% CPU** và chỉ **~25MB RAM**.
* **Tắt màn hình điện thoại:** Màn hình vật lý của điện thoại tắt đen ngòm để chống nóng máy và bảo vệ pin, trong khi màn hình máy tính vẫn hiển thị và điều khiển chuột/phím bình thường.
* **Luôn ghim trên cùng (Always on Top):** Cửa sổ điện thoại luôn nổi cạnh các phần mềm đang làm việc.
* **Tùy chỉnh độ phân giải:** Full HD+ (1080p), 720p (siêu nhẹ cho máy yếu) hoặc gốc.

### 2. 📱 Quản Lý Đa Thiết Bị (Multi-Device Auto Detect)
* Tự động quét và nhận diện mọi điện thoại Android cắm qua cáp USB hoặc mạng Wi-Fi.
* Hỗ trợ thanh Dropdown chuyển đổi điều khiển giữa nhiều máy nhanh chóng.
* **Bảng thông số Telemetry thời gian thực:** Model, Android OS, Mức Pin, Nhiệt độ phần cứng, Độ phân giải, Địa chỉ IP.

### 3. 🎮 Thanh Điều Khiển Từ Xa (Remote Nav Dock)
* Cụm phím điều hướng bo tròn dạng viên thuốc (Dynamic Island):
  * `◀ Quay lại (Back)`
  * `● Về trang chính (Home)`
  * `■ Đa nhiệm (Recents)`
  * `🔔 Hạ thanh thông báo (Notification Shade)`
  * `🔒 Bật / Khóa nguồn (Power)`
  * `🔉 / 🔊 Tăng giảm âm lượng`
* **Gõ chữ xuyên nền tảng (Text Injector):** Nhập văn bản hoặc đường link trên PC và nhấn Enter để bắn trực tiếp vào ô nhập liệu của điện thoại.

### 4. 🛠️ Hộp Công Cụ Bento (Quick Toolbox)
* 📸 **Chụp Màn Hình:** Bấm 1 nút lưu ngay ảnh HD vào thư mục `Pictures/DroidMaster` trên PC và tự mở ảnh.
* 📦 **Cài Đặt APK:** Hộp thoại chọn file `.apk` cài đặt trực tiếp vào điện thoại chỉ với 1 click.
* 📶 **Không Dây Wi-Fi:** Tự động kích hoạt cổng `5555` và kết nối không dây, cho phép rút dây cáp USB.
* 🤖 **Bot Phantom Scroll:** Kịch bản tự động hóa mở Facebook, lướt đọc báo công nghệ Tinhte và xem Nekogram trong 60 giây.
* 🚀 **Mở Nhanh Ứng Dụng:** Hàng phím squircle 1-click mở YouTube, Chrome, Facebook, Nekogram, Cài đặt, Camera.
* 💻 **Console Log:** Khung theo dõi log phong cách macOS Terminal với 3 chấm đỏ-vàng-xanh.

### 5. 🕶️ Chế Độ Hacker CLI (`cyber_droid.py`)
* Đi kèm script giao diện dòng lệnh mang phong cách **Cyberpunk / Hollywood Hacker** dành cho các anh em thích điều khiển điện thoại bằng terminal ngầu như phim điện ảnh.

---

## 🚀 Cài Đặt & Khởi Chạy / Getting Started

### Cách 1: Chạy từ Mã Nguồn (Source Code)

1. **Clone repository:**
   ```bash
   git clone https://github.com/xomno01/droidmaster-pro.git
   cd droidmaster-pro
   ```

2. **Cài đặt các thư viện cần thiết:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Khởi chạy phần mềm:**
   ```bash
   python main.py
   ```
   *(Hoặc nhấp đúp vào file `run_droid_master.bat`)*

---

### Cách 2: Tự Đóng Gói Thành File `.exe` Độc Lập (Build Standalone)

Nếu muốn đóng gói thành 1 thư mục Portable chạy được trên mọi máy Windows không cần cài Python:
```bash
pyinstaller --noconsole --name "DroidMaster_Pro" --icon "app_icon.ico" --add-data "bin;bin" --add-data "app_icon.ico;." main.py -y
```
File `.exe` sẽ nằm trong thư mục `dist/DroidMaster_Pro/`.

---

## 📁 Cấu Trúc Dự Án / Project Structure

```
droidmaster-pro/
├── bin/                   # Toàn bộ file thực thi Scrcpy 4.1 và ADB portable
│   ├── adb.exe
│   ├── scrcpy.exe
│   ├── scrcpy-server
│   ├── SDL3.dll
│   └── ...
├── main.py                # Giao diện chính PySide6 (Bento UI 2026)
├── adb_core.py            # Module xử lý lệnh ADB & Scrcpy bất đồng bộ
├── styles.py              # Bảng giao diện Dark Obsidian QSS
├── cyber_droid.py         # Terminal Hacker CLI C2 Interface
├── phantom_agent.py       # Kịch bản Bot lướt mạng xã hội tự động
├── app_icon.ico           # Biểu tượng phần mềm sấm sét neon
├── run_droid_master.bat   # Script khởi chạy nhanh 1-click
├── requirements.txt       # Danh sách thư viện Python
└── README.md
```

---

## 🛡️ Yêu Cầu Thiết Bị Android / Requirements

* Bất kỳ điện thoại Android nào chạy **Android 5.0 trở lên**.
* Đã bật **Gỡ lỗi USB (USB Debugging)** trong phần *Tùy chọn cho nhà phát triển*.
* **KHÔNG CẦN ROOT:** Toàn bộ tính năng đều chạy qua giao thức chuẩn của Android.

---

## 📄 Bản Quyền / License

Dự án được phát hành theo giấy phép **MIT License**. Tự do sử dụng, chỉnh sửa và phân phối.
