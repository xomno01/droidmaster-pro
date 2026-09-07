# -*- coding: utf-8 -*-
"""
================================================================================
  DROIDMASTER PRO // IN-APP USER GUIDE & KNOWLEDGE BASE
  Rich HTML In-App Viewer with Brand-by-Brand ADB Guides & Feature Walkthroughs
================================================================================
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextBrowser, QListWidget, QListWidgetItem,
    QFrame, QSplitter
)
from PySide6.QtGui import QFont, QCursor, QIcon

GUIDE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {
        font-family: 'Segoe UI', -apple-system, sans-serif;
        font-size: 14px;
        line-height: 1.65;
        color: #cbd5e1;
        background-color: #0b0f17;
        margin: 0;
        padding: 20px 28px;
    }
    h1 {
        font-size: 24px;
        font-weight: 800;
        color: #f8fafc;
        border-bottom: 2px solid #1e293b;
        padding-bottom: 10px;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    h2 {
        font-size: 18px;
        font-weight: 700;
        color: #38bdf8;
        margin-top: 30px;
        margin-bottom: 12px;
        border-left: 4px solid #38bdf8;
        padding-left: 10px;
    }
    h3 {
        font-size: 15px;
        font-weight: 700;
        color: #a855f7;
        margin-top: 20px;
        margin-bottom: 8px;
    }
    p {
        margin: 8px 0;
    }
    ul, ol {
        margin: 8px 0 16px 22px;
        padding: 0;
    }
    li {
        margin-bottom: 6px;
    }
    .card {
        background-color: #111827;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 14px 0;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 700;
        border-radius: 6px;
        background-color: #1e293b;
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .alert-box {
        background-color: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 10px;
        padding: 12px 16px;
        margin: 14px 0;
    }
    .alert-box-info {
        background-color: rgba(56, 189, 248, 0.08);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 10px;
        padding: 12px 16px;
        margin: 14px 0;
    }
    .alert-box-success {
        background-color: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 10px;
        padding: 12px 16px;
        margin: 14px 0;
    }
    code {
        font-family: 'Consolas', 'Courier New', monospace;
        background-color: #1e293b;
        color: #38bdf8;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12.5px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 14px 0;
    }
    th, td {
        border: 1px solid #1e293b;
        padding: 8px 12px;
        text-align: left;
    }
    th {
        background-color: #131d2e;
        color: #f8fafc;
        font-weight: 700;
    }
    tr:nth-child(even) {
        background-color: #0e1420;
    }
</style>
</head>
<body>

<h1>📖 CẨM NANG & HƯỚNG DẪN SỬ DỤNG DROIDMASTER PRO</h1>
<p>Chào mừng bạn đến với <b>DroidMaster Pro</b> — Trung tâm điều khiển và chiếu màn hình Android 60FPS thế hệ mới. Tài liệu này được tích hợp sẵn bên trong ứng dụng để giúp bạn làm chủ mọi tính năng từ cơ bản đến chuyên sâu mà không cần mở trình duyệt ngoài.</p>

<!-- ======================================================================= -->
<a name="sec_quickstart"></a>
<h2>🚀 PHẦN 1: BẮT ĐẦU NHANH & CHUẨN BỊ KẾT NỐI ADB</h2>

<div class="card">
    <p><b>ADB (Android Debug Bridge) là gì?</b><br>
    ADB là giao thức kết nối chính thức do Google phát triển, cho phép máy tính gửi lệnh điều khiển, truyền hình ảnh màn hình, âm thanh, cài đặt ứng dụng và truyền tệp tin trực tiếp tới điện thoại Android với tốc độ tức thì và độ trễ cực thấp.</p>
</div>

<h3>3 Bước Chuẩn Bị Cơ Bản:</h3>
<ol>
    <li><b>Cáp kết nối:</b> Sử dụng cáp USB Type-C có hỗ trợ truyền dữ liệu (không dùng cáp sạc trôi nổi chỉ có 2 dây nguồn). Khuyến khích cắm vào cổng USB 3.0 trực tiếp phía sau thùng máy để cấp nguồn và dữ liệu ổn định nhất.</li>
    <li><b>Bật chế độ nhà phát triển:</b> (Xem hướng dẫn cụ thể cho từng hãng điện thoại ở Phần 2 bên dưới).</li>
    <li><b>Cấp quyền tin cậy máy tính (RSA Key):</b> Khi cắm cáp USB lần đầu tiên, trên màn hình điện thoại sẽ hiện hộp thoại:
        <div class="alert-box-info">
            <b>"Cho phép gỡ lỗi USB từ máy tính này?"</b> (Allow USB debugging?)<br>
            👉 Bạn hãy <b>tích vào ô "Luôn cho phép từ máy tính này"</b> (Always allow) rồi bấm <b>OK / Cho phép</b>.
        </div>
    </li>
</ol>

<!-- ======================================================================= -->
<a name="sec_brands"></a>
<h2>📱 PHẦN 2: HƯỚNG DẪN BẬT ADB THEO TỪNG HÃNG MÁY CỤ THỂ</h2>

<!-- XIAOMI / POCO / REDMI -->
<a name="sec_xiaomi"></a>
<div class="card">
    <h3>🌟 1. Xiaomi / POCO / Redmi (MIUI 12, 13, 14 & Xiaomi HyperOS)</h3>
    <p><span class="badge">Đặc biệt quan trọng</span> Dòng máy Xiaomi có cơ chế bảo mật bổ sung nghiêm ngặt hơn các hãng khác.</p>
    <ol>
        <li>Vào <b>Cài đặt (Settings)</b> ➔ Chọn dòng đầu tiên: <b>Giới thiệu điện thoại (About Phone)</b>.</li>
        <li>Chạm liên tục <b>7 lần</b> vào dòng <b>Phiên bản MIUI</b> (hoặc <b>Phiên bản OS</b> trên HyperOS) cho đến khi máy báo <i>"Bạn đã là nhà phát triển"</i>.</li>
        <li>Quay lại màn hình Cài đặt chính ➔ Kéo xuống chọn <b>Cài đặt bổ sung (Additional settings)</b> ➔ Chọn <b>Tùy chọn nhà phát triển (Developer options)</b>.</li>
        <li>Gạt bật <b>Gỡ lỗi USB (USB debugging)</b>.</li>
    </ol>
    <div class="alert-box">
        <b>⚠️ BƯỚC BẮT BUỘC RIÊNG CHO XIAOMI / POCO:</b><br>
        Trong mục <i>Tùy chọn nhà phát triển</i>, bạn <b>PHẢI BẬT THÊM 2 MỤC SAU</b>:<br>
        1. <b>Cài đặt qua USB (Install via USB)</b>.<br>
        2. <b>Gỡ lỗi USB (Cài đặt bảo mật) / USB debugging (Security settings)</b>.<br>
        <i>(Lưu ý: Xiaomi sẽ yêu cầu lắp SIM hoặc đăng nhập Mi Account, sau đó máy sẽ hiện 3 màn hình cảnh báo đếm ngược 5 giây. Bạn hãy đợi 5s và bấm "Tiếp tục" / "Chấp nhận" cả 3 lần. Nếu không bật mục này, bạn sẽ không thể điều khiển chuột hoặc cài file APK từ máy tính!)</i>
    </div>
</div>

<!-- SAMSUNG -->
<a name="sec_samsung"></a>
<div class="card">
    <h3>🌟 2. Samsung Galaxy (One UI mọi phiên bản)</h3>
    <ol>
        <li>Vào <b>Cài đặt (Settings)</b> ➔ Kéo xuống dưới cùng chọn <b>Thông tin điện thoại (About phone)</b>.</li>
        <li>Chọn mục <b>Thông tin phần mềm (Software information)</b>.</li>
        <li>Chạm liên tục <b>7 lần</b> vào dòng <b>Số hiệu bản tạo (Build number)</b>. Nhập mã PIN màn hình nếu có.</li>
        <li>Quay lại màn hình Cài đặt chính ➔ Kéo xuống dưới cùng sẽ thấy mục mới: <b>Cài đặt cho người phát triển (Developer options)</b>.</li>
        <li>Tìm và gạt bật mục <b>Gỡ lỗi USB (USB debugging)</b> ➔ Chọn <b>OK</b>.</li>
    </ol>
</div>

<!-- OPPO & REALME -->
<a name="sec_oppo"></a>
<div class="card">
    <h3>🌟 3. OPPO & Realme (ColorOS / Realme UI)</h3>
    <ol>
        <li>Vào <b>Cài đặt</b> ➔ <b>Giới thiệu thiết bị (About device)</b> ➔ Chọn <b>Phiên bản (Version)</b>.</li>
        <li>Chạm liên tục <b>7 lần</b> vào dòng <b>Số bản dựng (Build number)</b>.</li>
        <li>Quay lại Cài đặt ➔ Chọn <b>Cài đặt hệ thống (System settings)</b> (hoặc Cài đặt bổ sung) ➔ Chọn <b>Tùy chọn cho nhà phát triển</b>.</li>
        <li>Bật <b>Gỡ lỗi USB</b>.</li>
        <li><i>(Mẹo thêm):</i> Kéo xuống dưới bật thêm mục <b>Tắt giám sát quyền (Disable permission monitoring)</b> nếu có để tránh pop-up làm phiền.</li>
    </ol>
</div>

<!-- VIVO -->
<a name="sec_vivo"></a>
<div class="card">
    <h3>🌟 4. Vivo & iQOO (Funtouch OS / OriginOS)</h3>
    <ol>
        <li>Vào <b>Cài đặt</b> ➔ Chọn <b>Quản lý hệ thống (System management)</b> hoặc <b>Thông tin điện thoại</b>.</li>
        <li>Chọn <b>Thông tin phần mềm</b> ➔ Chạm liên tục <b>7 lần</b> vào <b>Số hiệu bản dựng</b>.</li>
        <li>Quay lại <b>Cài đặt hệ thống</b> ➔ Chọn <b>Tùy chọn nhà phát triển</b> ➔ Bật <b>Gỡ lỗi USB</b>.</li>
    </ol>
</div>

<!-- GOOGLE PIXEL & ANDROID THUẦN -->
<a name="sec_pixel"></a>
<div class="card">
    <h3>🌟 5. Google Pixel, Sony, Motorola & Android Thuần (AOSP)</h3>
    <ol>
        <li>Vào <b>Settings</b> ➔ <b>About phone</b> ➔ Kéo xuống dưới chạm <b>7 lần</b> vào <b>Build number</b>.</li>
        <li>Quay lại <b>Settings</b> ➔ <b>System</b> ➔ <b>Developer options</b> ➔ Bật <b>USB debugging</b>.</li>
    </ol>
</div>

<!-- HUAWEI -->
<a name="sec_huawei"></a>
<div class="card">
    <h3>🌟 6. Huawei & Honor (EMUI / Magic UI)</h3>
    <ol>
        <li>Vào <b>Cài đặt</b> ➔ <b>Giới thiệu về điện thoại</b> ➔ Chạm <b>7 lần</b> vào <b>Số phiên bản bản dựng</b>.</li>
        <li>Vào <b>Hệ thống & Cập nhật</b> ➔ <b>Tùy chọn nhà phát triển</b> ➔ Bật <b>Gỡ lỗi USB</b>.</li>
        <li>Bật thêm mục <b>"Cho phép gỡ lỗi ADB ở chế độ chỉ sạc"</b> (Allow ADB debugging in charge only mode).</li>
    </ol>
</div>

<!-- ======================================================================= -->
<a name="sec_wifi"></a>
<h2>📶 PHẦN 3: HƯỚNG DẪN KẾT NỐI KHÔNG DÂY (WI-FI ADB)</h2>

<div class="card">
    <p>DroidMaster Pro cho phép bạn hoàn toàn giải phóng dây cáp vướng víu và điều khiển điện thoại thông qua sóng Wi-Fi mượt mà như cắm dây.</p>
</div>

<h3>1. Quy trình kết nối Wi-Fi chuẩn (Cùng mạng gia đình/văn phòng):</h3>
<ol>
    <li><b>Cắm cáp USB nối điện thoại với máy tính 1 lần đầu tiên</b> để máy tính kích hoạt cổng mạng nhận lệnh <code>5555</code>.</li>
    <li>Đảm bảo điện thoại và máy tính đang cùng bắt chung 1 mạng Wi-Fi (hoặc máy tính cắm dây LAN cùng modem router Wi-Fi).</li>
    <li>Trên DroidMaster Pro, bấm vào thẻ <b>"Không Dây Wi-Fi"</b>. Ứng dụng sẽ tự động phát hiện IP của điện thoại, kích hoạt cổng và chuyển sang kết nối không dây.</li>
    <li><b>Rút cáp USB ra!</b> Bây giờ bạn đã có thể điều khiển điện thoại hoàn toàn qua Wi-Fi.</li>
</ol>

<div class="alert-box">
    <b>💡 LƯU Ý KHI NÀO CẦN CẮM LẠI CÁP USB?</b><br>
    Theo cơ chế bảo mật của Android: <b>Mỗi khi điện thoại bị tắt nguồn hoặc Khởi động lại (Reboot), Android sẽ tự động đóng cổng 5555</b>.<br>
    👉 Vì vậy, nếu sau một đêm máy tính báo Timeout không kết nối được Wi-Fi, bạn chỉ cần cắm cáp USB vào <b>1 lần duy nhất trong 3 giây</b>, bấm nút "Không Dây Wi-Fi" trên DroidMaster Pro rồi rút dây ra là xài tiếp!
</div>

<h3>2. Kết nối từ xa qua 4G/Internet bằng Tailscale:</h3>
<p>Nếu bạn đi làm xa mà để quên điện thoại ở nhà và cần truy cập khẩn cấp:</p>
<ol>
    <li>Cài ứng dụng <b>Tailscale</b> lên cả máy tính và điện thoại, đăng nhập cùng 1 tài khoản (hoàn toàn miễn phí).</li>
    <li>Lấy địa chỉ IP Tailscale của điện thoại (có dạng <code>100.x.y.z</code>).</li>
    <li>Mở DroidMaster Pro ➔ Bấm nút nhỏ <b>"⚙️ Đổi IP"</b> trên thẻ Wi-Fi ➔ Nhập địa chỉ <code>100.x.y.z:5555</code> ➔ Bấm OK.<br>
    Bạn có thể điều khiển điện thoại ở nhà từ bất kỳ đâu trên thế giới!</li>
</ol>

<h3>3. Cách đổi nhanh địa chỉ IP (Khi đổi mạng Wi-Fi hoặc dùng Tailscale):</h3>
<div class="alert-box-info">
    <b>⚙️ NÚT TOGGLE "ĐỔI IP" TIỆN LỢI TRÊN THẺ WI-FI:</b><br>
    Ngay trên tiêu đề thẻ <b>"Không Dây Wi-Fi"</b>, ứng dụng tích hợp sẵn nút nhỏ màu cam <code>⚙️ Đổi IP</code>.<br>
    👉 Bấm nút này bất cứ lúc nào để nhập địa chỉ IP mới (khi đổi sang mạng Wi-Fi khác hoặc chuyển sang IP Tailscale <code>100.x.y.z</code>). Ứng dụng sẽ tự động ngắt IP cũ và kết nối sang IP mới tức thì mà không cần cắm lại cáp!
</div>

<!-- ======================================================================= -->
<a name="sec_stream"></a>
<h2>🖥️ PHẦN 4: CHIẾU MÀN HÌNH (SCRCPY PRO) & CÁCH ĐỒNG BỘ 2 MÀN HÌNH CÙNG SÁNG</h2>

<div class="card">
    <h3>LÀM SAO ĐỂ MỞ ĐIỆN THOẠI LÊN VẪN THẤY NHỮNG GÌ ĐANG HIỂN THỊ THỰC TẾ?</h3>
    <p>Rất nhiều người dùng thắc mắc: <i>"Tại sao khi đang chiếu màn hình lên máy tính mà mở điện thoại lên thì màn hình điện thoại lại bị tắt hoặc đen thui?"</i></p>
    <p>👉 <b>Nguyên nhân:</b> Trong bảng điều khiển có tùy chọn <b>"Tắt màn hình máy (Tiết kiệm pin)"</b>. Khi bạn tích chọn ô này, Scrcpy sẽ chủ động ra lệnh tắt đèn màn hình điện thoại để chống nóng máy và tiết kiệm pin.</p>
    <div class="alert-box-success">
        <b>GIẢI PHÁP ĐỂ 2 MÀN HÌNH CÙNG SÁNG SONG SONG THỰC TẾ:</b><br>
        1. <b>BỎ TÍCH</b> ô <b>"Tắt màn hình máy"</b> trước khi bấm Chiếu màn hình. Khi đó, bạn thao tác trên máy tính thì trên màn hình điện thoại cũng sẽ sáng và hiển thị đồng thời y hệt 100% theo thời gian thực!<br>
        2. <b>Nếu đang chiếu mà lỡ bị tắt màn hình điện thoại:</b> Bạn chỉ cần bấm tổ hợp phím <b>Alt + Shift + O</b> trực tiếp trên cửa sổ chiếu của máy tính, hoặc bấm nút biểu tượng <b>💡 (Bật sáng màn hình)</b> trên thanh điều khiển bên trái của DroidMaster Pro để màn hình điện thoại bật sáng trở lại ngay lập tức!
    </div>
</div>

<h3>Bảng Phím Tắt Vàng Khi Đang Chiếu Màn Hình:</h3>
<table>
    <tr><th>Phím tắt</th><th>Thao tác tương ứng</th></tr>
    <tr><td><code>Alt + F</code></td><td>Bật / Tắt chế độ Toàn màn hình (Fullscreen)</td></tr>
    <tr><td><code>Alt + Shift + O</code></td><td><b>BẬT SÁNG LẠI MÀN HÌNH ĐIỆN THOẠI</b></td></tr>
    <tr><td><code>Alt + O</code></td><td>Tắt màn hình điện thoại (chỉ xem trên máy tính)</td></tr>
    <tr><td><code>Alt + P</code> hoặc Click chuột phải</td><td>Mở nguồn / Khóa màn hình</td></tr>
    <tr><td><code>Alt + H</code> hoặc Click chuột giữa</td><td>Về màn hình chính (Home)</td></tr>
    <tr><td><code>Alt + B</code> hoặc Chuột phải</td><td>Quay lại (Back)</td></tr>
    <tr><td><code>Alt + S</code></td><td>Mở danh sách ứng dụng gần đây (Recents / Đa nhiệm)</td></tr>
    <tr><td><code>Alt + N</code></td><td>Hạ thanh thông báo (Notification Panel)</td></tr>
    <tr><td><code>Alt + Mũi Tên Lên / Xuống</code></td><td>Tăng / Giảm âm lượng</td></tr>
    <tr><td><code>Kéo thả file APK vào cửa sổ</code></td><td>Tự động cài đặt file APK trực tiếp vào máy</td></tr>
    <tr><td><code>Kéo thả file ảnh / nhạc / tài liệu</code></td><td>Tự động copy file vào thư mục Download của điện thoại</td></tr>
</table>

<!-- ======================================================================= -->
<a name="sec_features"></a>
<h2>🛠️ PHẦN 5: CHI TIẾT CÁC TÍNH NĂNG TRÊN DROIDMASTER PRO</h2>

<div class="card">
    <h3>1. 📸 Chụp Màn Hình Siêu Tốc (Snapshot In-Memory)</h3>
    <ul>
        <li>Chụp ảnh màn hình điện thoại trực tiếp vào RAM máy tính với tốc độ dưới 0.3s.</li>
        <li>Tự động lưu file ảnh PNG sắc nét vào thư mục <code>captures/</code>.</li>
        <li><b>Tự động sao chép vào Clipboard:</b> Bạn chỉ cần sang Zalo, Telegram, Facebook hoặc Word bấm <code>Ctrl + V</code> là dán ngay ảnh chụp màn hình vừa chụp!</li>
    </ul>
</div>

<div class="card">
    <h3>2. 📦 Cài Đặt File APK (APK Installer)</h3>
    <ul>
        <li>Bấm vào thẻ <b>"Cài Đặt APK"</b> ➔ Chọn file <code>.apk</code> từ máy tính để cài đặt trực tiếp vào máy mà không cần copy thủ công.</li>
        <li>Hoặc bạn chỉ cần kéo và thả trực tiếp file <code>.apk</code> vào cửa sổ chiếu màn hình!</li>
    </ul>
</div>

<div class="card">
    <h3>3. 🤖 Bot Tự Động Hóa (Phantom Scroll Engine)</h3>
    <ul>
        <li>Tự động cuộn lướt xem bài viết, tin tức trên Facebook, Báo chí, Mạng xã hội với hành vi mô phỏng ngón tay người dùng tự nhiên (Bezier Curve Touch).</li>
        <li>Giúp đọc tin tức rảnh tay, kiểm tra độ mượt của app hoặc tự động giữ tương tác tài khoản.</li>
        <li><b>Nút Dừng Khẩn Cấp (Emergency Stop):</b> Khi Bot đang chạy, nút chuyển sang màu đỏ <i>"⏹ DỪNG BOT KHẨN CẤP"</i>. Bạn có thể bấm nút bất kỳ lúc nào để ngắt hoạt động tức thì trong 0.1 giây.</li>
    </ul>
</div>

<div class="card">
    <h3>4. ⌨️ Bắn Văn Bản & Đồng Bộ Tiếng Việt (Unicode Sync)</h3>
    <ul>
        <li>Điện thoại Android thông thường qua ADB rất dễ bị lỗi font hoặc mất dấu khi gõ tiếng Việt có dấu.</li>
        <li>DroidMaster Pro tích hợp công nghệ đồng bộ Clipboard: Bạn gõ bất kỳ đoạn văn bản tiếng Việt nào (ví dụ: <i>"Chào bạn, chúc một ngày tốt lành!"</i>) vào ô <i>"BẮN VĂN BẢN VÀO ĐIỆN THOẠI"</i> rồi bấm <b>Gửi ↵</b>. Toàn bộ câu từ tiếng Việt sẽ được chèn nguyên vẹn 100% chuẩn xác vào con trỏ điện thoại!</li>
    </ul>
</div>

<div class="card">
    <h3>5. 🎮 Thanh Dock Điều Khiển & Phím Ảo (Sidebar)</h3>
    <ul>
        <li><b>◀ Quay lại (Back):</b> Tương đương phím Back cứng.</li>
        <li><b>● Trang chính (Home):</b> Về màn hình chính điện thoại.</li>
        <li><b>■ Đa nhiệm (Recents):</b> Xem các app đang chạy ngầm để chuyển đổi hoặc đóng.</li>
        <li><b>🔔 Hạ thông báo:</b> Kéo thanh Notification xuống để xem tin nhắn/thông báo mới.</li>
        <li><b>💡 Sáng màn hình:</b> Đánh thức màn hình điện thoại khi đang tắt hoặc đang stream.</li>
        <li><b>🔒 Nguồn / Khóa máy:</b> Tắt hoặc bật màn hình.</li>
        <li><b>🔉 / 🔊 Âm lượng:</b> Tăng giảm âm thanh từ xa.</li>
    </ul>
</div>

<div class="card">
    <h3>6. 🚀 Mở Nhanh Ứng Dụng (Quick Launcher)</h3>
    <p>Bao gồm 6 nút bấm tiện lợi xếp theo lưới thích ứng giúp bạn mở tức thì:</p>
    <ul>
        <li><b>YouTube:</b> Bật xem video.</li>
        <li><b>Chrome:</b> Lướt web.</li>
        <li><b>Facebook:</b> Mạng xã hội.</li>
        <li><b>Nekogram / Telegram:</b> Nhắn tin liên lạc.</li>
        <li><b>Cài đặt:</b> Mở thẳng mục Cài đặt hệ thống để kiểm tra Wi-Fi, IP, bộ nhớ.</li>
        <li><b>Camera:</b> Khởi động máy ảnh tức thì.</li>
    </ul>
</div>

<!-- ======================================================================= -->
<a name="sec_faq"></a>
<h2>❓ PHẦN 6: CÂU HỎI THƯỜNG GẶP & KHẮC PHỤC SỰ CỐ (TROUBLESHOOTING)</h2>

<div class="card">
    <h3>1. Lỗi "ADBTimeoutError: Command timed out after 5s" khi kết nối Wi-Fi?</h3>
    <p><b>Nguyên nhân:</b> Do qua đêm Router Wi-Fi cấp số IP mới cho điện thoại, hoặc điện thoại vừa bị khởi động lại làm đóng cổng 5555.<br>
    <b>Cách xử lý:</b></p>
    <ul>
        <li>Vào Cài đặt điện thoại ➔ Wi-Fi ➔ Xem địa chỉ IP hiện tại là bao nhiêu.</li>
        <li>Nếu IP thay đổi: Bấm "Không Dây Wi-Fi" trên app và nhập IP mới vào.</li>
        <li>Nếu máy bị khởi động lại: Cắm cáp USB 1 lần trong 3s, bấm "Không Dây Wi-Fi" rồi rút cáp ra là xong.</li>
    </ul>
</div>

<div class="card">
    <h3>2. Báo lỗi "Device unauthorized" hoặc thiết bị không nhận?</h3>
    <p><b>Cách xử lý:</b> Mở khóa màn hình điện thoại, kiểm tra xem có pop-up hỏi <i>"Cho phép gỡ lỗi USB từ máy tính này?"</i> hay không. Hãy tích vào ô <b>"Luôn cho phép"</b> rồi bấm OK. Nếu không hiện, hãy rút cáp USB ra cắm lại vào cổng USB khác.</p>
</div>

<div class="card">
    <h3>3. Trên máy Xiaomi/POCO: Bật chiếu màn hình được nhưng chuột không bấm được hoặc không cài được APK?</h3>
    <p><b>Cách xử lý:</b> Bạn chưa bật mục <b>"Gỡ lỗi USB (Cài đặt bảo mật)"</b> và <b>"Cài đặt qua USB"</b> trong mục <i>Tùy chọn nhà phát triển</i> của Xiaomi. Hãy làm theo hướng dẫn chi tiết ở <b>Phần 2 - Mục 1</b> ở trên!</p>
</div>

<div style="text-align: center; margin-top: 40px; padding: 20px; color: #64748b; font-size: 12px; border-top: 1px solid #1e293b;">
    ⚡ DroidMaster Pro • Thiết kế & Phát triển chuẩn tương lai 2026 • Chúc bạn có trải nghiệm tuyệt vời!
</div>

</body>
</html>
"""

