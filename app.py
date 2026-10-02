import io
import datetime
import pandas as pd
import streamlit as st
import msoffcrypto

st.set_page_config(page_title="ค้นหาข้อมูลสิทธิการรักษาพยาบาลพนักงานธนาคารออมสิน", layout="centered", page_icon="🏥")

# --- การจัดการรหัสผ่านเข้าหน้า Admin อัปโหลด ---
ADMIN_PASSWORD = "GSBADMINCENTER"

if "df_gsb" not in st.session_state:
    st.session_state["df_gsb"] = None
if "version_update" not in st.session_state:
    st.session_state["version_update"] = "ยังไม่มีการอัปโหลดข้อมูล"

# --- แถบข้าง (Sidebar) สำหรับ Admin อัปโหลดไฟล์ ---
st.sidebar.title("🔒 เมนูผู้ดูแลระบบ (Admin)")
admin_pwd = st.sidebar.text_input("กรอกรหัสผ่าน Admin เพื่ออัปโหลด:", type="password")

if admin_pwd == ADMIN_PASSWORD:
    st.sidebar.success("ยืนยันตัวตนสำเร็จ")
    uploaded_file = st.sidebar.file_uploader("เลือกไฟล์ Excel ปรับปรุงประจำเดือน (.xlsx / .xls)", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        if st.sidebar.button("นำเข้าและอัปเดตข้อมูล (แทนที่เดิม)"):
            try:
                df = None
                try:
                    decrypted_data = io.BytesIO()
                    office_file = msoffcrypto.OfficeFile(uploaded_file)
                    office_file.load_key(password="GSBCENTER")
                    office_file.decrypt(decrypted_data)
                    df = pd.read_excel(decrypted_data, dtype=str)
                except Exception:
                    uploaded_file.seek(0)
                    df = pd.read_excel(uploaded_file, dtype=str)
                
                if df is not None:
                    df.columns = [" ".join(str(c).split()) for c in df.columns]
                    df = df.fillna('')
                    st.session_state["df_gsb"] = df
                    
                    today = datetime.datetime.now()
                    year_buddhism = today.year + 543
                    st.session_state["version_update"] = f"{today.day}/{today.month}/{year_buddhism}"
                    
                    st.sidebar.success("✅ อัปโหลดและปรับปรุงข้อมูลเรียบร้อยแล้ว!")
            except Exception as e:
                st.sidebar.error(f"❌ ไม่สามารถอ่านไฟล์ Excel ได้: {e}")
elif admin_pwd:
    st.sidebar.error("รหัสผ่าน Admin ไม่ถูกต้อง")

# --- หน้าจอหลัก ---
st.markdown("<h2 style='text-align: center; color: #003366;'>ค้นหาข้อมูลสิทธิการรักษาพยาบาลพนักงานธนาคารออมสิน</h2>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align: center;'>Version Update : <span style='color: red;'>{st.session_state['version_update']}</span></h4>", unsafe_allow_html=True)
st.markdown("---")

cid_input = st.text_input("➔ ค้นหาจากรหัสประจำตัวประชาชน :", placeholder="กรอกเลขบัตรประชาชน 13 หลัก...")

if cid_input:
    cid_clean = cid_input.strip()
    df = st.session_state["df_gsb"]
    
    if df is None:
        st.warning("⚠️ ยังไม่มีข้อมูลในระบบ กรุณาให้ Admin อัปโหลดไฟล์ประจำเดือนก่อนครับ")
    else:
        # 1. ค้นหาคอลัมน์เลขบัตรประชาชน
        col_cid = None
        for c in df.columns:
            if any(k in c.lower() for k in ['ประชาชน', 'id', 'เลขบัตร', 'citizen', 'pid']):
                col_cid = c
                break
        if not col_cid:
            col_cid = df.columns[0]
        
        result = df[df[col_cid].astype(str).str.strip() == cid_clean]
        
        if not result.empty:
            row = result.iloc[0]
            st.markdown("<h3 style='color: green;'>ผลการตรวจสอบ &nbsp;&nbsp;&nbsp;&nbsp; <b>ใช้สิทธิได้</b></h3>", unsafe_allow_html=True)
            
            # ฟังก์ชันแปลงรูปแบบวันที่ให้เป็น DD/MM/YYYY (พ.ศ.)
            def format_date_str(val):
                if not val or val.lower() in ['nan', 'none', '-']:
                    return '-'
                val = val.split()[0].replace('-', '/')
                parts = val.split('/')
                if len(parts) == 3:
                    # กรณีเรียงแบบ YYYY/MM/DD
                    if len(parts[0]) == 4:
                        y, m, d = parts[0], parts[1], parts[2]
                        return f"{int(d):02d}/{int(m):02d}/{y}"
                    # กรณีเรียงแบบ DD/MM/YYYY
                    elif len(parts[2]) == 4:
                        d, m, y = parts[0], parts[1], parts[2]
                        return f"{int(d):02d}/{int(m):02d}/{y}"
                return val

            # ฟังก์ชันดึงค่าจากคอลัมน์
            def find_val(keywords):
                for kw in keywords:
                    for col in df.columns:
                        if kw.lower() in col.lower():
                            v = str(row[col]).strip()
                            if v and v.lower() not in ['nan', 'none']:
                                return v
                return ''

            # 1. ชื่อ-นามสกุล
            title = find_val(['คำนำหน้า', 'คำนำ'])
            fname = find_val(['ชื่อผู้มีสิทธิ', 'ชื่อพนักงาน', 'ชื่อ'])
            lname = find_val(['นามสกุล', 'สกุล'])
            
            if lname and lname in fname:
                full_name = f"{title} {fname}".strip()
            else:
                full_name = f"{title} {fname} {lname}".strip()
            if not full_name:
                full_name = find_val(['ผู้มีสิทธิ', 'name'])

            # 2. รหัสพนักงาน
            emp_id = find_val(['รหัสพนักงาน', 'รหัสพนง', 'emp_id', 'staff_id'])

            # 3. วันเริ่มใช้สิทธิ
            raw_start = find_val(['เริ่มใช้สิทธิ', 'วันเริ่ม', 'ตั้งแต่วันที่', 'วันที่เริ่ม', 'start_dat', 'effective', 'start'])
            start_date = format_date_str(raw_start)

            # 4. วันสิ้นสุดการใช้สิทธิ
            raw_end = find_val(['สิ้นสุดการใช้สิทธิ', 'วันสิ้นสุด', 'ถึงวันที่', 'วันที่หมด', 'หมดสิทธิ', 'end_date', 'expire', 'end'])
            end_date = format_date_str(raw_end)

            # 5. หน่วยงาน (ดึง Name, Group, หรือคอลัมน์สังกัดรวมกัน)
            unit_parts = []
            for col in df.columns:
                col_lower = col.lower()
                if any(k in col_lower for k in ['name', 'group', 'หน่วยงาน', 'สังกัด', 'ศูนย์', 'เขต', 'ฝ่าย', 'สาขา', 'ตำแหน่ง']):
                    v = str(row[col]).strip()
                    if v and v.lower() not in ['nan', 'none'] and v not in unit_parts and v != full_name:
                        unit_parts.append(v)
            
            unit_val = " ".join(unit_parts) if unit_parts else find_val(['หน่วยงาน', 'สังกัด', 'department', 'org'])

            # แสดงผลทั้ง 5 ข้อ
            st.markdown(f"**1. ชื่อ ผู้มีสิทธิ** &nbsp;&nbsp;&nbsp;&nbsp; {full_name if full_name else '-'}")
            st.markdown(f"**2. รหัสพนักงาน** &nbsp;&nbsp;&nbsp;&nbsp; {emp_id if emp_id else '-'}")
            st.markdown(f"**3. วันเริ่มใช้สิทธิ** &nbsp;&nbsp;&nbsp;&nbsp; {start_date}")
            st.markdown(f"**4. วันสิ้นสุดการใช้สิทธิ** &nbsp;&nbsp;&nbsp;&nbsp; {end_date}")
            st.markdown(f"**5. หน่วยงาน** &nbsp;&nbsp;&nbsp;&nbsp; {unit_val if unit_val else '-'}")
        else:
            st.markdown("<h3 style='color: red;'>ผลการตรวจสอบ &nbsp;&nbsp;&nbsp;&nbsp; <b>ไม่พบข้อมูล / หมดสิทธิ</b></h3>", unsafe_allow_html=True)
