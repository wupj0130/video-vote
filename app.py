import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="影片決選投票系統", layout="wide")

# 設定檔案路徑
VIDEO_FILE = "videos.csv"
RECORD_FILE = "vote_records.csv"

# --- 核心修正：自動相容各種 Excel 匯出的 CSV 格式 ---
def load_videos():
    if not os.path.exists(VIDEO_FILE):
        return pd.DataFrame(columns=['id', 'uploader', 'location', 'url'])
    
    # 嘗試多種編碼與分隔符號組合
    for enc in ["utf-8-sig", "big5", "cp950", "utf-16"]:
        for sep in [",", "\t"]:
            try:
                df = pd.read_csv(VIDEO_FILE, encoding=enc, sep=sep)
                if 'uploader' in df.columns and 'url' in df.columns:
                    return df
            except:
                continue
    return pd.DataFrame(columns=['id', 'uploader', 'location', 'url'])

# --- 初始化與自動讀取紀錄 ---
if 'all_records' not in st.session_state:
    if os.path.exists(RECORD_FILE):
        try:
            st.session_state.all_records = pd.read_csv(RECORD_FILE).to_dict('records')
        except:
            st.session_state.all_records = []
    else:
        st.session_state.all_records = []

def save_records():
    pd.DataFrame(st.session_state.all_records).to_csv(RECORD_FILE, index=False, encoding="utf-8-sig")

video_df = load_videos()

# --- 14 位評審名單 ---
with st.sidebar:
    st.title("🗳️ 控制台")
    voter_names = ["憲哥", "范大", "小荳", "曉宣", "培芯", "Connie", "Grace", "Kathy", "Kate", "Kyle", "Parel", "Sharon", "YoYo", "Yvonne"]
    current_user = st.selectbox("請選擇姓名：", voter_names)
    
    user_data = [r for r in st.session_state.all_records if r['voter'] == current_user]
    user_votes = [r['video_id'] for r in user_data if r['type'] == 'vote']
    user_guarantee = next((r['video_id'] for r in user_data if r['type'] == 'guarantee'), None)
    
    st.metric("已投票數", f"{len(user_votes)} / 50")
    st.write(f"保送狀態: {'🟢 已保送' if user_guarantee else '🔴 尚未保送'}")

# --- 主畫面分頁 ---
tab1, tab2 = st.tabs(["🎥 影片投票區", "📊 統計報表"])

with tab2:
    if not st.session_state.all_records:
        st.info("目前尚無投票數據。")
    else:
        df_rec = pd.DataFrame(st.session_state.all_records)
        v_counts = df_rec[df_rec['type']=='vote']['video_id'].value_counts().to_dict()
        g_map = df_rec[df_rec['type']=='guarantee'].set_index('video_id')['voter'].to_dict()
        
        rep = video_df.copy()
        rep['得票數'] = rep['id'].map(v_counts).fillna(0).astype(int)
        rep['保送人'] = rep['id'].map(g_map).fillna("—")
        rep['priority'] = rep['保送人'].apply(lambda x: 0 if x != "—" else 1)
        st.table(rep.sort_values(['priority', '得票數'], ascending=[True, False]).head(50)[['id', 'uploader', 'location', '得票數', '保送人']])

with tab1:
    search = st.text_input("🔍 搜尋投稿者或地點")
    f_df = video_df[video_df['uploader'].astype(str).str.contains(search) | video_df['location'].astype(str).str.contains(search)]
    
    if f_df.empty:
        st.warning("⚠️ 找不到符合條件的影片，請確認 videos.csv 是否包含正確資料。")
    
    for _, row in f_df.iterrows():
        with st.expander(f"【ID {row['id']}】 {row['uploader']} - {row['location']}"):
            c1, c2 = st.columns([3, 1])
            with c1: st.video(row['url'])
            with c2:
                if st.button("❌ 取消" if row['id'] in user_votes else "✅ 投票", key=f"v_{row['id']}"):
                    if row['id'] in user_votes:
                        st.session_state.all_records = [r for r in st.session_state.all_records if not (r['voter']==current_user and r['video_id']==row['id'] and r['type']=='vote')]
                    elif len(user_votes) < 50:
                        st.session_state.all_records.append({'voter':current_user, 'video_id':row['id'], 'type':'vote'})
                    save_records(); st.rerun()

                if st.button("🌟 保送", key=f"g_{row['id']}", type="primary" if user_guarantee == row['id'] else "secondary"):
                    st.session_state.all_records = [r for r in st.session_state.all_records if not (r['voter']==current_user and r['type']=='guarantee')]
                    if user_guarantee != row['id']:
                        st.session_state.all_records.append({'voter':current_user, 'video_id':row['id'], 'type':'guarantee'})
                    save_records(); st.rerun()
