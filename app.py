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
                    # ถ้าไฟล์ไม่มีรหัสผ่าน
                    uploaded_file.seek(0)
                    df = pd.read_excel(uploaded_file, dtype=str)
                
                if df is not None:
                    # เคลียร์ชื่อคอลัมน์และแปลงค่าเป็น string ทั้งหมด
                    df.columns = [str(c).strip() for c in df.columns]
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
        # ค้นหาคอลัมน์เลขบัตรประชาชน
        col_cid_candidates = [c for c in df.columns if any(k in str(c) for k in ['ประชาชน', 'ID', 'เลข', 'บัตร'])]
        col_cid = col_cid_candidates[0] if col_cid_candidates else df.columns[0]
        
        # ค้นหาแถวที่ตรงกับ CID
        result = df[df[col_cid].astype(str).str.strip() == cid_clean]
        
        if not result.empty:
            row = result.iloc[0]
            st.markdown("<h3 style='color: green;'>ผลการตรวจสอบ &nbsp;&nbsp;&nbsp;&nbsp; <b>ใช้สิทธิได้</b></h3>", unsafe_allow_html=True)
            
            # ฟังก์ชันค้นหาค่าจากคอลัมน์ที่เข้าข่าย
            def get_col_val(keywords):
                for kw in keywords:
                    for c in df.columns:
                        if kw in str(c):
                            val = str(row[c]).strip()
                            if val and val.lower() != 'nan':
                                return val
                return ''

            # 1. จัดการชื่อ-นามสกุล
            title = get_col_val(['คำนำ', 'คำนำหน้า'])
            fname = get_col_val(['ชื่อผู้', 'ชื่อ'])
            lname = get_col_val(['สกุล', 'นามสกุล'])
            
            # ถ้านามสกุลรวมอยู่ในคอลัมน์ชื่อแล้ว ไม่ต้องต่อซ้ำ
            if lname and lname in fname:
                full_name = f"{title} {fname}".strip()
            else:
                full_name = f"{title} {fname} {lname}".strip()
            if not full_name:
                full_name = get_col_val(['ผู้มีสิทธิ', 'พนักงาน'])

            # 2. รหัสพนักงาน
            emp_id = get_col_val(['รหัสพนักงาน', 'รหัสพนง', 'เลขพนักงาน', 'พนักงาน'])

            # 3. วันเริ่มใช้สิทธิ
            start_date = get_col_val(['เริ่ม', 'วันเริ่ม', 'วันที่เริ่ม', 'ตั้งแต่วันที่', 'Effective'])

            # 4. วันสิ้นสุดการใช้สิทธิ
            end_date = get_col_val(['สิ้นสุด', 'หมดสิทธิ', 'วันที่หมด', 'ถึงวันที่', 'Expire'])

            # 5. หน่วยงาน
            unit_val = get_col_val(['หน่วยงาน', 'สังกัด', 'ศูนย์', 'เขต', 'ฝ่าย', 'สาขา', 'ตำแหน่ง'])

            # แสดงผลตามรูปแบบ
            st.markdown(f"**1. ชื่อ ผู้มีสิทธิ** &nbsp;&nbsp;&nbsp;&nbsp; {full_name if full_name else '-'}")
            st.markdown(f"**2. รหัสพนักงาน** &nbsp;&nbsp;&nbsp;&nbsp; {emp_id if emp_id else '-'}")
            st.markdown(f"**3. วันเริ่มใช้สิทธิ** &nbsp;&nbsp;&nbsp;&nbsp; {start_date if start_date else '-'}")
            st.markdown(f"**4. วันสิ้นสุดการใช้สิทธิ** &nbsp;&nbsp;&nbsp;&nbsp; {end_date if end_date else '-'}")
            st.markdown(f"**5. หน่วยงาน** &nbsp;&nbsp;&nbsp;&nbsp; {unit_val if unit_val else '-'}")
        else:
            st.markdown("<h3 style='color: red;'>ผลการตรวจสอบ &nbsp;&nbsp;&nbsp;&nbsp; <b>ไม่พบข้อมูล / หมดสิทธิ</b></h3>", unsafe_allow_html=True)
