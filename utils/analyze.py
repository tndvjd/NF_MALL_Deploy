import streamlit as st
import re

def analyze_product_names(df, column_name):
    """상품명 패턴을 분석하여 보고서를 생성"""
    st.subheader("상품명 패턴 분석")
    
    # 모든 상품명을 리스트로 변환
    product_names = df[column_name].astype(str).tolist()
    
    # 1. 모델번호 패턴 분석
    model_patterns = {
        'HZY': len([name for name in product_names if 'HZY' in name]),
        'N': len([name for name in product_names if name.startswith('N') and any(c.isdigit() for c in name[:5])])
    }
    
    # 2. 규격 패턴 분석
    size_pattern = r'\d+[x×*]\d+'
    sizes = [re.findall(size_pattern, name) for name in product_names]
    unique_sizes = set(sum(sizes, []))
    
    # 3. 색상 옵션 패턴 분석
    color_pattern = r'\d+colors?'
    colors = [re.findall(color_pattern, name) for name in product_names]
    color_counts = {}
    for color_list in colors:
        for color in color_list:
            color_counts[color] = color_counts.get(color, 0) + 1
    
    # 4. 가구 종류 분석
    furniture_types = ['서랍', '수납', '장', '테이블', '의자', '책상', '침대', '매트리스']
    type_counts = {}
    for ftype in furniture_types:
        type_counts[ftype] = len([name for name in product_names if ftype in name])
    
    # 결과 출력
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 모델번호 패턴")
        for pattern, count in model_patterns.items():
            st.write(f"- {pattern}: {count}개")
        
        st.write("\n### 규격 패턴")
        st.write(f"발견된 규격 패턴: {len(unique_sizes)}개")
        st.write("예시:", list(unique_sizes)[:5])
    
    with col2:
        st.write("### 색상 옵션")
        for color, count in color_counts.items():
            st.write(f"- {color}: {count}개")
        
        st.write("\n### 가구 종류")
        for ftype, count in type_counts.items():
            st.write(f"- {ftype}: {count}개")
    
    # 샘플 상품명 표시
    st.write("### 샘플 상품명")
    sample_size = min(5, len(product_names))
    for i, name in enumerate(product_names[:sample_size]):
        st.write(f"{i+1}. {name}")
    
    return {
        'model_patterns': model_patterns,
        'unique_sizes': unique_sizes,
        'color_counts': color_counts,
        'type_counts': type_counts
    } 