class UserGuideDialog(QDialog):
    """
    In-App Native User Guide Modal.
    Loads comprehensive HTML documentation into QTextBrowser with instant table of contents jump.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📖 DroidMaster Pro — Cẩm Nang & Hướng Dẫn Sử Dụng Toàn Diện")
        self.resize(960, 660)
        self.setMinimumSize(720, 500)
        self.setWindowModality(Qt.NonModal)

        self.setStyleSheet("""
            QDialog {
                background-color: #0b0f17;
            }
            QListWidget {
                background-color: #0e1420;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                color: #cbd5e1;
                font-size: 13px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 8px;
                margin-bottom: 4px;
            }
            QListWidget::item:hover {
                background-color: rgba(56, 189, 248, 0.12);
                color: #38bdf8;
            }
            QListWidget::item:selected {
                background-color: #38bdf8;
                color: #0b0f17;
                font-weight: 700;
            }
            QLineEdit {
                background-color: #111827;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                color: #f8fafc;
                font-size: 13px;
                padding: 8px 12px;
            }
            QLineEdit:focus {
                border-color: #38bdf8;
            }
            QPushButton#closeGuideBtn {
                background-color: #1e293b;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: #f8fafc;
                font-weight: 700;
                padding: 8px 16px;
                min-height: 34px;
            }
            QPushButton#closeGuideBtn:hover {
                background-color: #334155;
            }
            QTextBrowser {
                background-color: #0b0f17;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                color: #cbd5e1;
            }
            QScrollBar:vertical {
                border: none;
                background: #0b0f17;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 24px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 1. Top Header Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        lbl_head = QLabel("📖 HƯỚNG DẪN SỬ DỤNG GẮN SẴN")
        lbl_head.setStyleSheet("font-size: 16px; font-weight: 800; color: #f8fafc;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm nhanh từ khóa (xiaomi, samsung, wifi, phím tắt, timeout...)...")
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.returnPressed.connect(self.on_search_next)

        btn_close = QPushButton("Đóng")
        btn_close.setObjectName("closeGuideBtn")
        btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        btn_close.clicked.connect(self.close)

        top_bar.addWidget(lbl_head)
        top_bar.addWidget(self.search_input, stretch=1)
        top_bar.addWidget(btn_close)
        layout.addLayout(top_bar)

        # 2. Main Content Splitter (Left Table of Contents, Right Browser)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left TOC List
        self.toc_list = QListWidget()
        self.toc_list.setFixedWidth(240)

        self.sections_map = [
            ("🚀 Bắt đầu & Chuẩn bị ADB", "sec_quickstart"),
            ("📱 Xiaomi / POCO / Redmi", "sec_xiaomi"),
            ("📱 Samsung Galaxy (One UI)", "sec_samsung"),
            ("📱 OPPO & Realme", "sec_oppo"),
            ("📱 Vivo & iQOO", "sec_vivo"),
            ("📱 Google Pixel & Khác", "sec_pixel"),
            ("📱 Huawei & Honor", "sec_huawei"),
            ("📶 Kết nối Không Dây Wi-Fi", "sec_wifi"),
            ("🖥️ Chiếu Màn Hình & Phím Tắt", "sec_stream"),
            ("🛠️ Chi tiết toàn bộ tính năng", "sec_features"),
            ("❓ Khắc phục lỗi thường gặp", "sec_faq"),
        ]

        for title, anchor in self.sections_map:
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, anchor)
            self.toc_list.addItem(item)

        self.toc_list.currentRowChanged.connect(self.on_toc_selected)

        # Right Text Browser
        self.browser = QTextBrowser()
        self.browser.setHtml(GUIDE_HTML)
        self.browser.setOpenExternalLinks(False)
        self.browser.setOpenLinks(True)

        splitter.addWidget(self.toc_list)
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # Select first section by default
        self.toc_list.setCurrentRow(0)

    def on_toc_selected(self, row):
        if row < 0 or row >= len(self.sections_map):
            return
        _, anchor = self.sections_map[row]
        self.browser.scrollToAnchor(anchor)

    def on_search_changed(self, text):
        query = text.strip()
        if not query:
            return
        cursor = self.browser.textCursor()
        cursor.setPosition(0)
        self.browser.setTextCursor(cursor)
        self.browser.find(query)

    def on_search_next(self):
        query = self.search_input.text().strip()
        if query:
            if not self.browser.find(query):
                cursor = self.browser.textCursor()
                cursor.setPosition(0)
                self.browser.setTextCursor(cursor)
                self.browser.find(query)
