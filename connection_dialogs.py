# -*- coding: utf-8 -*-
"""
DroidMaster Pro - Modern Connection & Onboarding Dialogs
Provides:
1. ConnectingProgressDialog: Animated popup with progress bar, dynamic %, and step-by-step connection status.
2. TailscaleOnboardingDialog: Friendly guide shown when USB stream launches, explaining remote setup with Tailscale.
"""

from typing import Optional, Callable
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QCheckBox,
    QFrame,
    QScrollArea,
)

from device_manager import DeviceProfile
import adb_core


class ConnectingProgressDialog(QDialog):
    """
    Animated connection progress modal dialog.
    Displays target device, connection route, animated % progress bar,
    step status, and handles retry/cancel/error states gracefully.
    """

    cancelled = Signal()
    retry_requested = Signal()
    open_profiles_requested = Signal()

    def __init__(self, parent=None, profile: Optional[DeviceProfile] = None):
        super().__init__(parent)
        self.profile = profile
        self.target_progress = 0
        self.current_progress = 0
        self.is_completed = False
        self.is_error = False

        self.setWindowTitle("⚡ DroidMaster Pro — Đang Kết Nối Thiết Bị...")
        self.setMinimumSize(500, 330)
        self.resize(550, 350)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Smooth animation timer (ticks every 20ms)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate_progress_tick)

        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0f19;
                color: #f8fafc;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }
            QFrame#cardFrame {
                background-color: #111827;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                padding: 16px;
            }
            QFrame#stepBox {
                background-color: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 10px 14px;
            }
            QProgressBar {
                background-color: #1e293b;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 7px;
                height: 14px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:0.5 #06b6d4, stop:1 #3b82f6);
                border-radius: 6px;
            }
            QPushButton {
                background-color: #1f2937;
                color: #cbd5e1;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                min-height: 38px;
            }
            QPushButton:hover {
                background-color: #374151;
                color: #ffffff;
            }
            QPushButton#btnPrimary {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
                color: #ffffff;
                font-weight: 700;
                border: none;
            }
            QPushButton#btnPrimary:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 #10b981);
            }
            QPushButton#btnCancel {
                background-color: transparent;
                border: 1px solid rgba(239, 68, 68, 0.3);
                color: #fca5a5;
            }
            QPushButton#btnCancel:hover {
                background-color: rgba(239, 68, 68, 0.15);
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Main Card Frame
        card = QFrame()
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(14)

        # Top Header Row: Device Icon + Name on Left, Percent on Right
        top_hdr = QHBoxLayout()
        top_hdr.setSpacing(10)

        self.lbl_icon = QLabel("⚡")
        self.lbl_icon.setFont(QFont("Segoe UI", 20))
        top_hdr.addWidget(self.lbl_icon)

        dev_name = self.profile.name if self.profile else "Thiết bị Android"
        self.lbl_device_name = QLabel(f"📱 {dev_name}")
        self.lbl_device_name.setStyleSheet("font-size: 17px; font-weight: 800; color: #ffffff;")
        top_hdr.addWidget(self.lbl_device_name)
        top_hdr.addStretch()

        self.lbl_percent = QLabel("Connecting... 0%")
        self.lbl_percent.setStyleSheet("font-size: 15px; font-weight: 800; color: #38bdf8;")
        top_hdr.addWidget(self.lbl_percent)
        card_layout.addLayout(top_hdr)

        # Dedicated Route Badge (Full Width)
        self.lbl_route_badge = QLabel("Đang xác định lộ trình...")
        self.lbl_route_badge.setWordWrap(True)
        self.lbl_route_badge.setStyleSheet("""
            background-color: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(56, 189, 248, 0.2);
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 600;
            color: #38bdf8;
        """)
        card_layout.addWidget(self.lbl_route_badge)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        card_layout.addWidget(self.progress_bar)

        # Step Box: Visual checklist of connection phases
        self.step_box = QFrame()
        self.step_box.setObjectName("stepBox")
        step_layout = QVBoxLayout(self.step_box)
        step_layout.setContentsMargins(12, 10, 12, 10)
        step_layout.setSpacing(8)

        self.step1_lbl = QLabel("⏳ 1. Phân giải lộ trình kết nối tối ưu (USB / LAN / Tailscale)")
        self.step1_lbl.setStyleSheet("font-size: 12.5px; color: #cbd5e1; padding: 2px 0;")
        step_layout.addWidget(self.step1_lbl)

        self.step2_lbl = QLabel("○ 2. Bắt tay và xác thực cổng ADB")
        self.step2_lbl.setStyleSheet("font-size: 12.5px; color: #64748b; padding: 2px 0;")
        step_layout.addWidget(self.step2_lbl)

        self.step3_lbl = QLabel("○ 3. Khởi tạo đường truyền Scrcpy 60FPS độ trễ thấp")
        self.step3_lbl.setStyleSheet("font-size: 12.5px; color: #64748b; padding: 2px 0;")
        step_layout.addWidget(self.step3_lbl)

        card_layout.addWidget(self.step_box)

        # Error banner container (initially hidden)
        self.error_frame = QFrame()
        self.error_frame.setStyleSheet("""
            background-color: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 10px;
            padding: 10px;
        """)
        err_layout = QVBoxLayout(self.error_frame)
        err_layout.setContentsMargins(10, 8, 10, 8)
        err_layout.setSpacing(4)

        self.lbl_err_title = QLabel("❌ Kết nối không thành công")
        self.lbl_err_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #fca5a5;")
        err_layout.addWidget(self.lbl_err_title)

        self.lbl_err_detail = QLabel("Chi tiết lỗi...")
        self.lbl_err_detail.setWordWrap(True)
        self.lbl_err_detail.setStyleSheet("font-size: 12px; color: #fecaca;")
        err_layout.addWidget(self.lbl_err_detail)

        self.error_frame.setVisible(False)
        card_layout.addWidget(self.error_frame)

        layout.addWidget(card)

        # Bottom Buttons Row
        self.btn_row = QHBoxLayout()
        self.btn_row.setSpacing(10)

        self.btn_manage_profiles = QPushButton("📋 Mở Danh Bạ")
        self.btn_manage_profiles.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_manage_profiles.setVisible(False)
        self.btn_manage_profiles.clicked.connect(self._on_open_profiles_clicked)
        self.btn_row.addWidget(self.btn_manage_profiles)

        self.btn_retry = QPushButton("🔄 Thử Lại")
        self.btn_retry.setObjectName("btnPrimary")
        self.btn_retry.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_retry.setVisible(False)
        self.btn_retry.clicked.connect(self._on_retry_clicked)
        self.btn_row.addWidget(self.btn_retry)

        self.btn_row.addStretch()

        self.btn_cancel = QPushButton("Hủy Bỏ")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        self.btn_row.addWidget(self.btn_cancel)

        layout.addLayout(self.btn_row)

        self.anim_timer.start(20)

    def set_route_info(self, route_type: str, target: str):
        """Update route type badge."""
        type_labels = {
            "USB": "⚡ [Cáp USB Tốc Độ Cao]",
            "LAN": "📶 [Wi-Fi Mạng Nội Bộ]",
            "Tailscale": "🌐 [Tailscale VPN Từ Xa]"
        }
        badge = type_labels.get(route_type, f"[{route_type}]")
        self.lbl_route_badge.setText(f"{badge} -> {target}")

    def update_stage(self, stage: int, target_pct: int, message: str = "", detail: str = ""):
        """
        Advance to a stage with target percentage.
        Stage 1: Route resolution
        Stage 2: ADB connect
        Stage 3: Scrcpy stream launch
        Stage 4: Complete
        """
        self.target_progress = min(100, max(0, target_pct))

        if stage == 1:
            self.step1_lbl.setText("⚡ 1. Đang dò tìm cổng và kiểm tra lộ trình...")
            self.step1_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #38bdf8;")
        elif stage == 2:
            self.step1_lbl.setText("✓ 1. Lộ trình tối ưu đã sẵn sàng")
            self.step1_lbl.setStyleSheet("font-size: 12px; color: #10b981;")
            self.step2_lbl.setText("⚡ 2. Đang bắt tay và xác thực cổng ADB...")
            self.step2_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #38bdf8;")
        elif stage == 3:
            self.step1_lbl.setText("✓ 1. Lộ trình tối ưu đã sẵn sàng")
            self.step1_lbl.setStyleSheet("font-size: 12px; color: #10b981;")
            self.step2_lbl.setText("✓ 2. Đã kết nối ADB an toàn")
            self.step2_lbl.setStyleSheet("font-size: 12px; color: #10b981;")
            self.step3_lbl.setText("🚀 3. Đang khởi chạy Scrcpy 60FPS...")
            self.step3_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #38bdf8;")
        elif stage >= 4:
            self.step1_lbl.setText("✓ 1. Lộ trình tối ưu đã sẵn sàng")
            self.step1_lbl.setStyleSheet("font-size: 12px; color: #10b981;")
            self.step2_lbl.setText("✓ 2. Đã kết nối ADB an toàn")
            self.step2_lbl.setStyleSheet("font-size: 12px; color: #10b981;")
            self.step3_lbl.setText("✓ 3. Đã bật chiếu màn hình 60FPS")
            self.step3_lbl.setStyleSheet("font-size: 12px; color: #10b981;")

    def set_success(self, message: str = "Kết nối thành công! Đang mở màn hình..."):
        """Mark as successfully completed."""
        self.is_completed = True
        self.target_progress = 100
        self.current_progress = 100
        self.progress_bar.setValue(100)
        self.lbl_percent.setText("Connecting... 100%")
        self.lbl_percent.setStyleSheet("font-size: 15px; font-weight: 800; color: #10b981;")
        self.lbl_icon.setText("✅")
        self.update_stage(4, 100, message)

        self.btn_cancel.setVisible(False)
        # Auto-close after brief delay so user sees 100% confirmation
        QTimer.singleShot(600, self.accept)

    def set_error(self, title: str, detail: str, can_retry: bool = True):
        """Display error state with clear actionable details."""
        self.is_error = True
        self.anim_timer.stop()
        self.lbl_icon.setText("❌")
        self.lbl_percent.setText("Thất bại")
        self.lbl_percent.setStyleSheet("font-size: 15px; font-weight: 800; color: #ef4444;")

        # Red styling for progress bar
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border-radius: 7px;
                height: 14px;
            }
            QProgressBar::chunk {
                background: #ef4444;
                border-radius: 6px;
            }
        """)

        self.lbl_err_title.setText(f"❌ {title}")
        self.lbl_err_detail.setText(detail)
        self.error_frame.setVisible(True)

        self.btn_retry.setVisible(can_retry)
        self.btn_manage_profiles.setVisible(True)
        self.btn_cancel.setText("Đóng")

    def _animate_progress_tick(self):
        """Smoothly ticks progress towards target_progress."""
        if self.current_progress < self.target_progress:
            # Advance smoothly
            diff = self.target_progress - self.current_progress
            step = max(1, int(diff * 0.2))
            self.current_progress = min(self.target_progress, self.current_progress + step)
            self.progress_bar.setValue(self.current_progress)
            self.lbl_percent.setText(f"Connecting... {self.current_progress}%")

    def _on_cancel_clicked(self):
        self.anim_timer.stop()
        self.cancelled.emit()
        self.reject()

    def _on_retry_clicked(self):
        self.is_error = False
        self.error_frame.setVisible(False)
        self.btn_retry.setVisible(False)
        self.btn_manage_profiles.setVisible(False)
        self.btn_cancel.setText("Hủy Bỏ")
        self.current_progress = 0
        self.target_progress = 10
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 7px;
                height: 14px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:0.5 #06b6d4, stop:1 #3b82f6);
                border-radius: 6px;
            }
        """)
        self.anim_timer.start(20)
        self.retry_requested.emit()

    def _on_open_profiles_clicked(self):
        self.open_profiles_requested.emit()
        self.accept()


