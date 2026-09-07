# 🔒 Chính Sách Bảo Mật & Ranh Giới Tin Cậy / Security Policy & Trust Boundary

Tài liệu này định nghĩa chính sách bảo mật, mô hình ranh giới tin cậy (Trust Boundary) giữa máy trạm (Host PC) và thiết bị Android, cùng quy trình kiểm tra tính toàn vẹn nhị phân (Binary Integrity Verification) cho dự án **DroidMaster Pro**.

---

## 1. 🛡️ Chính Sách Bảo Mật (Supported Versions & Vulnerability Reporting)

### Các Phiên Bản Được Hỗ Trợ

Chúng tôi cam kết phát hành các bản vá bảo mật và cập nhật kỹ thuật cho các phiên bản sau:

| Phiên bản | Trạng thái hỗ trợ | Ghi chú |
| :--- | :--- | :--- |
| **v2.9.x (Smart Profiles & Resilient Remote)** | ✅ Đang hỗ trợ chính thức | Phiên bản Danh bạ thiết bị, 1-Click Remote, Silent Auto-Reconnect, Tối ưu hóa Model |
| **v2.8.x (Production-Grade & Responsive UI)** | ⚠️ Hỗ trợ bảo trì | Phiên bản kiến trúc Zero-Eval, Responsive Bento Layout, Real CPU Telemetry |
| **v2.7.x (Production-Grade Hardening)** | ⚠️ Hỗ trợ bảo trì | Tiếp nhận bản vá an ninh quan trọng |
| < v2.7.0 | ❌ Ngừng hỗ trợ | Khuyến nghị nâng cấp lên v2.8.0+ |

### Quy Trình Báo Cáo Lỗ Hổng (Reporting a Vulnerability)

