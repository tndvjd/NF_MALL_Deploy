def preprocess_categories(df, target_category=None):
    """
    상품 카테고리를 매핑하는 함수
    Args:
        df: 데이터프레임
        target_category: 매핑할 특정 카테고리 (선택사항). None이면 모든 카테고리 매핑
    Returns:
        매핑된 데이터프레임
    """
    
    # 카테고리 매핑 딕셔너리
    living_room_mapping = {
        '거실장': '거실수납장',
        '소파': '소파',
        '진열장/장식장': '진열장/장식장',
        '소파테이블': '소파테이블',
        '기타소품': '진열장/장식장',
        '선반': '진열장/장식장',
        '소파테이': '소파테이블',
        '수납장': '거실수납장',
        '신발장': '거실수납장',
        '책상': '소파테이블',
        '콘솔': '거실수납장',
        '테이블': '소파테이블',
        '협탁': '소파테이블'
    }

    bedroom_mapping = {
        '침대': '침대',
        '매트리스': '매트리스',
        '서랍장': '침실수납장',
        '화장대': '화장대',
        '화장대의자': '화장대',
        '행거': '행거/드레스룸',
        '행거/드레스룸': '행거/드레스룸',
        '드레스룸/옷장': '행거/드레스룸',
        '옷장': '행거/드레스룸',
        '옷장/장롱': '행거/드레스룸',
        '거울': '거울',
        '협탁': '협탁',
        '수납': '침실수납장',
        '수납장': '침실수납장',
        '거실장': '침실수납장'
    }

    kitchen_mapping = {
        '주방 수납장': '주방수납장',
        '주방 수납장/상부장': '주방수납장',
        '수납장': '주방수납장',
        '장식장': '주방수납장',
        '틈새장': '주방수납장',
        '렌지대': '렌지대/식탁렌지대',
        '렌지대/식탁렌지대': '렌지대/식탁렌지대',
        '식탁렌지대': '렌지대/식탁렌지대',
        '식탁': '식탁',
        '테이블': '식탁',
        '테이블다리': '식탁',
        '식탁 의자': '식탁의자/벤치',
        '식탁의자': '식탁의자/벤치',
        '식탁의자/벤치': '식탁의자/벤치',
        '식탁의자/밴치': '식탁의자/벤치',
        '홈바': '홈바',
        '홈바테이블': '홈바',
        '주방용품/기타': '주방용품/기타',
        '롤박스': '주방용품/기타'
    }

    study_mapping = {
        '책상': '책상',
        '좌식책상': '좌식책상',
        '책장': '책장/책꽂이',
        '책꽂이': '책장/책꽂이',
        '책장/책꽂이': '책장/책꽂이',
        '교구장': '책장/책꽂이',
        '장식장': '책장/책꽂이',
        '책상 서랍장': '서재수납장',
        '책상/서랍장': '서재수납장',
        '서랍장': '서재수납장',
        '수납장': '서재수납장',
        '수납': '서재수납장',
        '선반/받침대': '선반/받침대',
        '기타': '선반/받침대',
        '책상/책꽂이': '책장/책꽂이'
    }

    storage_mapping = {
        '수남장': '일반수납장',
        '수납장': '일반수납장',
        '틈새장': '틈새장',
        '선반장': '선반장',
        '신발장': '신발장',
        '수납박스': '수납박스'
    }

    chair_mapping = {
        '사무용/학생용 의자': '사무용/학생용 의자',
        '사무의자': '사무용/학생용 의자',
        '게이밍 의자': '게이밍/PC방 의자',
        '게이밍/pc방 의자': '게이밍/PC방 의자',
        '인테리어 의자': '인테리어 의자',
        '인테리어의자': '인테리어 의자',
        '까페의자': '인테리어 의자',
        '카페 의자': '인테리어 의자',
        '카페의자': '인테리어 의자',
        '스툴': '스툴',
        '수납 의자': '스툴',
        '수납의자': '스툴',
        '리클라이너': '리클라이너',
        '기타': '기타 의자',
        '기타 의자': '기타 의자'
    }

    outdoor_mapping = {
        '의자': '의자',
        '테이블': '테이블'
    }

    etc_mapping = {
        # 모든 하위 카테고리를 '기타소품'으로 매핑
        '.*': '기타소품'
    }
    
    # 매핑 정보를 딕셔너리로 구성
    category_mappings = {
        '거실가구': living_room_mapping,
        '침실가구': bedroom_mapping,
        '주방가구': kitchen_mapping,
        '서재가구': study_mapping,
        '수납': storage_mapping,
        '수납가구': storage_mapping,
        '의자': chair_mapping,
        '의자/스툴': chair_mapping,
        '아웃도어': outdoor_mapping,
        '가든 아웃도어': outdoor_mapping,
        '반려동물': etc_mapping,
        '업소용가구': etc_mapping,
        '일반상품': etc_mapping
    }
    
    # 컬럼명
    main_category_column = '상품분류 번호'
    sub_category_column = '상품분류 신상품영역'
    
    # 필수 컬럼 체크
    required_columns = [main_category_column, sub_category_column]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"데이터프레임에 다음 필수 컬럼이 없습니다: {', '.join(missing_columns)}")
    
    # 결과를 저장할 데이터프레임 복사
    result_df = df.copy()
    
    # 상품분류 추천상품영역의 구분자 통일 ('|' -> ',')
    if '상품분류 추천상품영역' in result_df.columns:
        result_df['상품분류 추천상품영역'] = result_df['상품분류 추천상품영역'].astype(str).apply(lambda x: x.replace('|', ','))
    
    # 빈 값을 '기타'로 채우기
    result_df[sub_category_column] = result_df[sub_category_column].fillna('기타')
    result_df.loc[result_df[sub_category_column].isin(['', 'nan', 'None', 'N,N', 'N,N,N']), sub_category_column] = '기타'
    
    # 특정 카테고리만 처리
    if target_category:
        if target_category not in category_mappings:
            raise ValueError(f"지원하지 않는 카테고리입니다: {target_category}")
        
        # 수납/수납가구는 특별 처리
        if target_category in ['수납', '수납가구']:
            mask = df[main_category_column].isin([target_category])
        # 의자/의자스툴도 특별 처리
        elif target_category in ['의자', '의자/스툴']:
            mask = df[main_category_column].isin(['의자', '의자/스툴'])
        # 아웃도어/가든 아웃도어도 특별 처리
        elif target_category in ['아웃도어', '가든 아웃도어']:
            mask = df[main_category_column].isin(['아웃도어', '가든 아웃도어'])
        else:
            mask = df[main_category_column] == target_category
            
        if not mask.any():
            print(f"경고: {target_category} 카테고리에 해당하는 데이터가 없습니다.")
            return result_df
            
        if target_category in ['반려동물', '업소용가구', '일반상품']:
            # 기타소품으로 직접 매핑
            result_df.loc[mask, sub_category_column] = '기타소품'
        else:
            # 매핑 적용
            result_df.loc[mask, sub_category_column] = (
                result_df.loc[mask, sub_category_column]
                .map(category_mappings[target_category])
            )
        
        # 매핑 결과 출력
        print(f"\n{target_category} 매핑 결과:")
        print(result_df.loc[mask, sub_category_column].value_counts())
        
    # 모든 카테고리 처리
    else:
        for category, mapping in category_mappings.items():
            # 수납/수납가구는 한번만 처리
            if category in ['수납', '수납가구']:
                if category == '수납':  # 수납 카테고리 처리 시에만 실행
                    mask = df[main_category_column].isin(['수납', '수납가구'])
                else:
                    continue
            # 의자/의자스툴도 한번만 처리
            elif category in ['의자', '의자/스툴']:
                if category == '의자':  # 의자 카테고리 처리 시에만 실행
                    mask = df[main_category_column].isin(['의자', '의자/스툴'])
                else:
                    continue
            # 아웃도어/가든 아웃도어도 한번만 처리
            elif category in ['아웃도어', '가든 아웃도어']:
                if category == '아웃도어':  # 아웃도어 카테고리 처리 시에만 실행
                    mask = df[main_category_column].isin(['아웃도어', '가든 아웃도어'])
                else:
                    continue
            else:
                mask = df[main_category_column] == category
                
            if mask.any():
                if category in ['반려동물', '업소용가구', '일반상품']:
                    # 기타소품으로 직접 매핑
                    result_df.loc[mask, sub_category_column] = '기타소품'
                else:
                    # 매핑 적용
                    result_df.loc[mask, sub_category_column] = (
                        result_df.loc[mask, sub_category_column]
                        .map(mapping)
                    )
                
                # 매핑 결과 출력
                print(f"\n{category} 매핑 결과:")
                print(result_df.loc[mask, sub_category_column].value_counts())
            else:
                print(f"경고: {category} 카테고리에 해당하는 데이터가 없습니다.")
    
    return result_df 