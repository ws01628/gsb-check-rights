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
                # ลองอ่านไฟล์กรณีติดรหัสผ่าน GSBCENTER
                try:
                    decrypted_data = io.BytesIO()
                    office_file = msoffcrypto.OfficeFile(uploaded_file)
                    office_file.load_key(password="GSBCENTER")
                    office_file.decrypt(decrypted_data)
                    df = pd.read_excel(decrypted_data, dtype=str)
                except Exception:
                    # ถ้าไฟล์ไม่ได้ตั้งรหัสผ่าน
                    uploaded_file.seek(0)
                    df = pd.read_excel(uploaded_file, dtype=str)
                
                if df is not None:
                    # ทำความสะอาดชื่อคอลัมน์ (ตัดช่องว่างซ้ำซ้อน)
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
            if any(k in c for k in ['ประชาชน', 'ID', 'เลขบัตร', 'CITIZEN', 'PID']):
                col_cid = c
                break
        if not col_cid:
            col_cid = df.columns[0]
        
        # ค้นหาแถวที่มีเลขบัตรประชาชนตรงกัน
        result = df[df[col_cid].astype(str).str.strip() == cid_clean]
        
        if not result.empty:
            row = result.iloc[0]
            st.markdown("<h3 style='color: green;'>ผลการตรวจสอบ &nbsp;&nbsp;&nbsp;&nbsp; <b>ใช้สิทธิได้</b></h3>", unsafe_allow_html=True)
            
            # ฟังก์ชันค้นหาค่าตาม Keyword ยืดหยุ่น
            def find_value(keywords):
                for kw in keywords:
                    for col in df.columns:
                        if kw.lower() in col.lower():
                            val = str(row[col]).strip()
                            if val and val.lower() != 'nan' and val != 'None':
                                # จัดการฟอร์แมตวันที่กรณีเป็น Timestamp
                                if '00:00:00' in val:
                                    val = val.split()[0]
                                return val
                return ''

            # 1. ชื่อ-นามสกุล
            title = find_value(['คำนำหน้า', 'คำนำ'])
            fname = find_value(['ชื่อผู้มีสิทธิ', 'ชื่อพนักงาน', 'ชื่อ'])
            lname = find_value(['นามสกุล', 'สกุล'])
            
            if lname and lname in fname:
                full_name = f"{title} {fname}".strip()
            else:
                full_name = f"{title} {fname} {lname}".strip()
            if not full_name:
                full_name = find_value(['ผู้มีสิทธิ', 'NAME'])

            # 2. รหัสพนักงาน
            emp_id = find_value(['รหัสพนักงาน', 'รหัสพนง', 'EMP_ID', 'STAFF_ID'])

            # 3. วันเริ่มใช้สิทธิ
            start_date = find_value(['เริ่มใช้สิทธิ', 'วันเริ่ม', 'ตั้งแต่วันที่', 'วันที่เริ่ม', 'EFFECTIVE', 'START'])

            # 4. วันสิ้นสุดการใช้สิทธิ
            end_date = find_value(['สิ้นสุดการใช้สิทธิ', 'วันสิ้นสุด', 'ถึงวันที่', 'วันที่หมด', 'หมดสิทธิ', 'EXPIRE', 'END'])

            # 5. หน่วยงาน
            unit_val = find_value(['หน่วยงาน', 'สังกัด', 'ศูนย์/เขต', 'ศูนย์', 'เขต', 'ฝ่าย', 'สาขา', 'ตำแหน่ง', 'ORG', 'DEPARTMENT'])

            # แสดงผล 5 ข้อตรงตามแบบ
            st.markdown(f"**1. ชื่อ ผู้มีสิทธิ** &nbsp;&nbsp;&nbsp;&nbsp; {full_name if full_name else '-'}")
            st.markdown(f"**2. รหัสพนักงาน** &nbsp;&nbsp;&nbsp;&nbsp; {emp_id if emp_id else '-'}")
            st.markdown(f"**3. วันเริ่มใช้สิทธิ** &nbsp;&nbsp;&nbsp;&nbsp; {start_date if start_date else '-'}")
            st.markdown(f"**4. วันสิ้นสุดการใช้สิทธิ** &nbsp;&nbsp;&nbsp;&nbsp; {end_date if end_date else '-'}")
            st.markdown(f"**5. หน่วยงาน** &nbsp;&nbsp;&nbsp;&nbsp; {unit_val if unit_val else '-'}")
        else:
            st.markdown("<h3 style='color: red;'>ผลการตรวจสอบ &nbsp;&nbsp;&nbsp;&nbsp; <b>ไม่พบข้อมูล / หมดสิทธิ</b></h3>", unsafe_allow_html=True)
