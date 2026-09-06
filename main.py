# -*- coding: utf-8 -*-
"""
================================================================================
  DROIDMASTER PRO // 2026 NEXT-GEN DESIGN
  Ultra-Modern, Spacious, Beautiful Android Control Center & 60FPS Mirror Hub
================================================================================
"""

import os
import sys
import time
import subprocess
import threading
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QCheckBox,
    QLineEdit, QTextEdit, QFrame, QFileDialog, QMessageBox,
    QScrollArea, QSizePolicy
)
from PySide6.QtGui import QFont, QCursor, QIcon

import adb_core
from styles import DARK_THEME_QSS

class AsyncWorker(QThread):
    finished = Signal(bool, object)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            res = self.fn(*self.args, **self.kwargs)
            if isinstance(res, tuple) and len(res) == 2:
                self.finished.emit(bool(res[0]), res[1])
            elif isinstance(res, bool):
                self.finished.emit(res, res)
            else:
                self.finished.emit(True, res)
        except Exception as e:
            self.finished.emit(False, str(e))

class PhantomBotWorker(QThread):
    sig_log = Signal(str)
    sig_finished = Signal(bool)

    def __init__(self, target_serial: str, log_callback=None):
        super().__init__()
        self.target_serial = target_serial
        self._is_cancelled = False
        self.runner = None
        if log_callback:
            self.sig_log.connect(log_callback)

    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def cancel(self):
        self._is_cancelled = True
        if self.runner:
            try:
                self.runner.cancel()
            except Exception:
                pass

    def run(self):
        try:
            import phantom_agent
            self.runner = phantom_agent.PhantomBotRunner()
            success = self.runner.run_workflow(
                serial=self.target_serial,
                log_callback=self.sig_log.emit,
                is_cancelled=self.is_cancelled
            )
            self.sig_finished.emit(bool(success))
        except Exception as e:
            self.sig_log.emit(f"❌ Lỗi thực thi Bot: {e}")
            self.sig_finished.emit(False)

class DroidMasterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DroidMaster Pro - Trung Tâm Điều Khiển Android")
        icon_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        if os.path.exists(icon_file):
            self.setWindowIcon(QIcon(icon_file))
        self.resize(1020, 740)
        self.setMinimumSize(780, 480)
        self.setStyleSheet(DARK_THEME_QSS)

        self.active_serial = None
        self.scrcpy_proc = None
        self.bot_worker = None
        self.btn_bot = None
        self.devices = []
        self.workers = []
        self.is_fetching_telemetry = False

        self.build_ui()
        self.reload_devices()

        # Telemetry auto-refresh every 6 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_poll_telemetry)
        self.timer.start(6000)

        # Scrcpy process monitor timer (every 1 second)
        self.scrcpy_monitor_timer = QTimer(self)
        self.scrcpy_monitor_timer.timeout.connect(self.monitor_scrcpy_process)
        self.scrcpy_monitor_timer.start(1000)

    def build_ui(self):
        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # =============================================================
        # LEFT COLUMN: SIDEBAR (DEVICE CARD & REMOTE CONTROLS)
        # =============================================================
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setObjectName("sidebarScroll")
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFrameShape(QFrame.NoFrame)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        sidebar_scroll.setMinimumWidth(260)
        sidebar_scroll.setMaximumWidth(340)

        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setMinimumWidth(260)
        sidebar.setMaximumWidth(340)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(18, 20, 18, 20)
        side_layout.setSpacing(16)

        # 1. App Branding
        brand_row = QHBoxLayout()
        lbl_logo = QLabel("⚡")
        lbl_logo.setStyleSheet("font-size: 22px;")
        lbl_brand = QLabel("DroidMaster Pro")
        lbl_brand.setObjectName("brandTitle")
        lbl_ver = QLabel("v2.8.0")
        lbl_ver.setObjectName("metricPill")

        brand_row.addWidget(lbl_logo)
        brand_row.addWidget(lbl_brand)
        brand_row.addWidget(lbl_ver)
        brand_row.addStretch()
        side_layout.addLayout(brand_row)

        # 2. Device Selector Dropdown
        dev_sel_box = QVBoxLayout()
        dev_sel_box.setSpacing(6)
        lbl_sel = QLabel("THIẾT BỊ ĐANG CHỌN")
        lbl_sel.setObjectName("metricLabel")

        dev_combo_row = QHBoxLayout()
        self.combo_devices = QComboBox()
        self.combo_devices.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_devices.currentIndexChanged.connect(self.on_device_selected)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setToolTip("Quét lại danh sách thiết bị")
        btn_refresh.setFixedWidth(40)
        btn_refresh.clicked.connect(self.reload_devices)

        dev_combo_row.addWidget(self.combo_devices)
        dev_combo_row.addWidget(btn_refresh)

        dev_sel_box.addWidget(lbl_sel)
        dev_sel_box.addLayout(dev_combo_row)
        side_layout.addLayout(dev_sel_box)

        # 3. Device Info Card (Bento Style)
        self.card_device = QFrame()
        self.card_device.setProperty("class", "bentoCard")
        card_dev_layout = QVBoxLayout(self.card_device)
        card_dev_layout.setContentsMargins(16, 16, 16, 16)
        card_dev_layout.setSpacing(12)

        # Device Header with status badge
        dev_header = QHBoxLayout()
        self.lbl_device_model = QLabel("Đang quét...")
        self.lbl_device_model.setObjectName("cardTitle")
        self.lbl_status_pill = QLabel("ONLINE")
        self.lbl_status_pill.setObjectName("statusPill")

        dev_header.addWidget(self.lbl_device_model)
        dev_header.addStretch()
        dev_header.addWidget(self.lbl_status_pill)
        card_dev_layout.addLayout(dev_header)

        # Specs Rows
        grid_specs = QGridLayout()
        grid_specs.setHorizontalSpacing(14)
        grid_specs.setVerticalSpacing(8)

        self.val_battery = QLabel("--")
        self.val_battery.setObjectName("metricValue")
        self.val_os = QLabel("--")
        self.val_os.setObjectName("metricValue")
        self.val_ip = QLabel("--")
        self.val_ip.setObjectName("metricValue")
        self.val_res = QLabel("--")
        self.val_res.setObjectName("metricValue")
        self.val_cpu = QLabel("--")
        self.val_cpu.setObjectName("metricValue")

        def add_spec(r, c, title, widget, col_span=None):
            lbl = QLabel(title)
            lbl.setObjectName("metricLabel")
            widget.setWordWrap(True)
            span = col_span if col_span is not None else (2 if (c == 0 and r >= 4) else 1)
            grid_specs.addWidget(lbl, r, c, 1, span)
            grid_specs.addWidget(widget, r + 1, c, 1, span)

        add_spec(0, 0, "Pin & Nhiệt Độ", self.val_battery)
        add_spec(0, 1, "Hệ Điều Hành", self.val_os)
        add_spec(2, 0, "Địa Chỉ Wi-Fi", self.val_ip)
        add_spec(2, 1, "Màn Hình", self.val_res)
        add_spec(4, 0, "CPU & Tải Máy", self.val_cpu)

        card_dev_layout.addLayout(grid_specs)
        side_layout.addWidget(self.card_device)

        # 4. Remote Navigation Bar (Dock Style)
        lbl_remote_title = QLabel("ĐIỀU KHIỂN ĐIỆN THOẠI")
        lbl_remote_title.setObjectName("metricLabel")
        side_layout.addWidget(lbl_remote_title)

        nav_dock = QFrame()
        nav_dock.setObjectName("navDock")
        nav_dock_layout = QHBoxLayout(nav_dock)
        nav_dock_layout.setContentsMargins(4, 4, 4, 4)
        nav_dock_layout.setSpacing(4)

        buttons_data = [
            ("◀", "Quay lại (Back)", lambda: self.send_key("4")),
            ("●", "Trang chính (Home)", lambda: self.send_key("3")),
            ("■", "Đa nhiệm (Recents)", lambda: self.send_key("187")),
            ("🔔", "Hạ thanh thông báo", self.action_pull_notifications),
            ("🔒", "Khóa / Mở nguồn (Power)", lambda: self.send_key("26")),
            ("🔉", "Giảm âm", lambda: self.send_key("25")),
            ("🔊", "Tăng âm", lambda: self.send_key("24")),
        ]

        for icon, tooltip, callback in buttons_data:
            btn = QPushButton(icon)
            btn.setProperty("class", "navBtn")
            btn.setToolTip(tooltip)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(callback)
            nav_dock_layout.addWidget(btn)

        side_layout.addWidget(nav_dock)

        # 5. Quick Text Injector Box
        text_inject_box = QVBoxLayout()
        text_inject_box.setSpacing(6)
        lbl_txt = QLabel("BẮN VĂN BẢN VÀO ĐIỆN THOẠI")
        lbl_txt.setObjectName("metricLabel")

        txt_row = QHBoxLayout()
        self.txt_inject = QLineEdit()
        self.txt_inject.setPlaceholderText("Nhập văn bản rồi nhấn Enter...")
        self.txt_inject.returnPressed.connect(self.action_send_text)

        btn_send = QPushButton("Gửi ↵")
        btn_send.setCursor(QCursor(Qt.PointingHandCursor))
        btn_send.clicked.connect(self.action_send_text)

        txt_row.addWidget(self.txt_inject)
        txt_row.addWidget(btn_send)

        text_inject_box.addWidget(lbl_txt)
        text_inject_box.addLayout(txt_row)
        side_layout.addLayout(text_inject_box)

        side_layout.addStretch()

        # Footer Link
        lbl_hint = QLabel("💡 Mẹo: Dùng chuột click vào màn hình stream để thao tác trực tiếp.")
        lbl_hint.setStyleSheet("font-size: 11px; color: #475569; line-height: 1.4;")
        lbl_hint.setWordWrap(True)
        side_layout.addWidget(lbl_hint)

        sidebar_scroll.setWidget(sidebar)
        root_layout.addWidget(sidebar_scroll)

        # =============================================================
        # RIGHT COLUMN: MAIN CANVAS (HERO STREAM + BENTO TILES)
        # =============================================================
        main_content = QWidget()
        content_layout = QVBoxLayout(main_content)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.setSpacing(20)

        # -------------------------------------------------------------
        # HERO SECTION: SCRCPY 60FPS SCREEN MIRRORING
        # -------------------------------------------------------------
        hero_card = QFrame()
        hero_card.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(22, 20, 22, 20)
        hero_layout.setSpacing(16)

        # Top row: Title + Live Status Badge
        hero_top = QHBoxLayout()
        hero_title_box = QVBoxLayout()
        hero_title_box.setSpacing(4)

        lbl_hero_head = QLabel("🖥️ Chiếu Màn Hình Thời Gian Thực (Scrcpy Pro)")
        lbl_hero_head.setStyleSheet("font-size: 17px; font-weight: 800; color: #f8fafc;")
        lbl_hero_sub = QLabel("Chuẩn 60 FPS • Độ trễ thấp 35-70ms • GPU giải mã phần cứng siêu nhẹ (< 1% CPU)")
        lbl_hero_sub.setStyleSheet("font-size: 12px; color: #94a3b8;")

        hero_title_box.addWidget(lbl_hero_head)
        hero_title_box.addWidget(lbl_hero_sub)
        hero_top.addLayout(hero_title_box)
        hero_top.addStretch()

        self.btn_hero_stream = QPushButton("▶ BẬT CHIẾU MÀN HÌNH")
        self.btn_hero_stream.setObjectName("primaryHeroBtn")
        self.btn_hero_stream.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_hero_stream.clicked.connect(self.action_toggle_stream)
        hero_top.addWidget(self.btn_hero_stream)

        hero_layout.addLayout(hero_top)

        # Bottom row: Pro Toggles & Quality
        toggles_row = QHBoxLayout()
        toggles_row.setSpacing(18)

        self.chk_turn_off = QCheckBox("Tắt màn hình điện thoại (Chống nóng máy)")
        self.chk_always_top = QCheckBox("Luôn ghim trên cùng (Always on Top)")
        self.chk_always_top.setChecked(True)
        self.chk_stay_awake = QCheckBox("Không khóa màn hình")
        self.chk_stay_awake.setChecked(True)

        toggles_row.addWidget(self.chk_turn_off)
        toggles_row.addWidget(self.chk_always_top)
        toggles_row.addWidget(self.chk_stay_awake)
        toggles_row.addStretch()

        # Quality Combo
        lbl_q = QLabel("Chất lượng:")
        lbl_q.setStyleSheet("color: #64748b; font-size: 12px;")
        self.combo_quality = QComboBox()
        self.combo_quality.addItems(["Chuẩn (1080p - 8Mbps)", "Siêu nhẹ (720p - 4Mbps)", "Gốc (Full HD+ - 16Mbps)"])

        toggles_row.addWidget(lbl_q)
        toggles_row.addWidget(self.combo_quality)

        hero_layout.addLayout(toggles_row)
        content_layout.addWidget(hero_card)

        # -------------------------------------------------------------
        # BENTO GRID: 4 ACTION TILES
        # -------------------------------------------------------------
        lbl_bento_head = QLabel("TÁC VỤ & CÔNG CỤ NHANH")
        lbl_bento_head.setObjectName("metricLabel")
        content_layout.addWidget(lbl_bento_head)

        bento_grid = QGridLayout()
        bento_grid.setHorizontalSpacing(16)
        bento_grid.setVerticalSpacing(16)

        def create_bento_tile(icon, title, desc, btn_text, callback, accent_color="#38bdf8"):
            tile = QFrame()
            tile.setProperty("class", "bentoCard")
            tile.setMinimumHeight(130)
            t_layout = QVBoxLayout(tile)
            t_layout.setContentsMargins(18, 16, 18, 16)
            t_layout.setSpacing(8)

            head_h = QHBoxLayout()
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"font-size: 22px; color: {accent_color};")
            t_title = QLabel(title)
            t_title.setObjectName("cardTitle")
            t_title.setWordWrap(True)
            head_h.addWidget(icon_lbl)
            head_h.addWidget(t_title)
            head_h.addStretch()

            t_desc = QLabel(desc)
            t_desc.setObjectName("cardDesc")
            t_desc.setWordWrap(True)

            action_btn = QPushButton(btn_text)
            action_btn.setMinimumHeight(38)
            action_btn.setCursor(QCursor(Qt.PointingHandCursor))
            action_btn.clicked.connect(callback)

            t_layout.addLayout(head_h)
            t_layout.addWidget(t_desc)
            t_layout.addSpacing(4)
            t_layout.addWidget(action_btn)
            return tile, action_btn

        tile_snap, _ = create_bento_tile(
            "📸", "Chụp Màn Hình",
            "Chụp và lưu ảnh HD thẳng vào Pictures/DroidMaster trên PC.",
            "Chụp ảnh ngay", self.action_take_screenshot, "#38bdf8"
        )

        tile_apk, _ = create_bento_tile(
            "📦", "Cài Đặt APK",
            "Chọn file .apk bất kỳ trên máy tính để cài đặt tự động vào máy.",
            "Chọn file APK...", self.action_install_apk, "#10b981"
        )

        tile_wifi, _ = create_bento_tile(
            "📶", "Không Dây Wi-Fi",
            "Kích hoạt kết nối qua Wi-Fi (cổng 5555) để rút dây cáp USB.",
            "Bật kết nối Wi-Fi", self.action_connect_wifi, "#f59e0b"
        )

        tile_bot, self.btn_bot = create_bento_tile(
            "🤖", "Bot Phantom Scroll",
            "Tự động mở Facebook, tin tức Tinhte và Nekogram lướt trong 60s.",
            "Kích hoạt Bot (60s)", self.action_run_bot, "#8b5cf6"
        )

        bento_grid.addWidget(tile_snap, 0, 0)
        bento_grid.addWidget(tile_apk, 0, 1)
        bento_grid.addWidget(tile_wifi, 1, 0)
        bento_grid.addWidget(tile_bot, 1, 1)

        content_layout.addLayout(bento_grid)

        # -------------------------------------------------------------
        # QUICK APP LAUNCHER STRIP
        # -------------------------------------------------------------
        app_strip_box = QHBoxLayout()
        app_strip_box.setSpacing(10)

        lbl_apps = QLabel("MỞ NHANH:")
        lbl_apps.setObjectName("metricLabel")
        app_strip_box.addWidget(lbl_apps)

        quick_apps = [
            ("▶ YouTube", "com.google.android.youtube"),
            ("🌐 Chrome", "com.android.chrome"),
            ("📘 Facebook", "com.facebook.katana"),
            ("✈️ Nekogram", "tw.nekomimi.nekogram"),
            ("⚙️ Cài đặt", "com.android.settings"),
            ("📷 Camera", "com.android.camera")
        ]

        for name, pkg in quick_apps:
            btn_app = QPushButton(name)
            btn_app.setProperty("class", "appIconBtn")
            btn_app.setCursor(QCursor(Qt.PointingHandCursor))
            btn_app.clicked.connect(lambda _, p=pkg: self.action_launch_app(p))
            app_strip_box.addWidget(btn_app)

        app_strip_box.addStretch()
        content_layout.addLayout(app_strip_box)

        # -------------------------------------------------------------
        # TERMINAL / LOG CONSOLE (macOS Style)
        # -------------------------------------------------------------
        term_frame = QFrame()
        term_layout = QVBoxLayout(term_frame)
        term_layout.setContentsMargins(0, 0, 0, 0)
        term_layout.setSpacing(0)

        term_head = QFrame()
        term_head.setObjectName("terminalHeader")
        th_layout = QHBoxLayout(term_head)
        th_layout.setContentsMargins(12, 6, 12, 6)

        dots = QLabel("🔴  🟡  🟢")
        dots.setStyleSheet("font-size: 10px;")
        t_label = QLabel("Console Log & Shell Output")
        t_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; margin-left: 8px;")

        th_layout.addWidget(dots)
        th_layout.addWidget(t_label)
        th_layout.addStretch()

        self.txt_log = QTextEdit()
        self.txt_log.setObjectName("terminalOutput")
        self.txt_log.setReadOnly(True)
        self.txt_log.setFixedHeight(105)

        term_layout.addWidget(term_head)
        term_layout.addWidget(self.txt_log)
        content_layout.addWidget(term_frame)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(main_content)

        root_layout.addWidget(scroll, 1)

        self.setCentralWidget(central)
        self.log("🚀 DroidMaster Pro v2.7.0 sẵn sàng.")

    # =================================================================
    # CONTROLLER ACTIONS & LOGIC
    # =================================================================
    def log(self, text):
        t_str = time.strftime("%H:%M:%S")
        self.txt_log.append(f"[{t_str}] {text}")

    def reload_devices(self):
        self.combo_devices.blockSignals(True)
        self.combo_devices.clear()

        self.devices = adb_core.list_devices()
        if not self.devices:
            self.combo_devices.addItem("Không tìm thấy thiết bị")
            self.active_serial = None
            self.lbl_device_model.setText("Chưa cắm máy")
            self.lbl_status_pill.setText("OFFLINE")
            self.lbl_status_pill.setObjectName("statusPillOffline")
            self.clear_specs()
        else:
            for dev in self.devices:
                self.combo_devices.addItem(f"{dev['model']} ({dev['type']})", dev["serial"])

            self.active_serial = self.devices[0]["serial"]
            self.lbl_device_model.setText(self.devices[0]["model"])
            self.lbl_status_pill.setText("ONLINE")
            self.lbl_status_pill.setObjectName("statusPill")
            self.fetch_telemetry(self.active_serial)

        self.combo_devices.blockSignals(False)

    def on_device_selected(self, idx):
        if idx >= 0 and self.devices:
            self.active_serial = self.combo_devices.currentData()
            self.lbl_device_model.setText(self.devices[idx]["model"])
            self.fetch_telemetry(self.active_serial)

    def run_async(self, fn, callback, *args, **kwargs):
        worker = AsyncWorker(fn, *args, **kwargs)
        self.workers.append(worker)
        def on_finished(ok: bool, res: object):
            if worker in self.workers:
                self.workers.remove(worker)
            try:
                callback(ok, res)
            except Exception as e:
                self.log(f"⚠️ Lỗi xử lý callback: {e}")
        worker.finished.connect(on_finished)
        worker.start()

    def fetch_telemetry(self, target_serial: str = None):
        target = target_serial or self.active_serial
        if not target:
            return
        if self.is_fetching_telemetry and target == getattr(self, "_current_fetching_serial", None):
            return

        self.is_fetching_telemetry = True
        self._current_fetching_serial = target

        def task():
            return adb_core.get_device_info(target)

        self.run_async(task, lambda ok, res: self._render_telemetry(ok, res, target))

    def _render_telemetry(self, ok: bool, res_data: object, target_serial: str = None):
        self.is_fetching_telemetry = False
        if target_serial != self.active_serial:
            return
        if not ok or not self.active_serial:
            return
        info = res_data if isinstance(res_data, dict) else {}
        if not info:
            return

        self.lbl_device_model.setText(str(info.get("model", "Android")))
        battery_lvl = info.get("battery_level", "--")
        battery_temp = info.get("battery_temp", "--")
        self.val_battery.setText(f"{battery_lvl} ({battery_temp})")
        self.val_os.setText(str(info.get("android_version", "--")))
        self.val_ip.setText(str(info.get("ip", "--")))
        self.val_res.setText(str(info.get("resolution", "--")))
        cpu_val = info.get("cpu", info.get("cpu_load", "--"))
        self.val_cpu.setText(str(cpu_val))

    def auto_poll_telemetry(self):
        if self.active_serial and not self.is_fetching_telemetry:
            self.fetch_telemetry(self.active_serial)

    def clear_specs(self):
        self.val_battery.setText("--")
        self.val_os.setText("--")
        self.val_ip.setText("--")
        self.val_res.setText("--")
        self.val_cpu.setText("--")

    def action_toggle_stream(self):
        if not self.active_serial:
            QMessageBox.warning(self, "Chú ý", "Vui lòng kết nối một điện thoại Android trước!")
            return

        if self.scrcpy_proc and self.scrcpy_proc.poll() is None:
            self.scrcpy_proc.terminate()
            self.scrcpy_proc = None
            self.btn_hero_stream.setText("▶ BẬT CHIẾU MÀN HÌNH")
            self.btn_hero_stream.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669); color: #ffffff;")
            self.log("⏹️ Đã tắt cửa sổ chiếu màn hình.")
        else:
            q_idx = self.combo_quality.currentIndex()
            res_val = 1080 if q_idx == 0 else (720 if q_idx == 1 else 0)
            bit_val = "8M" if q_idx == 0 else ("4M" if q_idx == 1 else "16M")

            opts = {
                "turn_screen_off": self.chk_turn_off.isChecked(),
                "always_on_top": self.chk_always_top.isChecked(),
                "stay_awake": self.chk_stay_awake.isChecked(),
                "max_size": res_val,
                "bitrate": bit_val,
                "title": f"DroidMaster // {self.lbl_device_model.text()}"
            }

            self.scrcpy_proc = adb_core.launch_scrcpy(self.active_serial, opts)
            if self.scrcpy_proc:
                self.btn_hero_stream.setText("■ DỪNG CHIẾU MÀN HÌNH")
                self.btn_hero_stream.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #dc2626); color: #ffffff;")
                self.log(f"🟢 Đã bật chiếu màn hình 60FPS cho {self.lbl_device_model.text()}.")
            else:
                QMessageBox.critical(self, "Lỗi", "Không thể bật Scrcpy. Hãy kiểm tra kết nối cáp USB!")

    def monitor_scrcpy_process(self):
        if self.scrcpy_proc != None and self.scrcpy_proc.poll() is not None:
            self.scrcpy_proc = None
            self.btn_hero_stream.setText("▶ BẬT CHIẾU MÀN HÌNH")
            self.btn_hero_stream.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669); color: #ffffff;")
            self.log("⏹️ Cửa sổ chiếu màn hình Scrcpy đã đóng.")

    def send_key(self, code):
        if not self.active_serial:
            return
        threading.Thread(target=adb_core.send_keyevent, args=(self.active_serial, code), daemon=True).start()

    def action_pull_notifications(self):
        if not self.active_serial:
            return
        threading.Thread(
            target=adb_core.run_adb_raw,
            args=(["shell", "cmd", "statusbar", "expand-notifications"],),
            kwargs={"serial": self.active_serial},
            daemon=True
        ).start()

    def action_send_text(self):
        if not self.active_serial:
            return
        text = self.txt_inject.text().strip()
        if not text:
            return
        threading.Thread(target=adb_core.send_text, args=(self.active_serial, text), daemon=True).start()
        self.log(f"⌨️ Đã gửi văn bản: \"{text}\"")
        self.txt_inject.clear()

    def action_launch_app(self, pkg):
        if not self.active_serial:
            return
        threading.Thread(
            target=adb_core.run_adb_raw,
            args=(["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"],),
            kwargs={"serial": self.active_serial},
            daemon=True
        ).start()
        self.log(f"📱 Khởi chạy ứng dụng: {pkg}")

    def action_take_screenshot(self):
        if not self.active_serial:
            return
        pic_dir = os.path.join(os.path.expanduser("~"), "Pictures", "DroidMaster")
        os.makedirs(pic_dir, exist_ok=True)
        filename = f"snap_{time.strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(pic_dir, filename)

        def task():
            return adb_core.take_screenshot(self.active_serial, filepath)

        def on_done(ok: bool, res: object):
            if ok and res:
                self.log(f"📸 Đã lưu ảnh chụp: {filepath}")
                try:
                    if hasattr(os, "startfile"):
                        os.startfile(filepath)
                    else:
                        subprocess.Popen(["xdg-open", filepath])
                except Exception:
                    pass
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể chụp ảnh màn hình!")

        self.run_async(task, on_done)

    def action_install_apk(self):
        if not self.active_serial:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file APK để cài đặt", "", "Android Package (*.apk)")
        if not path:
            return

        self.log(f"📦 Đang cài đặt {os.path.basename(path)}...")

        def task():
            return adb_core.install_apk(self.active_serial, path)

        def on_done(ok: bool, msg: object):
            msg_str = str(msg)
            if ok:
                QMessageBox.information(self, "Thành công", f"Đã cài đặt thành công:\n{os.path.basename(path)}")
                self.log(f"✅ {msg_str}")
            else:
                QMessageBox.critical(self, "Lỗi cài đặt", msg_str)
                self.log(f"❌ {msg_str}")

        self.run_async(task, on_done)

    def action_connect_wifi(self):
        if not self.active_serial:
            return
        ip = self.val_ip.text()
        if not ip or ip == "--":
            QMessageBox.warning(self, "Chưa có IP", "Chưa phát hiện địa chỉ IP Wi-Fi của máy!")
            return

        self.log(f"📶 Đang chuyển đổi sang kết nối Wi-Fi ({ip}:5555)...")

        def task():
            return adb_core.switch_to_wifi(self.active_serial, ip, 5555)

        def on_done(ok: bool, msg: object):
            msg_str = str(msg)
            if ok:
                QMessageBox.information(
                    self, "Thành công",
                    f"Đã kết nối không dây tới {ip}:5555!\nBây giờ anh có thể RÚT DÂY CÁP USB ra mà vẫn điều khiển bình thường."
                )
                self.reload_devices()
            else:
                QMessageBox.warning(self, "Lỗi kết nối", msg_str)

        self.run_async(task, on_done)

    def action_run_bot(self):
        # Emergency stop toggle
        if self.bot_worker is not None and self.bot_worker.isRunning():
            self.log("⚠️ Yêu cầu DỪNG KHẨN CẤP Bot Phantom Scroll...")
            if hasattr(self, 'btn_bot') and self.btn_bot:
                self.btn_bot.setEnabled(False)
                self.btn_bot.setText("Đang dừng...")
            self.bot_worker.cancel()
            return

        if not self.active_serial:
            QMessageBox.warning(self, "Chú ý", "Vui lòng kết nối một điện thoại Android trước khi chạy Bot!")
            return

        if hasattr(self, 'btn_bot') and self.btn_bot:
            self.btn_bot.setText("⏹ DỪNG BOT KHẨN CẤP")
            self.btn_bot.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #dc2626); "
                "color: #ffffff; font-weight: bold; border: 1px solid #f87171;"
            )

        self.bot_worker = PhantomBotWorker(self.active_serial, log_callback=self.log)
        self.bot_worker.sig_finished.connect(self.on_bot_finished)
        self.bot_worker.start()
        self.log(f"🤖 Đã kích hoạt Bot Phantom Scroll (60s) trên thiết bị [{self.active_serial}].")

    def on_bot_finished(self, success: bool):
        if hasattr(self, 'btn_bot') and self.btn_bot:
            self.btn_bot.setEnabled(True)
            self.btn_bot.setText("Kích hoạt Bot (60s)")
            self.btn_bot.setStyleSheet("")
        if success:
            self.log("🤖 Bot Phantom Scroll đã hoàn thành chu trình 60s thành công.")
        else:
            self.log("⏹️ Bot Phantom Scroll đã dừng hoặc kết thúc.")
        self.bot_worker = None

    def closeEvent(self, event):
        # 1. Cancel and terminate bot worker
        if self.bot_worker is not None and self.bot_worker.isRunning():
            try:
                self.bot_worker.cancel()
                self.bot_worker.quit()
                if not self.bot_worker.wait(1000):
                    self.bot_worker.terminate()
                    self.bot_worker.wait(500)
            except Exception:
                pass
            self.bot_worker = None

        # 2. Terminate / kill scrcpy process
        if self.scrcpy_proc is not None:
            try:
                if self.scrcpy_proc.poll() is None:
                    self.scrcpy_proc.terminate()
                    try:
                        self.scrcpy_proc.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        self.scrcpy_proc.kill()
            except Exception:
                pass
            self.scrcpy_proc = None

        # 3. Stop all QTimers
        try:
            if hasattr(self, 'timer') and self.timer.isActive():
                self.timer.stop()
        except Exception:
            pass
        try:
            if hasattr(self, 'scrcpy_monitor_timer') and self.scrcpy_monitor_timer.isActive():
                self.scrcpy_monitor_timer.stop()
        except Exception:
            pass

        # 4. Cleanup background workers
        for worker in list(self.workers):
            try:
                if worker.isRunning():
                    worker.quit()
                    worker.wait(500)
            except Exception:
                pass
        self.workers.clear()

        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DroidMasterApp()
    window.show()
    sys.exit(app.exec())
