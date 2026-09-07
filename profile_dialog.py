# -*- coding: utf-8 -*-
"""
DroidMaster Pro - Device Profiles Management Dialog
Provides a sleek, native Dark Obsidian dialog for managing device profiles,
custom Scrcpy flags, and connection routes.
"""

from typing import Optional, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QFrame,
    QMessageBox,
    QFormLayout,
    QGroupBox,
    QScrollArea,
)

from device_manager import DeviceProfile, device_manager
import adb_core


class ProfileDialog(QDialog):
    """Modern Bento Dark modal dialog for managing device profiles."""

    profiles_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 DroidMaster Pro — Quản Lý Danh Bạ Thiết Bị")
        self.setMinimumSize(660, 460)
        self.resize(760, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.current_profile: Optional[DeviceProfile] = None

        self.init_ui()
        self.load_profile_list()

    def init_ui(self):
        # Apply dark theme styling matching styles.py
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0f19;
                color: #f8fafc;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #161e2e;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px 12px;
                color: #f8fafc;
                font-size: 13px;
                min-height: 38px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #3b82f6;
                background-color: #1e293b;
            }
            QComboBox::drop-down {
                border: none;
                width: 28px;
            }
            QListWidget {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 10px;
                padding: 6px;
                color: #f8fafc;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 6px;
                margin-bottom: 4px;
            }
            QListWidget::item:hover {
                background-color: #1e293b;
            }
            QListWidget::item:selected {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: 600;
            }
            QGroupBox {
                border: 1px solid #1e293b;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 14px;
                font-weight: bold;
                color: #94a3b8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QCheckBox {
                color: #cbd5e1;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #475569;
                background: #1e293b;
            }
            QCheckBox::indicator:checked {
                background: #10b981;
                border-color: #10b981;
            }
            QPushButton {
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        lbl_title = QLabel("📋 Danh Bạ Thiết Bị Thông Minh")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #38bdf8;")
        lbl_sub = QLabel("Lưu trữ cấu hình mạng, Tailscale IP và tùy chọn tự động kết nối lại.")
        lbl_sub.setStyleSheet("font-size: 12px; color: #94a3b8;")

        head_v = QVBoxLayout()
        head_v.addWidget(lbl_title)
        head_v.addWidget(lbl_sub)
        header_layout.addLayout(head_v)
        header_layout.addStretch()

        self.btn_new = QPushButton("➕ Thêm Thiết Bị Mới")
        self.btn_new.setStyleSheet("background-color: #2563eb; color: #ffffff;")
        self.btn_new.clicked.connect(self.on_click_new)
        header_layout.addWidget(self.btn_new)
        main_layout.addLayout(header_layout)

        # Body Layout: Left (List) & Right (Form)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(18)

        # Left Column: List of profiles
        left_v = QVBoxLayout()
        lbl_list_head = QLabel("DANH SÁCH THIẾT BỊ")
        lbl_list_head.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 1px;")
        left_v.addWidget(lbl_list_head)

        self.list_profiles = QListWidget()
        self.list_profiles.currentItemChanged.connect(self.on_select_profile)
        left_v.addWidget(self.list_profiles)

        self.btn_delete = QPushButton("🗑️ Xóa Thiết Bị")
        self.btn_delete.setStyleSheet("background-color: #3f1d24; color: #f87171; border: 1px solid #7f1d1d;")
        self.btn_delete.clicked.connect(self.on_click_delete)
        left_v.addWidget(self.btn_delete)

        body_layout.addLayout(left_v, 1)

        # Right Column: Profile Edit Form wrapped in smooth QScrollArea
        right_scroll = QScrollArea()
        right_scroll.setObjectName("profileScrollArea")
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        right_container = QWidget()
        right_container.setStyleSheet("background: transparent;")
        right_v = QVBoxLayout(right_container)
        right_v.setContentsMargins(6, 4, 16, 6)
        right_v.setSpacing(14)

        lbl_form_head = QLabel("THÔNG TIN CẤU HÌNH")
        lbl_form_head.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 1px;")
        right_v.addWidget(lbl_form_head)

        # Basic Info Group
        grp_basic = QGroupBox("Nhận Diện Thiết Bị")
        form_basic = QFormLayout(grp_basic)
        form_basic.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form_basic.setRowWrapPolicy(QFormLayout.DontWrapRows)
        form_basic.setVerticalSpacing(12)
        form_basic.setHorizontalSpacing(14)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Ví dụ: 📱 POCO F1 (Tailscale)")
        form_basic.addRow("Tên gợi nhớ:", self.txt_name)

        self.txt_model = QLineEdit()
        self.txt_model.setPlaceholderText("Ví dụ: POCOPHONE F1 / SM-G998B")
        form_basic.addRow("Mã model:", self.txt_model)

        # USB Serial with quick-fetch button
        usb_layout = QHBoxLayout()
        usb_layout.setSpacing(8)
        self.txt_usb = QLineEdit()
        self.txt_usb.setPlaceholderText("Serial khi cắm cáp (ví dụ: 9e29bf42)")
        self.btn_fetch_usb = QPushButton("Lấy từ máy đang cắm")
        self.btn_fetch_usb.setStyleSheet("background: #1e293b; color: #38bdf8; border: 1px solid #334155; font-size: 11px; padding: 6px 12px; min-height: 38px; border-radius: 8px;")
        self.btn_fetch_usb.clicked.connect(self.on_fetch_usb_serial)
        usb_layout.addWidget(self.txt_usb)
        usb_layout.addWidget(self.btn_fetch_usb)
        form_basic.addRow("USB Serial:", usb_layout)

        right_v.addWidget(grp_basic)

        # Network Routes Group
        grp_net = QGroupBox("Đường Truyền & Địa Chỉ Mạng")
        form_net = QFormLayout(grp_net)
        form_net.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form_net.setRowWrapPolicy(QFormLayout.DontWrapRows)
        form_net.setVerticalSpacing(12)
        form_net.setHorizontalSpacing(14)

        self.txt_tailscale = QLineEdit()
        self.txt_tailscale.setPlaceholderText("Ví dụ: 100.83.144.79:5555")
        form_net.addRow("IP Tailscale VPN:", self.txt_tailscale)

        self.txt_lan = QLineEdit()
        self.txt_lan.setPlaceholderText("Ví dụ: 192.168.1.50:5555")
        form_net.addRow("IP Wi-Fi LAN:", self.txt_lan)

        self.combo_route = QComboBox()
        self.combo_route.addItem("⚡ Tự động (Auto Fallback: USB → LAN → Tailscale)", "auto")
        self.combo_route.addItem("🌐 Ưu tiên Tailscale (Điều khiển từ xa qua VPN)", "tailscale")
        self.combo_route.addItem("📶 Ưu tiên Wi-Fi LAN (Mạng gia đình / văn phòng)", "lan")
        self.combo_route.addItem("🔌 Ưu tiên Cáp USB (Độ trễ thấp nhất)", "usb")
        form_net.addRow("Lộ trình ưu tiên:", self.combo_route)

        right_v.addWidget(grp_net)

        # Scrcpy & Resilience Group
        grp_opts = QGroupBox("Tùy Chọn Khắc Phục Lỗi & Chiếu Màn Hình")
        v_opts = QVBoxLayout(grp_opts)
        v_opts.setSpacing(10)

        self.chk_no_audio = QCheckBox("🔇 Tắt âm thanh (--no-audio) — Khuyên dùng cho Android 10 (POCO F1)")
        v_opts.addWidget(self.chk_no_audio)

        self.chk_auto_reconnect = QCheckBox("🔄 Tự động kết nối lại khi đứt mạng (Silent Auto-Reconnect)")
        self.chk_auto_reconnect.setChecked(True)
        v_opts.addWidget(self.chk_auto_reconnect)

        rec_layout = QHBoxLayout()
        lbl_rec = QLabel("Số lần thử kết nối lại tối đa:")
        self.spin_retries = QSpinBox()
        self.spin_retries.setRange(1, 10)
        self.spin_retries.setValue(3)
        self.spin_retries.setFixedWidth(70)
        rec_layout.addWidget(lbl_rec)
        rec_layout.addWidget(self.spin_retries)
        rec_layout.addStretch()
        v_opts.addLayout(rec_layout)

        right_v.addWidget(grp_opts)

        # Action Buttons on Right
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 Lưu Hồ Sơ Thiết Bị")
        self.btn_save.setStyleSheet("background-color: #10b981; color: #ffffff; font-size: 14px; min-height: 42px; font-weight: 700; border-radius: 8px;")
        self.btn_save.clicked.connect(self.on_click_save)
        btn_layout.addWidget(self.btn_save)

        right_v.addLayout(btn_layout)
        right_scroll.setWidget(right_container)
        body_layout.addWidget(right_scroll, 2)

        main_layout.addLayout(body_layout)

        # Bottom Close Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()
        btn_close = QPushButton("Đóng")
        btn_close.setStyleSheet("background: #1e293b; color: #94a3b8; border: 1px solid #334155; padding: 6px 18px;")
        btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(btn_close)
        main_layout.addLayout(bottom_bar)

    def load_profile_list(self):
        self.list_profiles.clear()
        profiles = device_manager.get_profiles()
        for p in profiles:
            route_badge = "⚡" if p.preferred_route == "auto" else ("🌐" if p.preferred_route == "tailscale" else "📶")
            item = QListWidgetItem(f"{p.name} ({p.get_best_endpoint() or 'Chưa gán IP'})")
            item.setData(Qt.UserRole, p.id)
            self.list_profiles.addItem(item)

        if self.list_profiles.count() > 0:
            self.list_profiles.setCurrentRow(0)
        else:
            self.clear_form()

    def on_select_profile(self, current: QListWidgetItem, previous: Optional[QListWidgetItem]):
        if not current:
            return
        profile_id = current.data(Qt.UserRole)
        p = device_manager.get_profile(profile_id)
        if not p:
            return
        self.current_profile = p
        self.populate_form(p)

    def populate_form(self, p: DeviceProfile):
        self.txt_name.setText(p.name)
        self.txt_model.setText(p.model)
        self.txt_usb.setText(p.usb_serial)
        self.txt_tailscale.setText(p.tailscale_endpoint)
        self.txt_lan.setText(p.lan_endpoint)

        idx = self.combo_route.findData(p.preferred_route)
        if idx >= 0:
            self.combo_route.setCurrentIndex(idx)
        else:
            self.combo_route.setCurrentIndex(0)

        self.chk_no_audio.setChecked("--no-audio" in p.extra_scrcpy_flags)
        self.chk_auto_reconnect.setChecked(p.auto_reconnect)
        self.spin_retries.setValue(p.max_reconnect_attempts)

    def clear_form(self):
        self.current_profile = None
        self.txt_name.clear()
        self.txt_model.clear()
        self.txt_usb.clear()
        self.txt_tailscale.clear()
        self.txt_lan.clear()
        self.combo_route.setCurrentIndex(0)
        self.chk_no_audio.setChecked(False)
        self.chk_auto_reconnect.setChecked(True)
        self.spin_retries.setValue(3)

    def on_click_new(self):
        self.list_profiles.clearSelection()
        self.clear_form()
        self.txt_name.setText("📱 Thiết bị mới")
        self.txt_name.setFocus()

    def on_fetch_usb_serial(self):
        try:
            devs = adb_core.list_devices()
            usb_devs = [d for d in devs if d.get("type") == "USB" and d.get("state") == "device"]
            if usb_devs:
                target = usb_devs[0]
                self.txt_usb.setText(target["serial"])
                if not self.txt_model.text():
                    self.txt_model.setText(target.get("model", ""))
                QMessageBox.information(self, "Thành công", f"Đã nhận diện thiết bị USB: {target.get('model')} ({target['serial']})")
            else:
                QMessageBox.warning(self, "Thông báo", "Không tìm thấy thiết bị nào đang cắm cáp USB!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lấy serial USB: {e}")

    def on_click_save(self):
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Chú ý", "Vui lòng nhập tên thiết bị gợi nhớ!")
            return

        flags = []
        if self.chk_no_audio.isChecked():
            flags.append("--no-audio")

        p_id = self.current_profile.id if self.current_profile else ""
        prof = DeviceProfile(
            id=p_id,
            name=name,
            model=self.txt_model.text().strip(),
            usb_serial=self.txt_usb.text().strip(),
            tailscale_endpoint=self.txt_tailscale.text().strip(),
            lan_endpoint=self.txt_lan.text().strip(),
            preferred_route=self.combo_route.currentData(),
            extra_scrcpy_flags=flags,
            auto_reconnect=self.chk_auto_reconnect.isChecked(),
            max_reconnect_attempts=self.spin_retries.value(),
        )

        saved = device_manager.save_profile(prof)
        self.current_profile = saved
        self.profiles_changed.emit()
        self.load_profile_list()

        # Select saved item
        for i in range(self.list_profiles.count()):
            item = self.list_profiles.item(i)
            if item.data(Qt.UserRole) == saved.id:
                self.list_profiles.setCurrentItem(item)
                break

        QMessageBox.information(self, "Thành công", f"Đã lưu hồ sơ thiết bị '{saved.name}' thành công!")

    def on_click_delete(self):
        curr = self.list_profiles.currentItem()
        if not curr:
            return
        p_id = curr.data(Qt.UserRole)
        p = device_manager.get_profile(p_id)
        if not p:
            return

        ret = QMessageBox.question(
            self,
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa thiết bị '{p.name}' khỏi danh bạ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            device_manager.delete_profile(p_id)
            self.profiles_changed.emit()
            self.load_profile_list()
