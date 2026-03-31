# Apex Legends No-Recoil & Settings Editor (Python)

โครงการนี้เป็นเครื่องมือสำหรับปรับแต่งการตั้งค่าและช่วยควบคุมแรงดีด (No-Recoil) ในเกม Apex Legends โดยใช้ระบบ OCR (Optical Character Recognition) ในการสแกนชื่อปืนอัตโนมัติ

## 🚀 สถานะปัจจุบัน (Current Progress)

เราได้รวมระบบการทำงานจริง (Core Logic) เข้ากับหน้าจอตั้งค่า (GUI) เรียบร้อยแล้ว:
- [x] **GUI Editor**: หน้าจอสำหรับปรับ Sensitivity, Resolution และค่าอื่นๆ
- [x] **OCR Integration**: ระบบสแกน HUD ปืนจากจอเกม (รองรับ 1080p HUD)
- [x] **No-Recoil Control**: ระบบลดแรงดีดผ่าน Interception Driver (Low-level mouse control)
- [x] **Auto-Admin**: ระบบขอสิทธิ์ Administrator อัตโนมัติเมื่อเริ่มโปรแกรม

## 🛠️ โครงสร้างไฟล์ (Project Structure)

- `gui.py`: ไฟล์หลัก (Main Entry) - จัดการ UI และ Threads สำหรับ Recoil/OCR
- `config_store.py`: จัดการการอ่าน/เขียนไฟล์ `settings.ini` (INI format)
- `uuid_generator.py`: สร้าง UUID ประจำเครื่องเพื่อใช้ระบุตัวตน
- `Pattern/`: โฟลเดอร์เก็บไฟล์ `.txt` สำหรับแรงดีดของปืนแต่ละชนิด
- `Resolution/`: โฟลเดอร์เก็บไฟล์ `.ini` สำหรับข้อมูลพิกัดจอแยกตามความละเอียด
- `apexmaster.py`: ยูทิลิตี้สำหรับดึงข้อมูลสรุปผลของ Patterns/Resolutions (CLI)

## 📦 ความต้องการของระบบ (Requirements)

โปรแกรมนี้ออกแบบมาสำหรับ **Windows** เท่านั้น และต้องการ Library ดังนี้:
- `mss` (Screen capture)
- `opencv-python` (Image processing)
- `numpy` (Array handling)
- `pytesseract` (OCR engine)
- `interception-python` (Mouse driver wrapper)

**สำคัญ:** ต้องติดตั้ง **Tesseract-OCR** ในเครื่อง (Path เริ่มต้นคือ `C:\Program Files\Tesseract-OCR\tesseract.exe`) และติดตั้ง **Interception Driver**

## 🏗️ สถาปัตยกรรม (Architecture Notes for AI/Developers)

### 1. Threading Model
โปรแกรมทำงานแบบ Multi-threading โดยแบ่งเป็น:
- **Main Thread**: จัดการ Tkinter GUI
- **Recoil Thread**: วนลูปตรวจสอบการกดคลิกซ้าย/ขวา และสั่งขยับเมาส์ (Precise timing)
- **OCR Thread**: แคปหน้าจอตำแหน่ง HUD และสแกนหาชื่อปืนทุกๆ 0.5 วินาที

### 2. Sensitivity Sync
ระบบใช้สูตร `modifier = (4.0 / sensitivity)` จากโค้ดเดิม เมื่อมีการเลื่อน Slider ใน GUI ค่า `modifier` ในระบบ Recoil จะถูกอัปเดตแบบ Real-time ทันที

### 3. File Encoding
ไฟล์ `settings.ini` และไฟล์ใน `Resolution/` ถูกจัดเก็บในรูปแบบ **UTF-16 LE with BOM** เพื่อให้รองรับกับสคริปต์ AutoHotkey (AHK) ตัวเดิม

## ⏭️ สิ่งที่สามารถพัฒนาต่อได้ (Future Tasks)
- เพิ่มระบบจำลองการกดคีย์บอร์ด (Keybinding) สำหรับเปลี่ยนสลับปืนอัตโนมัติ
- ปรับปรุง UI ให้เป็นแบบ Modern/Transparent Overlay ในเกม
- เพิ่มระบบรองรับความละเอียดหน้าจอที่หลากหลายมากขึ้น (Dynamic HUD detection)