class TailscaleOnboardingDialog(QDialog):
    """
    Friendly Dark Obsidian modal onboarding popup shown when USB stream is active.
    Guides the user on setting up Tailscale for seamless remote control without cables.
    """

    open_profiles_requested = Signal()

    def __init__(self, parent=None, device_name: str = "Thiết bị Android", device_serial: str = ""):
        super().__init__(parent)
        self.device_name = device_name
        self.device_serial = device_serial

        self.setWindowTitle("💡 DroidMaster Pro — Mẹo Điều Khiển Từ Xa (Không Dây)")
        self.setMinimumSize(540, 500)
        self.resize(580, 560)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0f19;
                color: #f8fafc;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QFrame#heroCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #131d2e, stop:1 #0f172a);
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 16px;
                padding: 16px;
            }
            QFrame#stepCard {
                background-color: #111827;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 14px;
            }
            QFrame#stepItem {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 12px;
            }
            QPushButton {
                background-color: #1f2937;
                color: #cbd5e1;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                min-height: 38px;
            }
            QPushButton:hover {
                background-color: #374151;
                color: #ffffff;
            }
            QPushButton#btnPrimary {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0369a1);
                color: #ffffff;
                font-weight: 700;
                border: none;
            }
            QPushButton#btnPrimary:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #0284c7);
            }
            QCheckBox {
                color: #94a3b8;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                background-color: #111827;
            }
            QCheckBox::indicator:checked {
                background-color: #10b981;
                border-color: #10b981;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # Scroll container for small screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(2, 2, 2, 2)
        content_layout.setSpacing(10)

        # Hero Announcement Card
        hero_card = QFrame()
        hero_card.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(12, 10, 12, 10)
        hero_layout.setSpacing(6)

        hero_top = QHBoxLayout()
        icon_lbl = QLabel("🌐")
        icon_lbl.setFont(QFont("Segoe UI", 22))
        hero_top.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        h_title = QLabel("Mẹo Điều Khiển Từ Xa — Không Cần Cắm Cáp")
        h_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #ffffff;")
        title_box.addWidget(h_title)

        h_sub = QLabel(f"Thiết bị '{self.device_name}' đã kết nối qua cáp USB thành công!")
        h_sub.setStyleSheet("font-size: 12px; color: #38bdf8; font-weight: 600;")
        title_box.addWidget(h_sub)
        hero_top.addLayout(title_box)
        hero_top.addStretch()
        hero_layout.addLayout(hero_top)

        hero_desc = QLabel(
            "Để lần sau bạn có thể điều khiển thiết bị này từ xa (đi du lịch, quán cafe) "
            "mà <b>không cần cắm dây USB</b>, hãy thực hiện 3 bước đơn giản:"
        )
        hero_desc.setWordWrap(True)
        hero_desc.setStyleSheet("font-size: 12px; color: #cbd5e1; line-height: 1.3;")
        hero_layout.addWidget(hero_desc)

        content_layout.addWidget(hero_card)

        # 3-Step Instruction Card
        step_card = QFrame()
        step_card.setObjectName("stepCard")
        step_card_layout = QVBoxLayout(step_card)
        step_card_layout.setContentsMargins(10, 8, 10, 8)
        step_card_layout.setSpacing(6)

        # Step 1
        s1 = QFrame()
        s1.setObjectName("stepItem")
        s1_lay = QHBoxLayout(s1)
        s1_lay.setContentsMargins(8, 4, 8, 4)
        s1_num = QLabel("1️⃣")
        s1_num.setFont(QFont("Segoe UI", 15))
        s1_lay.addWidget(s1_num)
        s1_txt = QLabel("<b>Cài đặt app Tailscale trên Android</b><br><span style='color: #94a3b8; font-size: 11px;'>Tải miễn phí từ Google Play Store hoặc file APK chính thức trên điện thoại/tablet.</span>")
        s1_txt.setWordWrap(True)
        s1_lay.addWidget(s1_txt, stretch=1)
        step_card_layout.addWidget(s1)

        # Step 2
        s2 = QFrame()
        s2.setObjectName("stepItem")
        s2_lay = QHBoxLayout(s2)
        s2_lay.setContentsMargins(8, 4, 8, 4)
        s2_num = QLabel("2️⃣")
        s2_num.setFont(QFont("Segoe UI", 15))
        s2_lay.addWidget(s2_num)
        s2_txt = QLabel("<b>Đăng nhập cùng tài khoản Tailscale</b><br><span style='color: #94a3b8; font-size: 11px;'>Đăng nhập đúng tài khoản mà máy tính này đang dùng để kết nối mạng riêng ảo an toàn.</span>")
        s2_txt.setWordWrap(True)
        s2_lay.addWidget(s2_txt, stretch=1)
        step_card_layout.addWidget(s2)

        # Step 3
        s3 = QFrame()
        s3.setObjectName("stepItem")
        s3_lay = QHBoxLayout(s3)
        s3_lay.setContentsMargins(8, 4, 8, 4)
        s3_num = QLabel("3️⃣")
        s3_num.setFont(QFont("Segoe UI", 15))
        s3_lay.addWidget(s3_num)
        s3_txt = QLabel("<b>Lưu IP Tailscale vào DroidMaster</b><br><span style='color: #94a3b8; font-size: 11px;'>Mở <i>Danh Bạ Máy</i> trong DroidMaster, dán IP (100.x.y.z). Lần tới chỉ cần bấm <b>⚡ KẾT NỐI NHANH</b>!</span>")
        s3_txt.setWordWrap(True)
        s3_lay.addWidget(s3_txt, stretch=1)
        step_card_layout.addWidget(s3)

        content_layout.addWidget(step_card)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Do not show again checkbox
        self.chk_dont_show = QCheckBox("Không hiển thị lại hướng dẫn này trên thiết bị này")
        self.chk_dont_show.setCursor(QCursor(Qt.PointingHandCursor))
        main_layout.addWidget(self.chk_dont_show)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_configure = QPushButton("⚙ Mở Danh Bạ Nhập IP Ngay")
        self.btn_configure.setObjectName("btnPrimary")
        self.btn_configure.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_configure.clicked.connect(self._on_configure_clicked)
        btn_layout.addWidget(self.btn_configure)

        btn_layout.addStretch()

        self.btn_close = QPushButton("Đã Hiểu && Đóng")
        self.btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_close.clicked.connect(self._on_close_clicked)
        btn_layout.addWidget(self.btn_close)

        main_layout.addLayout(btn_layout)

    def _save_preference_if_checked(self):
        """If user checked 'Do not show again', persist to config.json."""
        if self.chk_dont_show.isChecked() and self.device_serial:
            cfg = adb_core.load_config()
            dismissed = set(cfg.get("dismissed_tailscale_hints", []))
            dismissed.add(self.device_serial)
            adb_core.save_config("dismissed_tailscale_hints", list(dismissed))

    def _on_configure_clicked(self):
        self._save_preference_if_checked()
        self.open_profiles_requested.emit()
        self.accept()

    def _on_close_clicked(self):
        self._save_preference_if_checked()
        self.accept()


def should_show_tailscale_hint(serial: str, profile: Optional[DeviceProfile] = None) -> bool:
    """
    Check whether the Tailscale remote onboarding hint should be shown.
    Returns True only if:
    1. It's a USB connection (no ':' in serial or endpoint).
    2. The serial has NOT been marked as dismissed in config.json.
    3. The profile does not already have a valid tailscale_ip filled in.
    """
    if not serial or ":" in serial:
        return False  # Already remote/network connected

    cfg = adb_core.load_config()
    dismissed = cfg.get("dismissed_tailscale_hints", [])
    if serial in dismissed:
        return False

    if profile:
        if profile.id in dismissed:
            return False
        # If user already configured a Tailscale IP for this profile, don't nag
        ts_ep = (getattr(profile, "tailscale_endpoint", "") or getattr(profile, "tailscale_ip", "")).strip()
        if ts_ep:
            return False

    return True