Nếu bạn phát hiện một vấn đề bảo mật hoặc nghi ngờ có lỗ hổng tiềm ẩn trong DroidMaster Pro:
1. **Không mở Issue công khai trên GitHub** để tránh nguy cơ tấn công Zero-Day.
2. Vui lòng gửi email mô tả chi tiết kèm mã khai thác chứng minh (PoC) về địa chỉ bảo mật của dự án hoặc sử dụng tính năng [GitHub Security Advisories - Report a vulnerability](https://github.com/xomno01/droidmaster-pro/security/advisories/new).
3. **Thời gian phản hồi cam kết (SLA):** Đội ngũ phát triển sẽ xác nhận tiếp nhận thông tin trong vòng **48 giờ** và đưa ra phương án khắc phục / bản vá trong vòng **7 ngày làm việc**.

---

## 2. 🏛️ Mô Hình Ranh Giới Tin Cậy ADB (ADB Trust Boundary)

Kiến trúc bảo mật của DroidMaster Pro được thiết kế xoay quanh giao thức kết nối ADB (Android Debug Bridge) và Scrcpy pipeline:

```
+-------------------------------------------------------------------------+
|                              HOST PC (Windows)                          |
|                                                                         |
|   +-----------------------------------------------------------------+   |
|   |  DroidMaster Pro App (Python / PySide6 GUI / CLI C2)           |   |
|   |  - Zero eval() / exec() Architecture                            |   |
|   |  - Typed PySide6 Signals (Thread-safe memory boundaries)         |   |
|   |  - Parameterized Subprocess Execution (shell=False)             |   |
|   +-------------------------------+---------------------------------+   |
|                                   | (IPC / Local Subprocess)            |
|                                   v                                     |
|   +-----------------------------------------------------------------+   |
|   |  Bundled Binaries (./bin/)                                      |   |
|   |  - adb.exe (Google Official Platform-Tools)                     |   |
|   |  - scrcpy.exe & SDL3 / FFmpeg DLLs (Genymobile v4.1 Official)   |   |
|   +-------------------------------+---------------------------------+   |
+-----------------------------------|-------------------------------------+
                                    |
          ==========================v==========================
          [ TRUST BOUNDARY: RSA 2048-bit Keypair Authentication ]
          ==========================+==========================
                                    | (USB Cable / Wi-Fi LAN Port 5555)
+-----------------------------------|-------------------------------------+
|                         ANDROID DEVICE (Target)                         |
|                                   v                                     |
|   +-----------------------------------------------------------------+   |
|   |  adbd (Android Debug Daemon - OS Kernel Level)                  |   |
|   |  - Context: uid=2000(shell), gid=2000(shell)                    |   |
|   |  - Permission Sandbox: Standard Android Shell User               |   |
|   |  - NO Root Required / NO Permanent su Escalation                 |   |
|   +-------------------------------+---------------------------------+   |
|                                   v                                     |
|   +-----------------------------------------------------------------+   |
|   |  Android Services & Scrcpy-Server Jar                           |   |
|   |  - MediaCodec / Hardware GPU Frame Encoder                      |   |
|   |  - Android Clipboard Service (cmd clipboard)                    |   |
|   |  - Input Injection Engine (Keyevent / Touch Tap)                |   |
|   +-----------------------------------------------------------------+   |
+-------------------------------------------------------------------------+
```

### Chi Tiết Các Nguyên Tắc Ranh Giới Bảo Mật

1. **Xác thực Cặp Khóa RSA (Host-to-Device Authentication):**
   * Thiết bị Android từ chối toàn bộ kết nối ADB cho đến khi người dùng mở khóa màn hình điện thoại và nhấn xác nhận tin cậy khóa công khai RSA của máy tính host (*"Cho phép gỡ lỗi USB từ máy tính này"*).
   * Cặp khóa xác thực được lưu trữ an toàn trong thư mục `%USERPROFILE%\.android\adbkey`.

2. **Ranh Giới Quyền Hạn Tối Thiểu (Principle of Least Privilege):**
   * Mọi thao tác tương tác thông qua `adb_core.py` đều thực thi dưới ngữ cảnh tài khoản **`shell` (UID: 2000)**.
   * DroidMaster Pro **không bao giờ yêu cầu quyền Superuser (`root`)** để hoạt động. Các phân vùng hệ thống (`/system`, `/vendor`) và dữ liệu nhạy cảm của các ứng dụng khác (`/data/data/<package>`) hoàn toàn được bảo vệ bởi Linux Sandbox của Android.

3. **Chống Lỗ Hổng Tiêm Lệnh (Command Injection Mitigation - Host-Side):**
   * Ứng dụng tuân thủ nghiêm ngặt nguyên tắc **Zero `eval()` / Zero `exec()`**.
   * Toàn bộ lệnh gọi nhị phân bên ngoài (`adb.exe`, `scrcpy.exe`) đều truyền danh sách đối số đã được tham số hóa (`args=[...]`) với tùy chọn `shell=False`. Điều này ngăn chặn triệt để kỹ thuật tấn công chèn ký tự đặc biệt (Metacharacter Injection: `&`, `|`, `;`, `` ` ``).

4. **Đồng Bộ Clipboard Tiếng Việt & Dữ Liệu Nhạy Cảm:**
   * Tính năng nhập liệu tiếng Việt sử dụng cơ chế đồng bộ clipboard hệ thống Android qua `cmd clipboard set text <string>` kết hợp sự kiện dán `input keyevent 279`.
   * **Khuyến cáo người dùng:** Tránh gửi các dữ liệu nhạy cảm (mật khẩu tài khoản ngân hàng, mã PIN, mã khôi phục ví điện tử, mã 2FA/OTP) qua clipboard khi kết nối trên các môi trường chưa được kiểm soát.

5. **Cảnh Báo An Toàn Kết Nối Không Dây (Wireless ADB TCP/IP Port 5555):**
   * Khi kích hoạt chế độ Wi-Fi ADB, daemon `adbd` trên điện thoại sẽ mở cổng TCP `5555` lắng nghe kết nối từ mạng cục bộ.
   * **Cảnh báo quan trọng:** Chỉ bật tính năng này trên mạng Wi-Fi gia đình hoặc văn phòng riêng biệt đáng tin cậy. **TUYỆT ĐỐI KHÔNG BẬT** Wireless ADB trên mạng Wi-Fi công cộng (quán cà phê, sân bay, khách sạn) vì các thiết bị khác trong cùng lớp mạng có thể quét thấy cổng 5555 và gửi lệnh vào thiết bị.
   * Sau khi hoàn tất phiên làm việc không dây, hãy hoàn nguyên về kết nối cáp USB an toàn qua lệnh:
     ```bash
     adb usb
     ```

---

## 3. 🔍 Kiểm Tra Tính Toàn Vẹn Của Binary Phụ Thuộc Trong `bin/`

DroidMaster Pro tích hợp sẵn bộ binary Scrcpy v4.1 và Android SDK Platform-Tools portable trong thư mục `bin/` để đảm bảo phần mềm có thể chạy ngay (out-of-the-box) mà người dùng không cần cài đặt thêm phần mềm rườm rà.

### Nguồn Gốc Binary & Giấy Phép Bản Quyền

* **ADB (`adb.exe`, `AdbWinApi.dll`, `AdbWinUsbApi.dll`):** Trích xuất từ gói chính thức **Google Android SDK Platform-Tools** cho Windows (Apache-2.0).
* **Scrcpy Suite (`scrcpy.exe`, `scrcpy-server`, `SDL3.dll`, FFmpeg DLLs):** Trích xuất từ bản phát hành chính thức **Genymobile Scrcpy v4.1** (Apache-2.0, zlib, LGPL-2.1+).
* Toàn bộ nguồn gốc, phiên bản và thông cáo bản quyền bên thứ ba được ghi chép chi tiết tại [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
* Siêu dữ liệu đối soát máy đọc được cung cấp tại [`bin/manifest.json`](bin/manifest.json).

### Bảng Mã Băm SHA-256 Chuẩn (Baseline Checksums)

Trước khi vận hành, người dùng và quản trị viên hệ thống có thể đối soát mã băm SHA-256 của các tệp trong thư mục `bin/` với bảng chuẩn dưới đây để đảm bảo các tệp thực thi chưa bị can thiệp hay nhiễm mã độc:

| Tệp tin nhị phân | Kích thước | SHA-256 Checksum Baseline |
| :--- | :--- | :--- |
| **`adb.exe`** | 8,485,016 bytes | `957E46B8615F7AF5B7292A2DDABE98D2E61940C3FB2B0545756507F080613E71` |
| **`AdbWinApi.dll`** | 108,184 bytes | `120BEF587119C6CB926B86B9BE90FDFBCE38937588EAE28CD91A94CE63C7B965` |
| **`AdbWinUsbApi.dll`** | 73,368 bytes | `6CA69A2CA0E31309C087D288F058977D421AD03500E4C3E1DBD981241A069C60` |
| **`scrcpy.exe`** | 720,524 bytes | `575CA1284345C7B3975585BC61B66D564A9A4F1ECB28FBB4C599C92A124054A9` |
| **`scrcpy-server`** | 733,706 bytes | `DEACB991ED2509715160FFDC7907E47B4160EB30D1566217E9047FD5B8850CAE` |
| **`SDL3.dll`** | 5,366,478 bytes | `0619EB2DA6032984DC6E2098897AEACDBD66B0415BB87BC03E628159BA60B15D` |
| **`avcodec-62.dll`** | 8,603,648 bytes | `7179DE2B132E78EB0A76458A0A3859DFE1EDCBB6D2EEB4A456F03F7AE96D5B66` |
| **`avformat-62.dll`** | 723,456 bytes | `7232316ACCE00371D89F589748B570D95885EA6BBFC1972A0A9D3B884903EEE1` |
| **`avutil-60.dll`** | 1,039,360 bytes | `3D6170DD68549C6F39B8D8710A37F79D9678905DF705A8B0A6BC7EA9037DADDF` |
| **`swresample-6.dll`** | 139,776 bytes | `4CC809D2CD822E186906FBC9D8A0ACFFA937E35DE1282B2E2AB7346CFED96FED` |
| **`libusb-1.0.dll`** | 227,005 bytes | `8EC130918A476B0DBD114C803E71314360608CEABDD2B6F38C83F6F208C608E0` |
| **`scrcpy-noconsole.vbs`**| 212 bytes | `3CCDA94C161F18CEF07C50D4D3C4913EB883D4B0FE3B939C35FAE52784FB1D2B` |
| **`open_a_terminal_here.bat`** | 5 bytes | `843758795A84D0D035A7D277AD29CC1FF1702048B4B61AE74B9E3439AE683423` |
| **`LICENSE.txt`** | 11,387 bytes | `01C12035BF35AF37241298DC7AD538EB2A07E5C940437BC6876FEEAA9D1951D0` |
| **`scrcpy.png`** | 6,530 bytes | `8E8CA237898FAA16014CDD118396AF53405B423F3DB0508C50CC3EDCE08EB313` |
| **`disconnected.png`** | 4,703 bytes | `E394873CD3E2CC3AB0CCA6212B10ED2A8A0FAD11A05675C8A9FA6F26F3AE12C0` |

### Lệnh Tự Động Kiểm Tra Checksum Qua PowerShell

Mở PowerShell tại thư mục gốc của dự án và thực thi lệnh sau:

```powershell
Get-ChildItem -Path ".\bin" -File | ForEach-Object {
    [PSCustomObject]@{
        File   = $_.Name
        SHA256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    }
} | Format-Table -AutoSize
```

Nếu phát hiện bất kỳ mã băm nào không khớp với bảng chuẩn trên, hãy ngừng chạy ứng dụng và tải lại bộ cài gốc từ kho lưu trữ GitHub chính thức.

---

## 4. 🧭 Thực Hành An Ninh Tốt Nhất Cho Người Dùng (Best Practices)

1. **Thu hồi ủy quyền USB khi không sử dụng:**
   * Trên thiết bị Android, định kỳ truy cập: *Cài đặt* -> *Tùy chọn cho nhà phát triển* -> Chọn **"Thu hồi ủy quyền gỡ lỗi USB" (Revoke USB debugging authorizations)**.
2. **Khóa màn hình thiết bị Android:**
   * Luôn thiết lập mã PIN, mật khẩu hoặc xác thực sinh trắc học cho điện thoại. ADB yêu cầu mở khóa màn hình để xác nhận ủy quyền kết nối lần đầu.
3. **Cập nhật định kỳ:**
   * Thường xuyên kéo phiên bản mới nhất từ kho mã nguồn chính thức để nhận các bản vá bảo mật và cải tiến tương thích từ cộng đồng.
