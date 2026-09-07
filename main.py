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
from typing import Optional, List, Dict, Any, Tuple
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize, QEvent, QObject, QRunnable, QThreadPool
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QCheckBox,
    QLineEdit, QTextEdit, QFrame, QFileDialog, QMessageBox,
    QScrollArea, QSizePolicy, QInputDialog
)
from PySide6.QtGui import QFont, QCursor, QIcon

import adb_core
from styles import DARK_THEME_QSS
from guide_dialog import UserGuideDialog
from device_manager import DeviceProfile, device_manager
from profile_dialog import ProfileDialog
from connection_dialogs import ConnectingProgressDialog, TailscaleOnboardingDialog, should_show_tailscale_hint

# Global unhandled exception hook to prevent Qt6 qFatal aborts (0xc0000409)
def global_excepthook(exctype, value, tb):
    import traceback
    sys.stderr.write("".join(traceback.format_exception(exctype, value, tb)))

sys.excepthook = global_excepthook

class WorkerSignals(QObject):
    finished = Signal(bool, object)

class AsyncWorker(QRunnable):
    """ThreadPool worker that avoids QThread deletion race conditions."""
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    def run(self):
        try:
            res = self.fn(*self.args, **self.kwargs)
            if isinstance(res, tuple) and len(res) == 2:
                self.signals.finished.emit(bool(res[0]), res[1])
            elif isinstance(res, bool):
                self.signals.finished.emit(res, res)
            else:
                self.signals.finished.emit(True, res)
        except Exception as e:
            self.signals.finished.emit(False, str(e))

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
        self.resize(960, 620)
        self.setMinimumSize(680, 460)
        self.setStyleSheet(DARK_THEME_QSS)

        self.active_serial = None
        self.active_profile = None
        self.is_stream_manually_stopped = False
        self.reconnect_attempts = 0
        self.scrcpy_proc = None
        self.bot_worker = None
        self.btn_bot = None
        self.devices = []
        self.workers = []
        self.is_fetching_telemetry = False

        self.build_ui()
        self.reload_profiles()
        self.reload_devices()

        # Telemetry auto-refresh every 6 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_poll_telemetry)
        self.timer.start(6000)

        # Scrcpy process monitor timer (every 1 second)
        self.scrcpy_monitor_timer = QTimer(self)
        self.scrcpy_monitor_timer.timeout.connect(self.monitor_scrcpy_process)
        self.scrcpy_monitor_timer.start(1000)

        # Connect application quit to cleanup
        app_inst = QApplication.instance()
        if app_inst:
            app_inst.aboutToQuit.connect(self.cleanup_all)

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
        sidebar_scroll.setMinimumWidth(250)
        sidebar_scroll.setMaximumWidth(310)

        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setMinimumWidth(250)
        sidebar.setMaximumWidth(310)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 16, 14, 16)
        side_layout.setSpacing(14)

        # 1. App Branding
        brand_row = QHBoxLayout()
        lbl_logo = QLabel("⚡")
        lbl_logo.setStyleSheet("font-size: 22px;")
        lbl_brand = QLabel("DroidMaster Pro")
        lbl_brand.setObjectName("brandTitle")
        lbl_ver = QLabel("v2.9.2")
        lbl_ver.setObjectName("metricPill")

        brand_row.addWidget(lbl_logo)
        brand_row.addWidget(lbl_brand)
        brand_row.addWidget(lbl_ver)
        brand_row.addStretch()
        side_layout.addLayout(brand_row)

        btn_guide = QPushButton("📖 HƯỚNG DẪN SỬ DỤNG")
        btn_guide.setObjectName("btnUserGuide")
        btn_guide.setCursor(QCursor(Qt.PointingHandCursor))
        btn_guide.setToolTip("Mở cẩm nang hướng dẫn bật ADB theo từng dòng máy và sử dụng toàn bộ tính năng")
        btn_guide.clicked.connect(self.open_user_guide)
        side_layout.addWidget(btn_guide)

        # 1.5. Smart Device Profiles (Danh bạ thiết bị thông minh)
        prof_box = QVBoxLayout()
        prof_box.setSpacing(6)
        lbl_prof = QLabel("DANH BẠ MÁY (PROFILES)")
        lbl_prof.setObjectName("metricLabel")

        prof_row = QHBoxLayout()
        self.combo_profiles = QComboBox()
        self.combo_profiles.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_profiles.currentIndexChanged.connect(self.on_profile_selected)

        self.btn_manage_profiles = QPushButton("⚙️")
        self.btn_manage_profiles.setToolTip("Quản lý danh bạ thiết bị (IP Tailscale / LAN / Cấu hình riêng)")
        self.btn_manage_profiles.setFixedWidth(36)
        self.btn_manage_profiles.clicked.connect(self.open_profile_manager)

        prof_row.addWidget(self.combo_profiles)
        prof_row.addWidget(self.btn_manage_profiles)

        self.btn_one_click_connect = QPushButton("⚡ KẾT NỐI NHANH (1-CLICK)")
        self.btn_one_click_connect.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_one_click_connect.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #1d4ed8);
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                border-radius: 8px;
                padding: 7px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #2563eb);
            }
        """)
        self.btn_one_click_connect.clicked.connect(self.action_one_click_connect)

        prof_box.addWidget(lbl_prof)
        prof_box.addLayout(prof_row)
        prof_box.addWidget(self.btn_one_click_connect)
        side_layout.addLayout(prof_box)

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
            ("💡", "Bật sáng màn hình máy (Wake Up)", self.action_wake_screen),
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
        self.main_content = QWidget()
        content_layout = QVBoxLayout(self.main_content)
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(14)

        # -------------------------------------------------------------
        # HERO SECTION: SCRCPY 60FPS SCREEN MIRRORING
        # -------------------------------------------------------------
        hero_card = QFrame()
        hero_card.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(14, 12, 14, 12)
        hero_layout.setSpacing(10)

        # 1. Header Title Block
        hero_title_box = QVBoxLayout()
        hero_title_box.setSpacing(3)

        lbl_hero_head = QLabel("🖥️ Chiếu Màn Hình Thời Gian Thực (Scrcpy Pro)")
        lbl_hero_head.setStyleSheet("font-size: 15px; font-weight: 800; color: #f8fafc;")
        lbl_hero_head.setWordWrap(True)

        lbl_hero_sub = QLabel("Chuẩn 60 FPS • Độ trễ 35-70ms • GPU giải mã siêu nhẹ (< 1% CPU)")
        lbl_hero_sub.setStyleSheet("font-size: 11px; color: #94a3b8;")
        lbl_hero_sub.setWordWrap(True)

        hero_title_box.addWidget(lbl_hero_head)
        hero_title_box.addWidget(lbl_hero_sub)
        hero_layout.addLayout(hero_title_box)

        # 2. Hero Stream Action Button (Prominent Center Control Bar)
        self.btn_hero_stream = QPushButton("▶ BẬT CHIẾU MÀN HÌNH")
        self.btn_hero_stream.setObjectName("primaryHeroBtn")
        self.btn_hero_stream.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_hero_stream.setMinimumHeight(40)
        self.btn_hero_stream.setMinimumWidth(160)
        self.btn_hero_stream.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_hero_stream.clicked.connect(self.action_toggle_stream)
        hero_layout.addWidget(self.btn_hero_stream)

        # 3. Toggles Grid (Row 0: 2 checks, Row 1: 1 check)
        toggles_grid = QGridLayout()
        toggles_grid.setHorizontalSpacing(10)
        toggles_grid.setVerticalSpacing(6)

        self.chk_turn_off = QCheckBox("Tắt màn hình máy (Tiết kiệm pin)")
        self.chk_turn_off.setChecked(False)
        self.chk_turn_off.setToolTip(
            "Nếu BẬT: Màn hình điện thoại sẽ tắt đen để chống nóng máy (chỉ xem trên máy tính).\n"
            "Phím tắt: Alt+Shift+O trên màn hình chiếu để bật sáng lại màn hình điện thoại.\n"
            "Nếu TẮT: Cả màn hình điện thoại và máy tính sẽ cùng sáng song song thực tế."
        )
        self.chk_always_top = QCheckBox("Ghim trên cùng")
        self.chk_always_top.setToolTip("Luôn ghim cửa sổ trên cùng (Always on Top)")
        self.chk_always_top.setChecked(True)
        self.chk_stay_awake = QCheckBox("Giữ sáng máy")
        self.chk_stay_awake.setToolTip("Không khóa màn hình điện thoại (Stay awake)")
        self.chk_stay_awake.setChecked(True)

        toggles_grid.addWidget(self.chk_turn_off, 0, 0)
        toggles_grid.addWidget(self.chk_always_top, 0, 1)
        toggles_grid.addWidget(self.chk_stay_awake, 1, 0)
        hero_layout.addLayout(toggles_grid)

        # Screen Sync Tip Banner
        lbl_screen_tip = QLabel("💡 Mẹo: Muốn điện thoại và máy tính cùng sáng song song, hãy BỎ TÍCH 'Tắt màn hình máy'. Phím tắt: Alt+Shift+O để bật lại màn hình điện thoại bất kỳ lúc nào.")
        lbl_screen_tip.setStyleSheet("font-size: 11px; color: #38bdf8; line-height: 1.3;")
        lbl_screen_tip.setWordWrap(True)
        hero_layout.addWidget(lbl_screen_tip)

        # 4. Stream Quality Row (spans full card width cleanly)
        quality_box = QHBoxLayout()
        quality_box.setContentsMargins(0, 0, 0, 0)
        quality_box.setSpacing(6)
        lbl_q = QLabel("Độ nét:")
        lbl_q.setStyleSheet("color: #64748b; font-size: 11px;")
        self.combo_quality = QComboBox()
        self.combo_quality.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_quality.addItems(["1080p (Chuẩn)", "720p (Nhẹ)", "Gốc (Full HD+)"])
        quality_box.addWidget(lbl_q)
        quality_box.addWidget(self.combo_quality)
        hero_layout.addLayout(quality_box)

        content_layout.addWidget(hero_card)

        # -------------------------------------------------------------
        # BENTO GRID: 4 ACTION TILES (ADAPTIVE 1 OR 2 COLUMNS)
        # -------------------------------------------------------------
        lbl_bento_head = QLabel("TÁC VỤ & CÔNG CỤ NHANH")
        lbl_bento_head.setObjectName("metricLabel")
        content_layout.addWidget(lbl_bento_head)

        self.bento_grid = QGridLayout()
        self.bento_grid.setHorizontalSpacing(14)
        self.bento_grid.setVerticalSpacing(14)

        def create_bento_tile(icon, title, desc, btn_text, callback, accent_color="#38bdf8", extra_widget=None):
            tile = QFrame()
            tile.setProperty("class", "bentoCard")
            tile.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            tile.setMinimumHeight(115)
            t_layout = QVBoxLayout(tile)
            t_layout.setContentsMargins(12, 10, 12, 10)
            t_layout.setSpacing(5)

            head_h = QHBoxLayout()
            head_h.setSpacing(8)
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"font-size: 18px; color: {accent_color};")
            t_title = QLabel(title)
            t_title.setObjectName("cardTitle")
            t_title.setWordWrap(True)
            head_h.addWidget(icon_lbl)
            head_h.addWidget(t_title, 1)

            if extra_widget:
                head_h.addWidget(extra_widget)

            t_desc = QLabel(desc)
            t_desc.setObjectName("cardDesc")
            t_desc.setWordWrap(True)

            action_btn = QPushButton(btn_text)
            action_btn.setMinimumHeight(34)
            action_btn.setCursor(QCursor(Qt.PointingHandCursor))
            action_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            action_btn.clicked.connect(callback)

            t_layout.addLayout(head_h)
            t_layout.addWidget(t_desc)
            t_layout.addStretch()
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

        btn_change_ip_toggle = QPushButton("⚙️ Đổi IP")
        btn_change_ip_toggle.setObjectName("btnMiniToggle")
        btn_change_ip_toggle.setCursor(QCursor(Qt.PointingHandCursor))
        btn_change_ip_toggle.setToolTip("Đổi địa chỉ IP Wi-Fi mới hoặc nhập IP Tailscale (100.x.y.z)")
        btn_change_ip_toggle.clicked.connect(self.prompt_change_ip)

        tile_wifi, _ = create_bento_tile(
            "📶", "Không Dây Wi-Fi",
            "Kích hoạt kết nối qua Wi-Fi (cổng 5555) hoặc đổi IP Tailscale.",
            "Bật kết nối Wi-Fi", self.action_connect_wifi, "#f59e0b",
            extra_widget=btn_change_ip_toggle
        )

        tile_bot, self.btn_bot = create_bento_tile(
            "🤖", "Bot Phantom Scroll",
            "Tự động mở Facebook, tin tức Tinhte và Nekogram lướt trong 60s.",
            "Kích hoạt Bot (60s)", self.action_run_bot, "#8b5cf6"
        )

        self.bento_tiles = [tile_snap, tile_apk, tile_wifi, tile_bot]
        content_layout.addLayout(self.bento_grid)
        self.relayout_bento(500)

        # -------------------------------------------------------------
        # QUICK APP LAUNCHER: 2 ROWS X 3 COLUMNS GRID
        # -------------------------------------------------------------
        lbl_apps = QLabel("MỞ NHANH ỨNG DỤNG")
        lbl_apps.setObjectName("metricLabel")
        content_layout.addWidget(lbl_apps)

        app_grid = QGridLayout()
        app_grid.setHorizontalSpacing(10)
        app_grid.setVerticalSpacing(8)

        quick_apps = [
            ("▶ YouTube", "com.google.android.youtube"),
            ("🌐 Chrome", "com.android.chrome"),
            ("📘 Facebook", "com.facebook.katana"),
            ("✈️ Nekogram", "tw.nekomimi.nekogram"),
            ("⚙️ Cài đặt", "com.android.settings"),
            ("📷 Camera", "com.android.camera")
        ]

        for idx, (name, pkg) in enumerate(quick_apps):
            r = idx // 3
            c = idx % 3
            btn_app = QPushButton(name)
            btn_app.setProperty("class", "appIconBtn")
            btn_app.setCursor(QCursor(Qt.PointingHandCursor))
            btn_app.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn_app.clicked.connect(lambda _, p=pkg: self.action_launch_app(p))
            app_grid.addWidget(btn_app, r, c)

        content_layout.addLayout(app_grid)

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

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setWidget(self.main_content)
        self.scroll.viewport().installEventFilter(self)

        root_layout.addWidget(self.scroll, 1)

        self.setCentralWidget(central)
        self.log("🚀 DroidMaster Pro v2.8.7 sẵn sàng.")

    def eventFilter(self, watched, event):
        try:
            if hasattr(self, 'scroll') and watched == self.scroll.viewport():
                if event.type() == QEvent.Resize:
                    self.relayout_bento(self.scroll.viewport().width())
        except Exception:
            pass
        return super().eventFilter(watched, event)

    def relayout_bento(self, width: int = None):
        try:
            if not hasattr(self, 'bento_tiles') or not hasattr(self, 'bento_grid'):
                return
            if width is None or width <= 0:
                if hasattr(self, 'scroll') and self.scroll.viewport().width() > 0:
                    width = self.scroll.viewport().width()
                elif hasattr(self, 'main_content') and self.main_content.width() > 0:
                    width = self.main_content.width()
                else:
                    width = 500

            target_cols = 1 if width < 560 else 2
            if getattr(self, "_bento_cols", None) == target_cols:
                return
            self._bento_cols = target_cols

            for tile in self.bento_tiles:
                self.bento_grid.removeWidget(tile)

            if target_cols == 1:
                self.bento_grid.setColumnStretch(0, 1)
                self.bento_grid.setColumnStretch(1, 0)
                for idx, tile in enumerate(self.bento_tiles):
                    self.bento_grid.addWidget(tile, idx, 0)
                    tile.setVisible(True)
            else:
                self.bento_grid.setColumnStretch(0, 1)
                self.bento_grid.setColumnStretch(1, 1)
                self.bento_grid.addWidget(self.bento_tiles[0], 0, 0)
                self.bento_grid.addWidget(self.bento_tiles[1], 0, 1)
                self.bento_grid.addWidget(self.bento_tiles[2], 1, 0)
                self.bento_grid.addWidget(self.bento_tiles[3], 1, 1)
                for tile in self.bento_tiles:
                    tile.setVisible(True)
        except Exception:
            pass

    def resizeEvent(self, event):
        try:
            super().resizeEvent(event)
            if hasattr(self, 'scroll') and hasattr(self, 'bento_grid'):
                w = self.scroll.viewport().width()
                self.relayout_bento(w)
        except Exception:
            pass

    # =================================================================
    # CONTROLLER ACTIONS & LOGIC
    # =================================================================
    def log(self, text):
        t_str = time.strftime("%H:%M:%S")
        self.txt_log.append(f"[{t_str}] {text}")

    def reload_devices(self, preferred_serial: str = None):
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
            if not getattr(self, "_is_reconnecting_wifi", False):
                self.try_auto_reconnect_wifi()
        else:
            selected_idx = 0
            for idx, dev in enumerate(self.devices):
                icon = "📶" if dev.get("type") == "Wi-Fi" else "🔌"
                self.combo_devices.addItem(f"{icon} {dev['model']} ({dev['type']})", dev["serial"])
                if preferred_serial and dev["serial"] == preferred_serial:
                    selected_idx = idx
                elif not preferred_serial and self.active_serial and dev["serial"] == self.active_serial:
                    selected_idx = idx
                if dev.get("type") == "Wi-Fi" or ":" in dev.get("serial", ""):
                    adb_core.save_config("last_wifi_endpoint", dev["serial"])

            self.combo_devices.setCurrentIndex(selected_idx)
            self.active_serial = self.devices[selected_idx]["serial"]
            self.lbl_device_model.setText(self.devices[selected_idx]["model"])
            self.lbl_status_pill.setText("ONLINE")
            self.lbl_status_pill.setObjectName("statusPill")
            self.fetch_telemetry(self.active_serial)

        self.combo_devices.blockSignals(False)

    def try_auto_reconnect_wifi(self):
        last_wifi = adb_core.load_config().get("last_wifi_endpoint")
        if not last_wifi:
            return
        self._is_reconnecting_wifi = True
        self.log(f"📶 Đang tự động quét & kết nối lại thiết bị Wi-Fi ({last_wifi})...")

        def task():
            return adb_core.connect_endpoint(last_wifi, timeout=4)

        def on_done(ok, msg):
            self._is_reconnecting_wifi = False
            if ok:
                self.log(f"✅ {msg}")
                self.reload_devices(preferred_serial=last_wifi)
            else:
                self.log(f"ℹ️ Thiết bị Wi-Fi ({last_wifi}) chưa phản hồi.")

        self.run_async(task, on_done)

    def on_device_selected(self, idx):
        if idx >= 0 and self.devices:
            self.active_serial = self.combo_devices.currentData()
            self.lbl_device_model.setText(self.devices[idx]["model"])
            self.fetch_telemetry(self.active_serial)

    def run_async(self, fn, callback, *args, **kwargs):
        worker = AsyncWorker(fn, *args, **kwargs)
        def on_finished(ok: bool, res: object):
            try:
                callback(ok, res)
            except Exception as e:
                self.log(f"⚠️ Lỗi xử lý callback: {e}")
        worker.signals.finished.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

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
        try:
            if self.is_fetching_telemetry:
                return

            # Check for device plug / unplug events dynamically
            current_devs = adb_core.list_devices()
            current_serials = [d["serial"] for d in current_devs]

            # 1. Active device was disconnected
            if self.active_serial and self.active_serial not in current_serials:
                self.log(f"🔌 Thiết bị {self.active_serial} đã ngắt kết nối.")
                self.reload_devices()
                return

            # 2. A new device was connected while offline
            if not self.active_serial and current_devs:
                self.log("⚡ Phát hiện thiết bị Android kết nối.")
                self.reload_devices()
                return

            if self.active_serial:
                self.fetch_telemetry(self.active_serial)
        except Exception:
            pass

    def clear_specs(self):
        self.val_battery.setText("--")
        self.val_os.setText("--")
        self.val_ip.setText("--")
        self.val_res.setText("--")
        self.val_cpu.setText("--")

    # =============================================================
    # SMART PROFILES & 1-CLICK REMOTE ENGINE
    # =============================================================
    def reload_profiles(self, preferred_id=None):
        """Reload profile list from device_manager into combobox."""
        try:
            self.combo_profiles.blockSignals(True)
            self.combo_profiles.clear()
            profiles = device_manager.get_profiles()
            sel_idx = 0
            for idx, p in enumerate(profiles):
                display = f"{p.name}"
                self.combo_profiles.addItem(display, p.id)
                if preferred_id and p.id == preferred_id:
                    sel_idx = idx
            if self.combo_profiles.count() > 0:
                self.combo_profiles.setCurrentIndex(sel_idx)
            self.combo_profiles.blockSignals(False)
            if profiles:
                self.on_profile_selected(sel_idx)
        except Exception as e:
            self.log(f"⚠️ Lỗi nạp danh bạ thiết bị: {e}")

    def on_profile_selected(self, index=None):
        p_id = self.combo_profiles.currentData()
        if p_id:
            self.active_profile = device_manager.get_profile(p_id)

    def open_profile_manager(self):
        dlg = ProfileDialog(self)
        dlg.profiles_changed.connect(lambda: self.reload_profiles(preferred_id=self.active_profile.id if self.active_profile else None))
        dlg.exec()

    def action_one_click_connect(self):
        """1-Click Smart Connection: Resolves optimal route, connects ADB, and starts stream with animated progress dialog."""
        p_id = self.combo_profiles.currentData()
        profile = device_manager.get_profile(p_id) if p_id else None
        if not profile:
            self.log("⚠️ Vui lòng chọn hoặc tạo một hồ sơ thiết bị trước!")
            self.open_profile_manager()
            return

        self.active_profile = profile
        self.log(f"⚡ [1-CLICK] Bắt đầu kết nối nhanh cho '{profile.name}'...")

        # Create animated progress modal dialog
        dlg = ConnectingProgressDialog(self, profile=profile)
        dlg.open_profiles_requested.connect(self.open_profile_manager)

        def on_connection_succeeded(endpoint: str, route_type: str):
            self.log(f"✅ [1-CLICK] Đã kết nối thành công qua [{route_type}] -> {endpoint}")
            self.reload_devices(preferred_serial=endpoint)
            self.launch_stream_for_profile(profile, endpoint, route_type=route_type)

        dlg.connection_succeeded.connect(on_connection_succeeded)
        dlg.start_connection()
        dlg.exec()

    def launch_stream_for_profile(self, profile: DeviceProfile, endpoint: str, route_type: Optional[str] = None):
        """Launch Scrcpy stream with customized profile flags."""
        self.is_stream_manually_stopped = False
        self.reconnect_attempts = 0

        q_idx = self.combo_quality.currentIndex()
        res_val = 1080 if q_idx == 0 else (720 if q_idx == 1 else 0)
        bit_val = "8M" if q_idx == 0 else ("4M" if q_idx == 1 else "16M")

        opts = {
            "turn_screen_off": self.chk_turn_off.isChecked(),
            "always_on_top": self.chk_always_top.isChecked(),
            "stay_awake": self.chk_stay_awake.isChecked(),
            "max_size": res_val,
            "bitrate": bit_val,
            "title": f"DroidMaster // {profile.name}",
            "extra_args": profile.extra_scrcpy_flags,
            "no_audio": "--no-audio" in profile.extra_scrcpy_flags
        }

        # If previous stream is running, terminate it
        if self.scrcpy_proc and self.scrcpy_proc.poll() is None:
            self.scrcpy_proc.terminate()
            self.scrcpy_proc = None

        self.scrcpy_proc = adb_core.launch_scrcpy(endpoint, opts)
        if self.scrcpy_proc:
            self.btn_hero_stream.setText("■ DỪNG CHIẾU MÀN HÌNH")
            self.btn_hero_stream.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #dc2626); color: #ffffff;")
            self.log(f"🟢 [1-CLICK] Đã bật chiếu màn hình cho {profile.name} ({endpoint}).")

            if not opts.get("turn_screen_off", False):
                self.run_async(lambda: adb_core.send_keyevent(endpoint, "224"), lambda ok, res: None)

            # Check if USB connection and should show Tailscale remote onboarding hint
            if should_show_tailscale_hint(endpoint, profile):
                QTimer.singleShot(800, lambda: self.show_tailscale_onboarding_hint(endpoint, profile))
        else:
            self.log(f"⚠️ Không thể khởi chạy Scrcpy cho {endpoint}")

    def show_tailscale_onboarding_hint(self, endpoint: str, profile: Optional[DeviceProfile] = None):
        """Show smart onboarding dialog teaching the user to use Tailscale for wireless remote access."""
        dev_name = profile.name if profile else self.lbl_device_model.text()
        dlg = TailscaleOnboardingDialog(self, device_name=dev_name, device_serial=endpoint)
        dlg.open_profiles_requested.connect(self.open_profile_manager)
        dlg.exec()

    def action_toggle_stream(self):
        try:
            # Refresh and verify device presence before launching Scrcpy
            current_devs = adb_core.list_devices()
            current_serials = [d["serial"] for d in current_devs]

            if not self.active_serial or self.active_serial not in current_serials:
                if current_devs:
                    self.log("🔄 Đồng bộ lại danh sách thiết bị trước khi bật chiếu...")
                    self.reload_devices()
                else:
                    last_wifi = adb_core.load_config().get("last_wifi_endpoint")
                    if last_wifi:
                        self.log(f"📶 Đang thử kết nối nhanh tới thiết bị Wi-Fi ({last_wifi})...")
                        ok, msg = adb_core.connect_endpoint(last_wifi, timeout=4)
                        if ok:
                            self.log(f"✅ {msg}")
                            self.reload_devices(preferred_serial=last_wifi)
                            current_devs = adb_core.list_devices()
                            current_serials = [d["serial"] for d in current_devs]

                    if not self.active_serial or self.active_serial not in current_serials:
                        QMessageBox.warning(self, "Chú ý", "Không tìm thấy thiết bị Android nào đang kết nối! Vui lòng kiểm tra cáp USB hoặc Wi-Fi.")
                        return

            if not self.active_serial:
                QMessageBox.warning(self, "Chú ý", "Vui lòng kết nối một điện thoại Android trước!")
                return

            if self.scrcpy_proc and self.scrcpy_proc.poll() is None:
                self.is_stream_manually_stopped = True
                self.scrcpy_proc.terminate()
                self.scrcpy_proc = None
                self.btn_hero_stream.setText("▶ BẬT CHIẾU MÀN HÌNH")
                self.btn_hero_stream.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669); color: #ffffff;")
                self.log("⏹️ Đã tắt cửa sổ chiếu màn hình.")
                if self.active_serial:
                    target_ser = self.active_serial
                    self.run_async(lambda: adb_core.run_adb_raw(["shell", "svc", "power", "stayon", "false"], serial=target_ser), lambda ok, res: None)
            else:
                self.is_stream_manually_stopped = False
                self.reconnect_attempts = 0

                q_idx = self.combo_quality.currentIndex()
                res_val = 1080 if q_idx == 0 else (720 if q_idx == 1 else 0)
                bit_val = "8M" if q_idx == 0 else ("4M" if q_idx == 1 else "16M")

                prof = self.active_profile
                extra_args = prof.extra_scrcpy_flags if prof else []
                no_audio = "--no-audio" in extra_args if prof else False

                opts = {
                    "turn_screen_off": self.chk_turn_off.isChecked(),
                    "always_on_top": self.chk_always_top.isChecked(),
                    "stay_awake": self.chk_stay_awake.isChecked(),
                    "max_size": res_val,
                    "bitrate": bit_val,
                    "title": f"DroidMaster // {self.lbl_device_model.text()}",
                    "extra_args": extra_args,
                    "no_audio": no_audio
                }

                self.scrcpy_proc = adb_core.launch_scrcpy(self.active_serial, opts)
                if self.scrcpy_proc:
                    self.btn_hero_stream.setText("■ DỪNG CHIẾU MÀN HÌNH")
                    self.btn_hero_stream.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #dc2626); color: #ffffff;")
                    self.log(f"🟢 Đã bật chiếu màn hình cho {self.lbl_device_model.text()} ({self.active_serial}).")

                    # If user wants both screens on (turn_screen_off unchecked), ensure device screen is awake
                    target_ser = self.active_serial
                    if not opts.get("turn_screen_off", False):
                        def wake_task():
                            adb_core.send_keyevent(target_ser, "224")  # KEYCODE_WAKEUP
                            if opts.get("stay_awake", True):
                                adb_core.run_adb_raw(["shell", "svc", "power", "stayon", "true"], serial=target_ser)
                        self.run_async(wake_task, lambda ok, res: None)

                    # If USB cable connection and Tailscale hint not dismissed, display onboarding popup
                    if should_show_tailscale_hint(self.active_serial, self.active_profile):
                        QTimer.singleShot(800, lambda: self.show_tailscale_onboarding_hint(self.active_serial, self.active_profile))
                else:
                    QMessageBox.critical(self, "Lỗi", "Không thể bật Scrcpy. Hãy kiểm tra kết nối thiết bị!")
        except Exception as e:
            self.log(f"⚠️ Lỗi chuyển đổi màn hình chiếu: {e}")

    def monitor_scrcpy_process(self):
        try:
            if self.scrcpy_proc is not None and self.scrcpy_proc.poll() is not None:
                self.scrcpy_proc = None

                # 1. If manually stopped by user, cleanup gracefully
                if self.is_stream_manually_stopped:
                    self.btn_hero_stream.setText("▶ BẬT CHIẾU MÀN HÌNH")
                    self.btn_hero_stream.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669); color: #ffffff;")
                    self.log("⏹️ Cửa sổ chiếu màn hình Scrcpy đã đóng.")
                    if self.active_serial:
                        target_ser = self.active_serial
                        self.run_async(lambda: adb_core.run_adb_raw(["shell", "svc", "power", "stayon", "false"], serial=target_ser), lambda ok, res: None)
                    return

                # 2. Unexpected termination: Trigger Silent Auto-Reconnect
                prof = self.active_profile
                should_reconnect = prof.auto_reconnect if prof else True
                max_retries = prof.max_reconnect_attempts if prof else 3

                if should_reconnect and self.reconnect_attempts < max_retries and self.active_serial:
                    self.reconnect_attempts += 1
                    target_ser = self.active_serial
                    self.log(f"⚠️ Mất kết nối stream! Đang tự động kết nối lại (Lần {self.reconnect_attempts}/{max_retries})...")
                    self.btn_hero_stream.setText(f"🔄 ĐANG KẾT NỐI LẠI ({self.reconnect_attempts}/{max_retries})...")
                    self.btn_hero_stream.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f59e0b, stop:1 #d97706); color: #ffffff;")

                    def retry_task():
                        time.sleep(1.2)
                        if ":" in target_ser:
                            ok, _ = adb_core.connect_endpoint(target_ser, timeout=3)
                            return ok
                        return True

                    def on_retry_done(success, ok):
                        if ok:
                            self.log("🔄 Thiết bị đã phản hồi, đang khôi phục màn hình chiếu...")
                            if prof:
                                self.launch_stream_for_profile(prof, target_ser)
                            else:
                                self.action_toggle_stream()
                        else:
                            self.log(f"⚠️ Thử kết nối lại lần {self.reconnect_attempts} chưa thành công.")
                            if self.reconnect_attempts >= max_retries:
                                self.btn_hero_stream.setText("▶ BẬT CHIẾU MÀN HÌNH")
                                self.btn_hero_stream.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669); color: #ffffff;")
                                self.log("❌ Đã hết số lần thử lại tự động. Vui lòng kiểm tra Wi-Fi / Tailscale trên điện thoại.")

                    self.run_async(retry_task, on_retry_done)
                else:
                    self.btn_hero_stream.setText("▶ BẬT CHIẾU MÀN HÌNH")
                    self.btn_hero_stream.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669); color: #ffffff;")
                    self.log("⏹️ Cửa sổ chiếu màn hình Scrcpy đã đóng.")
                    if self.active_serial:
                        target_ser = self.active_serial
                        self.run_async(lambda: adb_core.run_adb_raw(["shell", "svc", "power", "stayon", "false"], serial=target_ser), lambda ok, res: None)
        except Exception as e:
            self.log(f"⚠️ Lỗi giám sát tiến trình: {e}")

    def action_wake_screen(self):
        if not self.active_serial:
            return
        target_ser = self.active_serial
        def task():
            adb_core.send_keyevent(target_ser, "224")  # KEYCODE_WAKEUP
            time.sleep(0.08)
            adb_core.send_keyevent(target_ser, "82")   # KEYCODE_MENU (unlock)
        threading.Thread(target=task, daemon=True).start()
        self.log("💡 Đã gửi tín hiệu đánh thức màn hình điện thoại (Wake Up).")

    def open_user_guide(self):
        if not hasattr(self, "_guide_dialog") or self._guide_dialog is None:
            self._guide_dialog = UserGuideDialog(self)
        self._guide_dialog.show()
        self._guide_dialog.raise_()
        self._guide_dialog.activateWindow()

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

    def prompt_change_ip(self):
        """Prompt user for a new Wi-Fi or Tailscale IP address and switch immediately."""
        last_endpoint = adb_core.load_config().get("last_wifi_endpoint", "")
        current_ip = ""
        if self.active_serial and ":" in self.active_serial:
            current_ip = self.active_serial.split(":")[0]
        elif last_endpoint:
            current_ip = last_endpoint.split(":")[0]
        else:
            current_ip = "192.168.0.106"

        ip_val, ok = QInputDialog.getText(
            self, "Đổi Địa Chỉ IP Wi-Fi / Tailscale",
            "Nhập địa chỉ IP mới của điện thoại:\n"
            "• Nếu đổi sang mạng Wi-Fi khác: Nhập IP Wi-Fi mới (ví dụ: 192.168.1.50)\n"
            "• Nếu dùng qua mạng ngoài (Tailscale): Nhập IP Tailscale (ví dụ: 100.96.200.10)\n\n"
            "Địa chỉ IP mới:",
            text=current_ip
        )
        if not ok or not ip_val.strip():
            return

        target_ip = ip_val.strip()
        endpoint_full = f"{target_ip}:5555" if ":" not in target_ip else target_ip

        self.log(f"📶 Đang chuyển đổi sang địa chỉ IP mới ({endpoint_full})...")

        old_serial = self.active_serial

        def task():
            # If previous active connection was Wi-Fi, disconnect it first
            if old_serial and ":" in old_serial and old_serial != endpoint_full:
                adb_core.disconnect_endpoint(old_serial)
            return adb_core.connect_endpoint(target_ip, timeout=5)

        def on_done(ok_conn, msg_conn):
            if ok_conn:
                self.log(f"✅ {msg_conn}")
                adb_core.save_config("last_wifi_endpoint", endpoint_full)
                self.reload_devices(preferred_serial=endpoint_full)
                QMessageBox.information(
                    self, "Đổi IP Thành Công",
                    f"🎉 {msg_conn}\n\n"
                    f"👉 Thiết bị đã được kết nối với địa chỉ mới: {endpoint_full}!\n"
                    f"Bây giờ anh có thể bấm 'BẬT CHIẾU MÀN HÌNH' để sử dụng."
                )
            else:
                self.log(f"❌ {msg_conn}")
                QMessageBox.warning(
                    self, "Không Thể Kết Nối Tới IP Mới",
                    f"Không thể kết nối Wi-Fi tới {endpoint_full}.\n\n"
                    f"• Chi tiết: {msg_conn}\n\n"
                    f"👉 Hướng dẫn kiểm tra:\n"
                    f"1. Nếu dùng Wi-Fi khác: Kiểm tra điện thoại và máy tính đã bắt chung mạng chưa.\n"
                    f"2. Nếu dùng Tailscale: Đảm bảo ứng dụng Tailscale trên điện thoại đang Connected (bật VPN).\n"
                    f"3. Nếu điện thoại vừa khởi động lại: Cần cắm cáp USB 1 lần để mở lại cổng 5555."
                )

        self.run_async(task, on_done)

    def action_connect_wifi(self):
        if not self.active_serial:
            self.prompt_change_ip()
            return

        if ":" in self.active_serial:
            reply = QMessageBox.question(
                self, "Đổi Địa Chỉ IP Wi-Fi",
                f"Thiết bị hiện đang kết nối qua Wi-Fi:\n👉 {self.active_serial}\n\n"
                "Anh có muốn đổi sang địa chỉ IP khác (mạng Wi-Fi mới hoặc IP Tailscale) không?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.prompt_change_ip()
            return

        # Check if this device already has an active Wi-Fi connection in devices list
        current_serials = [d["serial"] for d in self.devices]
        existing_wifi = None
        for dev in self.devices:
            s = dev.get("serial", "")
            if (dev.get("type") == "Wi-Fi" or ":" in s) and (s in current_serials):
                existing_wifi = s
                break

        if existing_wifi:
            self.log(f"📶 Thiết bị đã kết nối sẵn qua Wi-Fi ({existing_wifi}). Đang chuyển sang điều khiển không dây...")
            self.reload_devices(preferred_serial=existing_wifi)
            QMessageBox.information(
                self, "Kích Hoạt Wi-Fi Thành Công",
                f"🎉 Thiết bị đã kết nối sẵn qua Wi-Fi ({existing_wifi})!\n\n"
                f"👉 Ứng dụng đã tự động chuyển sang điều khiển qua Wi-Fi ({existing_wifi}).\n"
                f"Bây giờ anh có thể RÚT DÂY CÁP USB ra và bấm 'BẬT CHIẾU MÀN HÌNH'."
            )
            return

        ip = self.val_ip.text().strip()
        ip_param = ip if (ip and ip != "--" and ip != "Unknown") else None
        target_serial = self.active_serial
        target_label = f"({ip_param}:5555)" if ip_param else ""
        self.log(f"📶 Đang chuyển đổi sang kết nối Wi-Fi {target_label}...")

        def task():
            return adb_core.connect_wifi(target_serial, ip=ip_param, port=5555)

        def on_done(ok: bool, msg: object):
            msg_str = str(msg)
            if ok:
                self.log(f"✅ {msg_str}")
                # Auto-select the Wi-Fi serial endpoint in combo_devices
                devs = adb_core.list_devices()
                wifi_serial = None
                for d in devs:
                    if ":" in d.get("serial", ""):
                        wifi_serial = d["serial"]
                        break
                self.reload_devices(preferred_serial=wifi_serial)
                QMessageBox.information(
                    self, "Kích Hoạt Wi-Fi Thành Công",
                    f"🎉 {msg_str}\n\n"
                    f"👉 Bây giờ anh có thể RÚT DÂY CÁP USB ra an toàn.\n"
                    f"Ứng dụng đã tự động chuyển sang điều khiển qua Wi-Fi ({self.active_serial})."
                )
            else:
                self.log(f"❌ {msg_str}")
                QMessageBox.warning(self, "Lỗi kết nối Wi-Fi", msg_str)

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

    def cleanup_all(self):
        # 1. Cancel and terminate bot worker
        if getattr(self, "bot_worker", None) is not None and self.bot_worker.isRunning():
            try:
                self.bot_worker.cancel()
                self.bot_worker.quit()
                if not self.bot_worker.wait(800):
                    self.bot_worker.terminate()
                    self.bot_worker.wait(400)
            except Exception:
                pass
            self.bot_worker = None

        # 2. Terminate / kill scrcpy process
        if getattr(self, "scrcpy_proc", None) is not None:
            try:
                if self.scrcpy_proc.poll() is None:
                    self.scrcpy_proc.terminate()
                    try:
                        self.scrcpy_proc.wait(timeout=0.8)
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

        # 4. Drain thread pool cleanly
        try:
            QThreadPool.globalInstance().waitForDone(500)
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            self.cleanup_all()
        except Exception:
            pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DroidMasterApp()
    window.show()
    sys.exit(app.exec())
