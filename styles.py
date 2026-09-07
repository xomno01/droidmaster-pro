# -*- coding: utf-8 -*-
"""
DroidMaster Ultra-Modern UI Theme (2026 Design System)
Inspired by Linear, Raycast, and macOS Fluent design.
Clean, breathable, modern dark aesthetics with refined accents and zero visual clutter.
"""

DARK_THEME_QSS = """
/* Reset & Global */
* {
    outline: none;
}

QWidget {
    background-color: #0b0f17;
    color: #e2e8f0;
    font-family: "Segoe UI Variable Display", "Segoe UI", -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #10b981;
    selection-color: #000000;
}

QMainWindow {
    background-color: #0b0f17;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* Card Surface (Bento Grid Cards) */
QFrame.bentoCard {
    background-color: #111827;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    padding: 0px;
}
QFrame.bentoCard:hover {
    border-color: rgba(255, 255, 255, 0.14);
}

QFrame.bentoCard QPushButton {
    min-height: 36px;
    font-size: 13px;
    font-weight: 600;
    border-radius: 8px;
    padding: 6px 12px;
}

/* Sidebar Container */
QScrollArea#sidebarScroll {
    background-color: #0e1420;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}
QScrollArea#sidebarScroll > QWidget > QWidget {
    background-color: #0e1420;
}

QFrame#sidebarFrame {
    background-color: #0e1420;
    border: none;
}

/* Hero Mirror Card */
QFrame#heroCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #131d2e, stop:1 #0f172a);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 18px;
    padding: 0px;
}

/* Labels */
QLabel {
    color: #cbd5e1;
    background: transparent;
}

QLabel#brandTitle {
    font-size: 18px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.5px;
}

QLabel#cardTitle {
    font-size: 15px;
    font-weight: 700;
    color: #f8fafc;
}

QLabel#cardDesc {
    font-size: 12px;
    color: #64748b;
    line-height: 1.4;
}

QLabel#metricValue {
    font-size: 13.5px;
    font-weight: 700;
    color: #f1f5f9;
}

QLabel#metricLabel {
    font-size: 11px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Status Badges & Pills */
QLabel#statusPill {
    background-color: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
}

QLabel#statusPillOffline {
    background-color: rgba(239, 68, 68, 0.12);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
}

QLabel#metricPill {
    background-color: #1e293b;
    color: #94a3b8;
    border-radius: 8px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 600;
}

/* Push Buttons */
QPushButton {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 10px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #273549;
    border-color: rgba(255, 255, 255, 0.18);
}

QPushButton:pressed {
    background-color: #172033;
    border-color: rgba(255, 255, 255, 0.05);
}

QPushButton:disabled {
    background-color: #111827;
    color: #475569;
    border-color: rgba(255, 255, 255, 0.04);
}

/* Primary Hero Button (Emerald Green Glow) */
QPushButton#primaryHeroBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
    color: #ffffff;
    border: none;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 800;
    min-height: 40px;
    padding: 8px 16px;
}

QPushButton#primaryHeroBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 #10b981);
}

QPushButton#primaryHeroBtn:pressed {
    background: #047857;
}

/* Stop Button (Red Accent) */
QPushButton#stopBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #dc2626);
    color: #ffffff;
    border: none;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 700;
    padding: 12px 24px;
}

QPushButton#stopBtn:hover {
    background: #f87171;
}

/* User Guide Button (Indigo / Violet Gradient) */
QPushButton#btnUserGuide {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 12px;
    min-height: 32px;
}

QPushButton#btnUserGuide:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6);
    border-color: #a78bfa;
}

/* Mini Header Toggle Button (e.g. Change IP / Settings) */
QPushButton#btnMiniToggle {
    background-color: rgba(245, 158, 11, 0.16);
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 6px;
    color: #f59e0b;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    min-height: 22px;
}

QPushButton#btnMiniToggle:hover {
    background-color: rgba(245, 158, 11, 0.32);
    border-color: #fbbf24;
    color: #ffffff;
}

/* Action Card Button (Modern Tile Button) */
QPushButton#actionTileBtn {
    background-color: #162032;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
    color: #f1f5f9;
}

QPushButton#actionTileBtn:hover {
    background-color: #1e2c45;
    border-color: #38bdf8;
}

/* Remote Navigation Bar (Dock Style) */
QFrame#navDock {
    background-color: #162032;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 6px;
}

QPushButton.navBtn {
    background-color: transparent;
    color: #cbd5e1;
    border: none;
    border-radius: 8px;
    padding: 10px;
    font-size: 14px;
    font-weight: 700;
}

QPushButton.navBtn:hover {
    background-color: #24324c;
    color: #38bdf8;
}

QPushButton.navBtn:pressed {
    background-color: #0f172a;
}

/* App Quick Launcher Icons */
QPushButton.appIconBtn {
    background-color: #162032;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 6px 10px;
    font-weight: 600;
    font-size: 12px;
    min-height: 32px;
}

QPushButton.appIconBtn:hover {
    background-color: #1f2e48;
    border-color: rgba(255, 255, 255, 0.2);
}

/* Input Fields */
QLineEdit {
    background-color: #111827;
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 13px;
    min-height: 38px;
}

QLineEdit:focus {
    border: 1px solid #38bdf8;
    background-color: #131c2e;
}

/* Combo Box (Modern Dropdown) */
QComboBox {
    background-color: #162032;
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
    min-height: 38px;
}

QComboBox:hover {
    border-color: #38bdf8;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #111827;
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    selection-background-color: #10b981;
    selection-color: #000000;
    padding: 6px;
}

/* Checkboxes (Toggle style) */
QCheckBox {
    spacing: 8px;
    color: #94a3b8;
    font-size: 12px;
    font-weight: 500;
}

QCheckBox:hover {
    color: #e2e8f0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #334155;
    background-color: #0f172a;
}

QCheckBox::indicator:checked {
    background-color: #10b981;
    border-color: #10b981;
}

/* Terminal Console (macOS / iTerm2 Style) */
QFrame#terminalHeader {
    background-color: #0f172a;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-bottom: none;
    padding: 6px 12px;
}

QTextEdit#terminalOutput {
    background-color: #060910;
    color: #4ade80;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-top: none;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
    padding: 10px;
    line-height: 1.5;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""
