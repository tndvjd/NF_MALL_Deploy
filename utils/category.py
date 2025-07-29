def convert_categories(df):
    """
    전처리된 카테고리를 코드로 변환하는 함수
    Args:
        df: 데이터프레임
    Returns:
        tuple: (변환된 데이터프레임, 성공 여부)
    """
    try:
        # 필수 컬럼 체크
        required_columns = ['상품분류 번호', '상품분류 신상품영역']
        if not all(col in df.columns for col in required_columns):
            return df, False
        
        # 거실가구 카테고리 코드 매핑
        living_room_codes = {
            '거실수납장': '71',
            '소파': '72',
            '진열장/장식장': '73',
            '소파테이블': '141'
        }
        
        # 침실가구 카테고리 코드 매핑
        bedroom_codes = {
            '침대': '76',
            '매트리스': '77',
            '침실수납장': '78',
            '화장대': '79',
            '행거/드레스룸': '80',
            '거울': '81',
            '협탁': '82'
        }
        
        # 주방가구 카테고리 코드 매핑
        kitchen_codes = {
            '주방수납장': '85',
            '렌지대/식탁렌지대': '86',
            '식탁': '87',
            '식탁의자/벤치': '88',
            '홈바': '89',
            '주방용품/기타': '131'
        }
        
        # 서재가구 카테고리 코드 매핑
        study_codes = {
            '책상': '93',
            '좌식책상': '94',
            '책장/책꽂이': '95',
            '서재수납장': '96',
            '선반/받침대': '97'
        }
        
        # 수납가구 카테고리 코드 매핑
        storage_codes = {
            '일반수납장': '99',
            '틈새장': '100',
            '선반장': '101',
            '신발장': '102',
            '수납박스': '103'
        }
        
        # 의자 카테고리 코드 매핑
        chair_codes = {
            '사무용/학생용 의자': '105',
            '게이밍/PC방 의자': '106',
            '인테리어 의자': '107',
            '스툴': '108',
            '리클라이너': '109',
            '기타 의자': '110'
        }
        
        # 아웃도어 카테고리 코드 매핑
        outdoor_codes = {
            '의자': '113',
            '테이블': '112'
        }
        
        # 결과를 저장할 데이터프레임 복사
        result_df = df.copy()
        
        # 각 카테고리별 처리
        category_mapping = {
            '거실가구': living_room_codes,
            '침실가구': bedroom_codes,
            '주방가구': kitchen_codes,
            '서재가구': study_codes,
            '수납': storage_codes,
            '수납가구': storage_codes,
            '의자': chair_codes,
            '의자/스툴': chair_codes,
            '아웃도어': outdoor_codes,
            '가든 아웃도어': outdoor_codes
        }
        
        # 기타 카테고리 처리 (반려동물, 업소용가구, 일반상품)
        etc_categories = ['반려동물', '업소용가구', '일반상품']
        etc_mask = df['상품분류 번호'].isin(etc_categories)
        if etc_mask.any():
            result_df.loc[etc_mask, '상품분류 번호'] = '114'  # 기타소품 코드
        
        # 각 카테고리별 매핑 적용
        for category, codes in category_mapping.items():
            if category in ['수납', '수납가구']:
                if category == '수납':  # 수납 카테고리 처리 시에만 실행
                    mask = df['상품분류 번호'].isin(['수납', '수납가구'])
                else:
                    continue
            elif category in ['의자', '의자/스툴']:
                if category == '의자':  # 의자 카테고리 처리 시에만 실행
                    mask = df['상품분류 번호'].isin(['의자', '의자/스툴'])
                else:
                    continue
            elif category in ['아웃도어', '가든 아웃도어']:
                if category == '아웃도어':  # 아웃도어 카테고리 처리 시에만 실행
                    mask = df['상품분류 번호'].isin(['아웃도어', '가든 아웃도어'])
                else:
                    continue
            else:
                mask = df['상품분류 번호'] == category
            
            if mask.any():
                for subcategory, code in codes.items():
                    subcategory_mask = mask & (df['상품분류 신상품영역'] == subcategory)
                    result_df.loc[subcategory_mask, '상품분류 번호'] = code
                
                # 매핑 결과 출력
                print(f"\n{category} 코드 변환 결과:")
                print(result_df.loc[mask, '상품분류 번호'].value_counts())
        
        return result_df, True
        
    except Exception as e:
        print(f"카테고리 변환 중 오류 발생: {str(e)}")
        return df, False
